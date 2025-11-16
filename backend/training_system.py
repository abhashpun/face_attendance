import os
import pickle
import numpy as np
import face_recognition
import cv2
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
import schemas
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaceTrainingSystem:
    def __init__(self, db: Session):
        self.db = db
        self.model_path = "models/face_recognition_model.pkl"
        self.metrics_path = "models/training_metrics.json"
        self.model = None
        self.encodings = []
        self.labels = []
        self.training_history = []
        
        # Create models directory if it doesn't exist
        os.makedirs("models", exist_ok=True)
        
    def collect_training_data(self) -> Dict:
        """Collect face encodings and labels from database"""
        try:
            students = self.db.query(models.Student).all()
            
            if not students:
                return {"success": False, "message": "No students found for training"}
            
            encodings = []
            labels = []
            student_data = []
            
            for student in students:
                if student.face_encoding:
                    encodings.append(np.array(student.face_encoding))
                    labels.append(student.student_id)
                    student_data.append({
                        "student_id": student.student_id,
                        "name": student.name,
                        "semester": student.semester
                    })
            
            if not encodings:
                return {"success": False, "message": "No face encodings found"}
            
            self.encodings = encodings
            self.labels = labels
            
            return {
                "success": True,
                "total_samples": len(encodings),
                "unique_students": len(set(labels)),
                "student_data": student_data
            }
            
        except Exception as e:
            logger.error(f"Error collecting training data: {e}")
            return {"success": False, "message": str(e)}
    
    def train_model(self, model_type: str = "svm") -> Dict:
        """Train face recognition model"""
        try:
            # Collect training data
            data_status = self.collect_training_data()
            if not data_status["success"]:
                return data_status
            
            if len(self.encodings) < 2:
                return {"success": False, "message": "Insufficient data for training"}
            
            # Split data for training and testing
            X_train, X_test, y_train, y_test = train_test_split(
                self.encodings, self.labels, test_size=0.2, random_state=42, stratify=self.labels
            )
            
            # Train model based on type
            if model_type == "svm":
                self.model = SVC(kernel='linear', probability=True)
            else:
                self.model = SVC(kernel='rbf', probability=True)
            
            # Train the model
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Generate detailed metrics
            metrics = {
                "accuracy": float(accuracy),
                "total_samples": len(self.encodings),
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "unique_students": len(set(self.labels)),
                "model_type": model_type,
                "training_date": datetime.now().isoformat(),
                "classification_report": classification_report(y_test, y_pred, output_dict=True)
            }
            
            # Save model and metrics
            self.save_model()
            self.save_metrics(metrics)
            
            # Store training history
            self.training_history.append({
                "date": datetime.now().isoformat(),
                "accuracy": accuracy,
                "model_type": model_type,
                "samples": len(self.encodings)
            })
            
            return {
                "success": True,
                "accuracy": accuracy,
                "metrics": metrics,
                "message": f"Model trained successfully with {accuracy:.2%} accuracy"
            }
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {"success": False, "message": str(e)}
    
    def save_model(self):
        """Save trained model to disk"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def load_model(self) -> bool:
        """Load trained model from disk"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                logger.info("Model loaded successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def save_metrics(self, metrics: Dict):
        """Save training metrics to disk"""
        try:
            with open(self.metrics_path, 'w') as f:
                json.dump(metrics, f, indent=2)
            logger.info(f"Metrics saved to {self.metrics_path}")
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def load_metrics(self) -> Optional[Dict]:
        """Load training metrics from disk"""
        try:
            if os.path.exists(self.metrics_path):
                with open(self.metrics_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")
            return None
    
    def predict_face(self, face_encoding: List[float]) -> Dict:
        """Predict student from face encoding using trained model"""
        try:
            if self.model is None:
                if not self.load_model():
                    return {"success": False, "message": "No trained model available"}
            
            # Convert to numpy array
            encoding_array = np.array(face_encoding).reshape(1, -1)
            
            # Make prediction
            prediction = self.model.predict(encoding_array)[0]
            confidence = np.max(self.model.predict_proba(encoding_array))
            
            # Get student details
            student = self.db.query(models.Student).filter(
                models.Student.student_id == prediction
            ).first()
            
            if student:
                return {
                    "success": True,
                    "student_id": prediction,
                    "student_name": student.name,
                    "confidence": float(confidence),
                    "semester": student.semester
                }
            else:
                return {"success": False, "message": "Student not found"}
                
        except Exception as e:
            logger.error(f"Error predicting face: {e}")
            return {"success": False, "message": str(e)}
    
    def evaluate_model_performance(self) -> Dict:
        """Evaluate current model performance"""
        try:
            metrics = self.load_metrics()
            if not metrics:
                return {"success": False, "message": "No training metrics found"}
            
            # Get recent attendance data for evaluation
            recent_attendance = self.db.query(models.Attendance).filter(
                models.Attendance.date >= datetime.now().date() - timedelta(days=7)
            ).all()
            
            evaluation_data = {
                "model_metrics": metrics,
                "recent_attendance_count": len(recent_attendance),
                "evaluation_date": datetime.now().isoformat(),
                "training_history": self.training_history[-5:] if self.training_history else []
            }
            
            return {"success": True, "evaluation": evaluation_data}
            
        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            return {"success": False, "message": str(e)}
    
    def get_training_recommendations(self) -> Dict:
        """Get recommendations for improving model performance"""
        try:
            metrics = self.load_metrics()
            if not metrics:
                return {"success": False, "message": "No training data available"}
            
            recommendations = []
            
            # Check accuracy
            accuracy = metrics.get("accuracy", 0)
            if accuracy < 0.8:
                recommendations.append("Model accuracy is below 80%. Consider retraining with more data.")
            
            # Check sample size
            total_samples = metrics.get("total_samples", 0)
            if total_samples < 10:
                recommendations.append("Very few training samples. Add more student face images.")
            
            # Check class balance
            unique_students = metrics.get("unique_students", 0)
            if total_samples > 0 and total_samples / unique_students < 2:
                recommendations.append("Low samples per student. Add multiple face images per student.")
            
            # Check training history
            if len(self.training_history) > 0:
                recent_accuracy = self.training_history[-1].get("accuracy", 0)
                if recent_accuracy < accuracy:
                    recommendations.append("Recent training showed lower accuracy. Check data quality.")
            
            return {
                "success": True,
                "recommendations": recommendations,
                "current_metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return {"success": False, "message": str(e)}

class DataQualityAnalyzer:
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_face_quality(self, face_encoding: List[float]) -> Dict:
        """Analyze quality of face encoding"""
        try:
            encoding_array = np.array(face_encoding)
            
            # Check for zero or very small values
            zero_count = np.sum(encoding_array == 0)
            small_count = np.sum(np.abs(encoding_array) < 0.01)
            
            # Calculate variance (higher variance = more unique features)
            variance = np.var(encoding_array)
            
            # Quality score based on multiple factors
            quality_score = 0
            
            if variance > 0.1:
                quality_score += 30
            elif variance > 0.05:
                quality_score += 20
            else:
                quality_score += 10
            
            if zero_count < len(encoding_array) * 0.1:
                quality_score += 30
            elif zero_count < len(encoding_array) * 0.2:
                quality_score += 20
            else:
                quality_score += 10
            
            if small_count < len(encoding_array) * 0.3:
                quality_score += 40
            elif small_count < len(encoding_array) * 0.5:
                quality_score += 25
            else:
                quality_score += 10
            
            quality_level = "High" if quality_score >= 80 else "Medium" if quality_score >= 60 else "Low"
            
            return {
                "quality_score": quality_score,
                "quality_level": quality_level,
                "variance": float(variance),
                "zero_count": int(zero_count),
                "small_count": int(small_count),
                "recommendation": "Good quality" if quality_score >= 80 else "Consider retaking photo"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing face quality: {e}")
            return {"error": str(e)}
    
    def get_data_statistics(self) -> Dict:
        """Get comprehensive statistics about training data"""
        try:
            students = self.db.query(models.Student).all()
            
            total_students = len(students)
            students_with_faces = len([s for s in students if s.face_encoding])
            students_without_faces = total_students - students_with_faces
            
            # Semester distribution
            semester_counts = {}
            for student in students:
                semester = student.semester or "Unknown"
                semester_counts[semester] = semester_counts.get(semester, 0) + 1
            
            # Quality analysis for students with faces
            quality_scores = []
            for student in students:
                if student.face_encoding:
                    quality = self.analyze_face_quality(student.face_encoding)
                    if "quality_score" in quality:
                        quality_scores.append(quality["quality_score"])
            
            avg_quality = np.mean(quality_scores) if quality_scores else 0
            
            return {
                "total_students": total_students,
                "students_with_faces": students_with_faces,
                "students_without_faces": students_without_faces,
                "face_coverage_percentage": (students_with_faces / total_students * 100) if total_students > 0 else 0,
                "average_quality_score": float(avg_quality),
                "semester_distribution": semester_counts,
                "quality_distribution": {
                    "high": len([s for s in quality_scores if s >= 80]),
                    "medium": len([s for s in quality_scores if 60 <= s < 80]),
                    "low": len([s for s in quality_scores if s < 60])
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting data statistics: {e}")
            return {"error": str(e)} 