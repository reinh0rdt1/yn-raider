@echo off
title YN Raider Setup & Run Console

:: Initialize
setlocal EnableDelayedExpansion
set "APP_NAME=YN Raider"
set "PORT=5000"
set "PYTHON_MIN_VERSION=3.8"
set "FLASK_MIN_VERSION=2.0"
set "TLS_CLIENT_MIN_VERSION=0.2"

:: Set script directory as current directory
cd /d "%~dp0"

:: Enable ANSI color support for Windows 11
reg add "HKCU\Console" /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1

:: Color codes (using echo. to ensure no trailing 'echo')
set "COLOR_GREEN=echo.[32m"
set "COLOR_ORANGE=echo.[33m"
set "COLOR_RED=echo.[31m"
set "COLOR_RESET=echo.[0m"

cls
%COLOR_GREEN%[Success] Starting %APP_NAME% setup... Please wait...%COLOR_RESET%
echo.

:: Check if Python is installed
%COLOR_GREEN%[Success] Checking for Python...%COLOR_RESET%
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    %COLOR_RED%[Error] Python is not installed.%COLOR_RESET%
    %COLOR_RED%[Error] Please download and install Python %PYTHON_MIN_VERSION% or higher from https://www.python.org/downloads/%COLOR_RESET%
    pause
    exit /b 1
)

:: Check Python version
for /f "tokens=2 delims= " %%v in ('python --version 2^>nul') do set "PYTHON_VERSION=%%v"
for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
    set "PYTHON_MAJOR=%%a"
    set "PYTHON_MINOR=%%b"
)
if !PYTHON_MAJOR! LSS 3 (
    %COLOR_RED%[Error] Python !PYTHON_VERSION! is not supported.%COLOR_RESET%
    %COLOR_RED%[Error] Please install Python %PYTHON_MIN_VERSION% or higher.%COLOR_RESET%
    pause
    exit /b 1
)
if !PYTHON_MAJOR!==3 if !PYTHON_MINOR! LSS 8 (
    %COLOR_RED%[Error] Python !PYTHON_VERSION! is too old.%COLOR_RESET%
    %COLOR_RED%[Error] Please install Python %PYTHON_MIN_VERSION% or higher.%COLOR_RESET%
    pause
    exit /b 1
)
%COLOR_GREEN%[Success] Python !PYTHON_VERSION! is installed and compatible.%COLOR_RESET%

:: Check if pip is installed
%COLOR_GREEN%[Success] Checking for pip...%COLOR_RESET%
python -m pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    %COLOR_RED%[Error] pip is not installed.%COLOR_RESET%
    %COLOR_RED%[Error] Please ensure pip is installed with Python. Reinstall Python or run 'python -m ensurepip --upgrade'.%COLOR_RESET%
    pause
    exit /b 1
)
%COLOR_GREEN%[Success] pip is installed.%COLOR_RESET%

:: Install required packages
%COLOR_GREEN%[Success] Installing dependencies (flask, tls_client)...%COLOR_RESET%
:: Flask
python -m pip install flask --upgrade >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    %COLOR_ORANGE%[Warning] Failed to install/upgrade Flask. It may already be installed, continuing...%COLOR_RESET%
) else (
    %COLOR_GREEN%[Success] Flask installed/upgraded successfully.%COLOR_RESET%
)
:: tls_client
python -m pip install tls_client --upgrade >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    %COLOR_ORANGE%[Warning] Failed to install/upgrade tls_client. It may already be installed, continuing...%COLOR_RESET%
) else (
    %COLOR_GREEN%[Success] tls_client installed/upgraded successfully.%COLOR_RESET%
)

:: Check module versions
%COLOR_GREEN%[Success] Checking module versions...%COLOR_RESET%
:: Flask version
for /f "tokens=2" %%v in ('pip show flask 2^>nul ^| findstr Version') do set "FLASK_VERSION=%%v"
if not defined FLASK_VERSION (
    %COLOR_RED%[Error] Flask is not installed.%COLOR_RESET%
    %COLOR_RED%[Error] Please run 'pip install flask' manually.%COLOR_RESET%
    pause
    exit /b 1
)
for /f "tokens=1 delims=." %%a in ("!FLASK_VERSION!") do set "FLASK_MAJOR=%%a"
if !FLASK_MAJOR! LSS 2 (
    %COLOR_RED%[Error] Flask version !FLASK_VERSION! is too old.%COLOR_RESET%
    %COLOR_RED%[Error] Please upgrade Flask to %FLASK_MIN_VERSION% or higher using 'pip install flask --upgrade'.%COLOR_RESET%
    pause
    exit /b 1
)
%COLOR_GREEN%[Success] Flask version !FLASK_VERSION! is compatible.%COLOR_RESET%

:: tls_client version
for /f "tokens=2" %%v in ('pip show tls_client 2^>nul ^| findstr Version') do set "TLS_CLIENT_VERSION=%%v"
if not defined TLS_CLIENT_VERSION (
    %COLOR_RED%[Error] tls_client is not installed.%COLOR_RESET%
    %COLOR_RED%[Error] Please run 'pip install tls_client' manually.%COLOR_RESET%
    pause
    exit /b 1
)
for /f "tokens=1 delims=." %%a in ("!TLS_CLIENT_VERSION!") do set "TLS_CLIENT_MAJOR=%%a"
if !TLS_CLIENT_MAJOR! LSS 0 (
    %COLOR_RED%[Error] tls_client version !TLS_CLIENT_VERSION! is too old.%COLOR_RESET%
    %COLOR_RED%[Error] Please upgrade tls_client to %TLS_CLIENT_MIN_VERSION% or higher using 'pip install tls_client --upgrade'.%COLOR_RESET%
    pause
    exit /b 1
)
%COLOR_GREEN%[Success] tls_client version !TLS_CLIENT_VERSION! is compatible.%COLOR_RESET%

:: Start the server
%COLOR_GREEN%[Success] Starting %APP_NAME% server...%COLOR_RESET%
start "" "http://localhost:%PORT%"
python app.py
if %ERRORLEVEL% NEQ 0 (
    %COLOR_RED%[Error] Failed to start the server.%COLOR_RESET%
    %COLOR_RED%[Error] Please ensure app.py exists, has no syntax errors, and port %PORT% is not in use.%COLOR_RESET%
    pause
    exit /b 1
)

%COLOR_GREEN%[Success] %APP_NAME% server started successfully. Discord Server: https://discord.gg/d5XMev3stu Join Now! %COLOR_RESET%
pause
goto :end

:end
%COLOR_RESET%
endlocal
