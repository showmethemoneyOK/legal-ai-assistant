@echo off
echo Initializing Git repository for Legal AI project...
cd /d "%~dp0"

REM Remove any existing .git directory
if exist ".git" (
    echo Removing existing .git directory...
    rmdir /s /q ".git"
)

REM Initialize new Git repository
echo Initializing new Git repository...
git init

REM Configure Git
echo Configuring Git...
git config user.name "Benben"
git config user.email "benben@openclaw.ai"

REM Add all files
echo Adding files to Git...
git add .

REM Create initial commit
echo Creating initial commit...
git commit -m "Initial commit: Legal AI Assistant - Local AI-powered legal document analysis system

Features:
- Complete local deployment (Windows)
- Multi-user permission system
- Vector database with ChromaDB
- PyQt6 GUI + FastAPI backend
- SQLite for relational data
- Document parsing (PDF/DOCX)
- AI document generation and review
- File sharing and collaboration
- Vector database incremental updates"

echo.
echo Git repository initialized successfully!
echo.
echo To push to GitHub:
echo 1. Create a new repository on GitHub
echo 2. Run: git remote add origin https://github.com/yourusername/legal-ai-assistant.git
echo 3. Run: git push -u origin main
echo.
pause