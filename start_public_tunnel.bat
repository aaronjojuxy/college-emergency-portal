@echo off
title College Emergency Portal - Public Tunnel
color 0B

:: Detect Python executable
set "PYTHON_EXE=python"
python --version >nul 2>&1
if errorlevel 1 (
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    ) else if exist "C:\Python311\python.exe" (
        set "PYTHON_EXE=C:\Python311\python.exe"
    )
)

"%PYTHON_EXE%" start_tunnel.py

pause
