from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date, time

# User schemas
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Student schemas
class StudentBase(BaseModel):
    student_id: str
    name: str
    email: str
    semester: int | None = None

class StudentCreate(StudentBase):
    face_encoding: List[float]

class Student(StudentBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Attendance schemas
class AttendanceMark(BaseModel):
    image: str  # Base64 encoded image

class AttendanceResponse(BaseModel):
    id: int
    student_id: str
    student_name: str
    date: date
    time: time
    marked_by: int
    
    class Config:
        from_attributes = True

# Stats schema
class Stats(BaseModel):
    total_students: int
    today_attendance: int
    attendance_rate: float 