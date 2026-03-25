@echo off
echo ========================================
echo   Course Compass - Starting Services
echo ========================================
echo.

echo [1/2] Starting FastAPI backend on port 8000...
start "Course Compass Backend" cmd /k "cd /d "%~dp0backend" && pip install -r requirements.txt -q && uvicorn main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Vue frontend on port 5173...
start "Course Compass Frontend" cmd /k "cd /d "%~dp0frontend" && npm install && npm run dev"

echo.
echo ========================================
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo  API Docs: http://localhost:8000/docs
echo ========================================
echo.
echo Both servers are starting in separate windows.
echo Press any key to exit this window...
pause >nul
