from sqlalchemy import Column, Integer, String, DateTime, Date, Time, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from database import Base
from datetime import datetime
import numpy as np

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    attendances_marked = relationship("Attendance", back_populates="marked_by_user")

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String)
    face_encoding = Column(ARRAY(Float))  # Store face encoding as array
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    attendances = relationship("Attendance", back_populates="student")

class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, ForeignKey("students.student_id"))
    date = Column(Date)
    time = Column(Time)
    marked_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="attendances")
    marked_by_user = relationship("User", back_populates="attendances_marked") 