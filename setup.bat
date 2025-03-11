@echo off
title YN Raider Setup & Run

echo Starting YN Raider...
echo Please wait...

:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed.
    echo Download it from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Install required packages silently
pip install flask tls_client >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install dependencies.
    pause
    exit /b 1
)

:: Check required files
if not exist app.py (
    echo Error: app.py is missing.
    goto :missing_files
)
if not exist templates/index.html (
    echo Error: templates/index.html is missing.
    goto :missing_files
)

:: Start the server
start "" "http://localhost:5000"
python app.py
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to start the server.
    pause
    exit /b 1
)

pause
goto :end

:missing_files
echo Error: Some files are missing.
echo Download the full tool from GitHub.
pause
exit /b 1

:end
