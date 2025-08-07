#!/bin/bash

echo "=== Git Setup for Face Recognition Attendance System ==="
echo

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Initialize Git repository
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Add .gitignore
echo "📝 Adding .gitignore file..."
git add .gitignore
git commit -m "Add .gitignore file"

# Add backend files (excluding virtual environment and sensitive files)
echo "📁 Adding backend files..."
git add backend/main.py
git add backend/database.py
git add backend/models.py
git add backend/schemas.py
git add backend/auth.py
git add backend/face_utils.py
git add backend/env_example.txt
git add requirements.txt
git commit -m "Add backend FastAPI application"

# Add frontend files (excluding node_modules and build files)
echo "📁 Adding frontend files..."
git add frontend/package.json
git add frontend/src/
git add frontend/public/
git commit -m "Add React frontend application"

# Add documentation and setup files
echo "📚 Adding documentation..."
git add README.md
git add setup.sh
git commit -m "Add documentation and setup scripts"

echo
echo "✅ All required files have been added to Git!"
echo
echo "📋 Files included in the repository:"
echo "   Backend:"
echo "   - main.py (FastAPI application)"
echo "   - database.py (Database configuration)"
echo "   - models.py (SQLAlchemy models)"
echo "   - schemas.py (Pydantic schemas)"
echo "   - auth.py (Authentication utilities)"
echo "   - face_utils.py (Face recognition utilities)"
echo "   - env_example.txt (Environment template)"
echo "   - requirements.txt (Python dependencies)"
echo
echo "   Frontend:"
echo "   - package.json (Node.js dependencies)"
echo "   - src/ (React components and logic)"
echo "   - public/ (Static files)"
echo
echo "   Documentation:"
echo "   - README.md (Project documentation)"
echo "   - setup.sh (Setup script)"
echo "   - .gitignore (Git ignore rules)"
echo
echo "📋 Files excluded from the repository:"
echo "   - Virtual environments (venv/, .venv/)"
echo "   - Environment files (.env)"
echo "   - Node modules (node_modules/)"
echo "   - Build files (build/, dist/)"
echo "   - Database files (*.db, *.sqlite)"
echo "   - Face encodings cache (*.pkl)"
echo "   - Known faces directory (known_faces/)"
echo "   - Log files (*.log)"
echo "   - IDE files (.vscode/, .idea/)"
echo
echo "🚀 To push to a remote repository:"
echo "   1. Create a repository on GitHub/GitLab"
echo "   2. Run: git remote add origin <repository-url>"
echo "   3. Run: git push -u origin main"
echo
echo "💡 To check what files will be committed:"
echo "   git status"
echo
echo "💡 To see all tracked files:"
echo "   git ls-files" 