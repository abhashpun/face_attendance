#python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import face_recognition
import cv2
import numpy as np
import os
import pickle
from datetime import datetime, date
import base64
from io import BytesIO
from PIL import Image
from sqlalchemy import text, func

from database import get_db, engine
import models
import schemas
import auth
import face_utils
import training_system

# Create database tables
models.Base.metadata.create_all(bind=engine)
# Ensure DB schema compatibility (best effort for existing DB)
try:
    with engine.connect() as conn:
        # Make attendance.marked_by nullable
        conn.execute(text("ALTER TABLE attendance ALTER COLUMN marked_by DROP NOT NULL"))
        # Add students.semester if missing
        conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS semester INTEGER"))

except Exception:
    pass

app = FastAPI(title="Face Recognition Attendance System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
# Optional bearer for public endpoints
optional_security = HTTPBearer(auto_error=False)

@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new admin user"""
    return auth.create_user(db, user)

@app.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login and get access token"""
    return auth.authenticate_user_and_create_token(db, user_credentials)

@app.post("/encode-face")
def encode_face(image_data: schemas.AttendanceMark):
    """Encode face from image data"""
    try:
        encoding = face_utils.encode_face_from_image(image_data.image)
        return {"encoding": encoding}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/students", response_model=schemas.Student)
def create_student(
    student: schemas.StudentCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new student with face encoding"""
    token = credentials.credentials
    current_user = auth.get_current_user(db, token)
    
    # Check if student with same student_id already exists
    existing_student = db.query(models.Student).filter(
        models.Student.student_id == student.student_id
    ).first()
    if existing_student:
        raise HTTPException(
            status_code=400,
            detail="Student with this ID already exists"
        )
    
    # Create student record
    db_student = models.Student(
        student_id=student.student_id,
        name=student.name,
        email=student.email,
        semester=student.semester,
        face_encoding=student.face_encoding
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    
    return db_student

@app.get("/students", response_model=List[schemas.Student])
def get_students(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all students"""
    token = credentials.credentials
    current_user = auth.get_current_user(db, token)
    
    students = db.query(models.Student).all()
    return students

@app.delete("/students/{student_id}")
def delete_student(
    student_id: str,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a student"""
    token = credentials.credentials
    current_user = auth.get_current_user(db, token)
    
    student = db.query(models.Student).filter(
        models.Student.student_id == student_id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    db.delete(student)
    db.commit()
    
    return {"message": "Student deleted successfully"}

@app.post("/attendance/mark")
def mark_attendance(
    attendance_data: schemas.AttendanceMark,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security)
):
    """Mark attendance using face recognition"""
    current_user = None
    if credentials and credentials.credentials:
        try:
            token = credentials.credentials
            current_user = auth.get_current_user(db, token)
        except Exception:
            current_user = None
    
    # Decode base64 image
    try:
        image_data = base64.b64decode(attendance_data.image.split(',')[1])
        image = Image.open(BytesIO(image_data))
        image_array = np.array(image)
        
        # Convert RGB to BGR for OpenCV
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        
        # Detect faces in the image
        face_locations = face_recognition.face_locations(image_bgr)
        face_encodings = face_recognition.face_encodings(image_bgr, face_locations)
        
        if not face_encodings:
            raise HTTPException(status_code=400, detail="No face detected in image")
        
        # Get all students and precompute arrays
        students = db.query(models.Student).all()
        student_encodings = [np.array(s.face_encoding) for s in students]
        recognized_students = []
        already_marked_students = []
        unknown_faces_count = 0

        tolerance = 0.6
        
        for face_encoding in face_encodings:
            if not student_encodings:
                unknown_faces_count += 1
                continue
            # Compute distances to all known encodings and pick best match
            distances = face_recognition.face_distance(student_encodings, face_encoding)
            best_idx = int(np.argmin(distances)) if len(distances) > 0 else -1
            if best_idx >= 0 and distances[best_idx] <= tolerance:
                matched_student = students[best_idx]
                # Check duplicate attendance today
                today = date.today()
                existing_attendance = db.query(models.Attendance).filter(
                    models.Attendance.student_id == matched_student.student_id,
                    models.Attendance.date == today
                ).first()
                if not existing_attendance:
                    attendance = models.Attendance(
                        student_id=matched_student.student_id,
                        date=today,
                        time=datetime.now().time(),
                        marked_by=(current_user.id if current_user else None)
                    )
                    db.add(attendance)
                    recognized_students.append(matched_student.name)
                else:
                    already_marked_students.append(matched_student.name)
            else:
                unknown_faces_count += 1
        
        db.commit()
        
        # Prepare response message
        response_message = ""
        response_data = {
            "recognized_students": recognized_students,
            "already_marked_students": already_marked_students,
            "unknown_faces_count": unknown_faces_count
        }
        
        if recognized_students:
            response_message += f"Attendance marked for: {', '.join(recognized_students)}. "
        
        if already_marked_students:
            response_message += f"Attendance already done for: {', '.join(already_marked_students)}. "
        
        if unknown_faces_count > 0:
            response_message += f"Unknown face detected ({unknown_faces_count} face(s)). "
        
        if not recognized_students and not already_marked_students and unknown_faces_count == 0:
            raise HTTPException(status_code=400, detail="No recognized students found")
        
        return {
            "message": response_message.strip(),
            **response_data
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/attendance", response_model=List[schemas.AttendanceResponse])
def get_attendance(
    date_filter: Optional[date] = None,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get attendance records with optional date filter"""
    token = credentials.credentials
    current_user = auth.get_current_user(db, token)
    
    query = db.query(models.Attendance).join(models.Student)
    
    if date_filter:
        query = query.filter(models.Attendance.date == date_filter)
    
    attendance_records = query.all()
    
    result = []
    for record in attendance_records:
        result.append(schemas.AttendanceResponse(
            id=record.id,
            student_id=record.student_id,
            student_name=record.student.name,
            student_semester=record.student.semester,
            date=record.date,
            time=record.time,
            marked_by=record.marked_by
        ))
    
    return result

@app.delete("/attendance/{attendance_id}")
def delete_attendance(
    attendance_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete an attendance record"""
    token = credentials.credentials
    current_user = auth.get_current_user(db, token)
    
    attendance = db.query(models.Attendance).filter(
        models.Attendance.id == attendance_id
    ).first()
    
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    db.delete(attendance)
    db.commit()
    
    return {"message": "Attendance record deleted successfully"}

@app.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security)
):
    """Get system statistics, including semester-wise stats"""
    # Optional auth
    if credentials and credentials.credentials:
        try:
            _ = auth.get_current_user(db, credentials.credentials)
        except Exception:
            pass

    total_students = db.query(models.Student).count()

    # Count distinct students marked present today, only for students that still exist
    today_attendance = (
        db.query(models.Attendance.student_id)
          .join(models.Student, models.Student.student_id == models.Attendance.student_id)
          .filter(models.Attendance.date == date.today())
          .distinct()
          .count()
    )

    # Semester-wise totals and present today
    semester_totals = dict(
        db.query(models.Student.semester, func.count(models.Student.id))
          .filter(models.Student.semester.isnot(None))
          .group_by(models.Student.semester)
          .all()
    )
    semester_present = dict(
        db.query(models.Student.semester, func.count(func.distinct(models.Attendance.student_id)))
          .join(models.Attendance, models.Attendance.student_id == models.Student.student_id)
          .filter(models.Attendance.date == date.today())
          .filter(models.Student.semester.isnot(None))
          .group_by(models.Student.semester)
          .all()
    )

    semester_stats = [
        {
            "semester": s,
            "total": int(semester_totals.get(s, 0) or 0),
            "present_today": int(semester_present.get(s, 0) or 0),
            "attendance_rate": (int(semester_present.get(s, 0) or 0) / int(semester_totals.get(s, 0) or 1) * 100) if int(semester_totals.get(s, 0) or 0) > 0 else 0.0,
        }
        for s in range(1, 9)
    ]

    return {
        "total_students": total_students,
        "today_attendance": today_attendance,
        "attendance_rate": (today_attendance / total_students * 100) if total_students > 0 else 0,
        "semester_stats": semester_stats,
    }

# Training System Endpoints
@app.post("/training/collect-data")
def collect_training_data(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Collect training data from database"""
    token = credentials.credentials
    current_user = auth.get_current_user(db, token)
    training_sys = training_system.FaceTrainingSystem(db)
    return training_sys.collect_training_data()

@app.post("/training/train-model")
def train_model(
    model_type: str = "svm",
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Train face recognition model"""
    token = credentials.credentials
    current_user = auth.get_current_user(db, token)
    training_sys = training_system.FaceTrainingSystem(db)
    return training_sys.train_model(model_type)

@app.get("/training/performance")
def get_model_performance(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get model performance metrics"""
    token = credentials.credentials
    current_user = auth.get_current_user(db, token)
    training_sys = training_system.FaceTrainingSystem(db)
    return training_sys.evaluate_model_performance()

@app.get("/training/recommendations")
def get_training_recommendations(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get training recommendations"""
    token = credentials.credentials
    current_user = auth.get_current_user(db, token)
    training_sys = training_system.FaceTrainingSystem(db)
    return training_sys.get_training_recommendations()

@app.get("/training/data-statistics")
def get_data_statistics(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get comprehensive data statistics"""
    token = credentials.credentials
    current_user = auth.get_current_user(db, token)
    analyzer = training_system.DataQualityAnalyzer(db)
    return analyzer.get_data_statistics()

@app.post("/training/analyze-face-quality")
def analyze_face_quality(
    face_encoding: List[float],
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Analyze quality of face encoding"""
    token = credentials.credentials
    current_user = auth.get_current_user(db, token)
    analyzer = training_system.DataQualityAnalyzer(db)
    return analyzer.analyze_face_quality(face_encoding)

@app.post("/training/predict-face")
def predict_face_with_model(
    face_encoding: List[float],
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Predict student using trained model"""
    token = credentials.credentials
    current_user = auth.get_current_user(db, token)
    training_sys = training_system.FaceTrainingSystem(db)
    return training_sys.predict_face(face_encoding)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 