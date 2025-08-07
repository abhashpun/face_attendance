#!/bin/bash

echo "=== Face Recognition Attendance System Setup ==="
echo "This script will help you set up the complete system."
echo

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please don't run this script as root."
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
if [ $(echo "$python_version >= 3.8" | bc -l) -eq 0 ]; then
    echo "Error: Python 3.8+ is required. Current version: $python_version"
    exit 1
fi

# Check Node.js version
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

node_version=$(node --version | grep -oP '\d+')
if [ "$node_version" -lt 16 ]; then
    echo "Error: Node.js 16+ is required. Current version: $node_version"
    exit 1
fi

echo "✓ Python and Node.js versions are compatible"
echo

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib python3-venv python3-pip

echo "✓ System dependencies installed"
echo

# Setup PostgreSQL
echo "Setting up PostgreSQL database..."
sudo -u postgres psql -c "CREATE DATABASE attendance_db;" 2>/dev/null || echo "Database already exists"
sudo -u postgres psql -c "CREATE USER attendance_user WITH PASSWORD 'attendance123';" 2>/dev/null || echo "User already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE attendance_db TO attendance_user;"

echo "✓ PostgreSQL database configured"
echo

# Setup Backend
echo "Setting up Backend..."
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r ../requirements.txt

# Create .env file
if [ ! -f .env ]; then
    cp env_example.txt .env
    echo "✓ Environment file created"
else
    echo "✓ Environment file already exists"
fi

echo "✓ Backend setup complete"
echo

# Setup Frontend
echo "Setting up Frontend..."
cd ../frontend

# Install Node.js dependencies
npm install

echo "✓ Frontend setup complete"
echo

# Create startup scripts
cd ..
echo "Creating startup scripts..."

cat > start_backend.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
EOF

cat > start_frontend.sh << 'EOF'
#!/bin/bash
cd frontend
npm start
EOF

chmod +x start_backend.sh start_frontend.sh

echo "✓ Startup scripts created"
echo

# Final instructions
echo "=== Setup Complete! ==="
echo
echo "Next steps:"
echo "1. Edit backend/.env with your database credentials"
echo "2. Start the backend: ./start_backend.sh"
echo "3. Start the frontend: ./start_frontend.sh"
echo "4. Open http://localhost:3000 in your browser"
echo "5. Register an admin account and start using the system"
echo
echo "Default database credentials:"
echo "  Database: attendance_db"
echo "  User: attendance_user"
echo "  Password: attendance123"
echo
echo "Remember to change these credentials in production!" 