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

from database import get_db, engine
import models
import schemas
import auth
import face_utils

# Create database tables
models.Base.metadata.create_all(bind=engine)

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
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Mark attendance using face recognition"""
    token = credentials.credentials
    current_user = auth.get_current_user(db, token)
    
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
        
        # Get all students
        students = db.query(models.Student).all()
        recognized_students = []
        
        for face_encoding in face_encodings:
            for student in students:
                # Convert stored encoding back to numpy array
                stored_encoding = np.array(student.face_encoding)
                
                # Compare faces
                matches = face_recognition.compare_faces(
                    [stored_encoding], 
                    face_encoding, 
                    tolerance=0.6
                )
                
                if matches[0]:
                    # Check if attendance already marked today
                    today = date.today()
                    existing_attendance = db.query(models.Attendance).filter(
                        models.Attendance.student_id == student.student_id,
                        models.Attendance.date == today
                    ).first()
                    
                    if not existing_attendance:
                        # Mark attendance
                        attendance = models.Attendance(
                            student_id=student.student_id,
                            date=today,
                            time=datetime.now().time(),
                            marked_by=current_user.id
                        )
                        db.add(attendance)
                        recognized_students.append(student.name)
        
        db.commit()
        
        if recognized_students:
            return {
                "message": f"Attendance marked for: {', '.join(recognized_students)}",
                "recognized_students": recognized_students
            }
        else:
            raise HTTPException(status_code=400, detail="No recognized students found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/attendance", response_model=List[schemas.AttendanceResponse])
def get_attendance(
    date_filter: Optional[date] = None,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get attendance records"""
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
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get system statistics"""
    token = credentials.credentials
    current_user = auth.get_current_user(db, token)
    
    total_students = db.query(models.Student).count()
    today_attendance = db.query(models.Attendance).filter(
        models.Attendance.date == date.today()
    ).count()
    
    return {
        "total_students": total_students,
        "today_attendance": today_attendance,
        "attendance_rate": (today_attendance / total_students * 100) if total_students > 0 else 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 