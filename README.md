# Face Recognition Attendance System

A full-stack web application for automated attendance tracking using face recognition technology. Built with FastAPI, React, and PostgreSQL.

## Features

- **Real-time Face Recognition**: Mark attendance using webcam
- **Student Management**: Add, edit, and delete student records with face capture
- **Admin Authentication**: Secure login system with JWT tokens
- **Attendance History**: View and export attendance records
- **Dashboard**: Real-time statistics and charts
- **PostgreSQL Database**: Store face encodings and attendance data
- **Responsive UI**: Modern React interface with Bootstrap

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Database for storing face encodings and data
- **SQLAlchemy**: ORM for database operations
- **Face Recognition**: Python library for face detection and recognition
- **JWT**: Authentication and authorization
- **OpenCV**: Image processing

### Frontend
- **React**: Modern JavaScript framework
- **React Router**: Client-side routing
- **Bootstrap**: UI components and styling
- **Chart.js**: Data visualization
- **React Webcam**: Camera integration
- **Axios**: HTTP client

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL
- Webcam

### 1. Database Setup

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE attendance_db;
CREATE USER attendance_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE attendance_db TO attendance_user;
\q
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r ../requirements.txt

# Create .env file
cp env_example.txt .env
# Edit .env with your database credentials and secret key

# Run database migrations
alembic upgrade head

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

### 4. Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Usage

### 1. Register Admin Account
- Visit http://localhost:3000/register
- Create an admin account

### 2. Add Students
- Login to the system
- Go to "Students" section
- Click "Add Student"
- Fill in student details and capture face photo

### 3. Mark Attendance
- Go to "Mark Attendance" section
- Position face in camera
- Click "Capture Photo"
- Click "Mark Attendance"

### 4. View Reports
- Check "Dashboard" for statistics
- View "History" for detailed records
- Export data to CSV

## API Endpoints

### Authentication
- `POST /register` - Register admin user
- `POST /login` - Login and get token

### Students
- `GET /students` - Get all students
- `POST /students` - Add new student
- `DELETE /students/{id}` - Delete student

### Attendance
- `POST /attendance/mark` - Mark attendance with face recognition
- `GET /attendance` - Get attendance records
- `DELETE /attendance/{id}` - Delete attendance record

### Statistics
- `GET /stats` - Get system statistics

## Database Schema

### Users Table
- id (Primary Key)
- username (Unique)
- email (Unique)
- hashed_password
- created_at

### Students Table
- id (Primary Key)
- student_id (Unique)
- name
- email
- face_encoding (Array of floats)
- created_at

### Attendance Table
- id (Primary Key)
- student_id (Foreign Key)
- date
- time
- marked_by (Foreign Key to Users)
- created_at

## Configuration

### Environment Variables (.env)
```env
DATABASE_URL=postgresql://username:password@localhost:5432/attendance_db
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Face Recognition Settings
- **Tolerance**: 0.6 (adjustable in code)
- **Model**: HOG (faster) or CNN (more accurate)
- **Image Size**: Automatically resized for performance

## Performance Optimizations

- **Cached Encodings**: Face encodings are stored in database
- **Frame Skipping**: Process every Nth frame to reduce lag
- **Image Resizing**: Smaller images for faster processing
- **Connection Pooling**: Database connection optimization

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Bcrypt password encryption
- **CORS Protection**: Cross-origin request handling
- **Input Validation**: Pydantic schema validation

## Troubleshooting

### Common Issues

1. **Camera not working**
   - Check browser permissions
   - Ensure HTTPS in production
   - Try different browsers

2. **Face recognition not working**
   - Ensure good lighting
   - Check face is clearly visible
   - Verify face encoding quality

3. **Database connection errors**
   - Check PostgreSQL service is running
   - Verify database credentials
   - Ensure database exists

4. **Performance issues**
   - Reduce number of known faces
   - Increase frame skip rate
   - Use lower resolution images

### Development Tips

- Use `uvicorn main:app --reload` for development
- Check browser console for frontend errors
- Monitor FastAPI logs for backend issues
- Use PostgreSQL logs for database debugging

## Deployment

### Production Setup

1. **Backend Deployment**
   ```bash
   # Use production WSGI server
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Frontend Deployment**
   ```bash
   npm run build
   # Serve build folder with nginx or similar
   ```

3. **Database**
   - Use managed PostgreSQL service
   - Set up proper backups
   - Configure connection pooling

4. **Security**
   - Use HTTPS
   - Set strong SECRET_KEY
   - Configure CORS properly
   - Set up firewall rules

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check the troubleshooting section
- Review API documentation
- Open an issue on GitHub 