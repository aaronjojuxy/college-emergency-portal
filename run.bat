@echo off
title College Student Emergency Assistance Portal
color 0C

echo ======================================================================
echo    COLLEGE STUDENT EMERGENCY ASSISTANCE PORTAL - RUNNER
echo ======================================================================
echo.

:: Detect Python executable
set "PYTHON_EXE=python"
python --version >nul 2>&1
if errorlevel 1 (
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    ) else if exist "C:\Python311\python.exe" (
        set "PYTHON_EXE=C:\Python311\python.exe"
    ) else (
        echo [ERROR] Python not found. Please ensure Python 3.11 is installed.
        pause
        exit /b 1
    )
)

echo [*] Using Python: %PYTHON_EXE%
echo [*] Checking dependencies...
"%PYTHON_EXE%" -m pip install -r requirements.txt --quiet

echo [*] Initializing SQLite database and verifying seed data...
"%PYTHON_EXE%" database.py

echo.
echo ======================================================================
echo  SERVER STARTING:
echo   - On this PC:        http://127.0.0.1:5000
echo   - On Mobile / Wi-Fi: Check the IP printed below (e.g. http://192.168.1.7:5000)
echo.
echo  Demo Credentials:
echo    Student:   student1   / password123
echo    Responder: security1  / security123
echo    Admin:     admin      / admin123
echo ======================================================================
echo.

:: Open default web browser after 2 seconds in background
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000"

:: Start the Flask app
"%PYTHON_EXE%" app.py

pause
