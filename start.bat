@echo off
echo =================================================================
echo   BHULEKH | AI-Powered Land Governance Platform
echo =================================================================

set SCRIPT_DIR=%~dp0

echo 1. Seeding Backend Database...
cd /d "%SCRIPT_DIR%backend"
python seed_data.py

echo 2. Launching Backend on http://localhost:8000 ...
start "BHULEKH Backend (FastAPI)" cmd /k "python -m uvicorn main:app --port 8000 --reload"

echo 3. Launching Frontend on http://localhost:3000 ...
cd /d "%SCRIPT_DIR%frontend"
start "BHULEKH Frontend (Next.js)" cmd /k "npm run dev"

echo.
echo =================================================================
echo   Backend API:   http://localhost:8000
echo   Swagger Docs:  http://localhost:8000/docs
echo   Frontend UI:   http://localhost:3000
echo =================================================================
