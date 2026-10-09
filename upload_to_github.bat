@echo off
title Push Project to GitHub
color 0A

echo ======================================================================
echo       UPLOAD COLLEGE EMERGENCY ASSISTANCE PORTAL TO GITHUB
echo ======================================================================
echo.

:: Check git and add to PATH if needed
where git >nul 2>&1
if errorlevel 1 (
    if exist "C:\Program Files\Git\cmd" (
        set "PATH=C:\Program Files\Git\cmd;%PATH%"
    ) else if exist "%LOCALAPPDATA%\Programs\Git\cmd" (
        set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"
    ) else (
        echo [ERROR] Git is not recognized. Please reopen this terminal or restart your PC.
        pause
        exit /b 1
    )
)

echo [*] Local Git repository is ready on branch 'main'.
echo.
echo Please create a new empty repository on GitHub:
echo   1. Open https://github.com/new in your browser.
echo   2. Name it (e.g., college-emergency-portal).
echo   3. Leave "Add a README", ".gitignore" UNCHECKED.
echo   4. Click "Create repository".
echo.
echo ======================================================================
set /p REPO_URL="Paste your GitHub repository URL here (e.g., https://github.com/username/repo.git): "

if "%REPO_URL%"=="" (
    echo [ERROR] No URL provided. Exiting.
    pause
    exit /b 1
)

echo.
echo [*] Adding remote origin: %REPO_URL%
git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%

echo [*] Pushing files to GitHub branch 'main'...
git push -u origin main

if errorlevel 1 (
    echo.
    echo [!] Push failed. If prompted for GitHub login, please sign in via browser or Personal Access Token.
) else (
    echo.
    echo ======================================================================
    echo  [SUCCESS] Project uploaded to GitHub successfully!
    echo ======================================================================
)

echo.
pause
