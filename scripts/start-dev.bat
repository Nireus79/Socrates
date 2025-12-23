@echo off
REM Socrates AI - Development Startup Script for Windows
REM
REM Starts the entire system:
REM - Backend API (FastAPI)
REM - Frontend Dev Server (Vite)
REM
REM Usage: Run from Socrates root directory
REM    start-dev.bat

setlocal enabledelayedexpansion

REM Colors and formatting
set GREEN=[92m
set BLUE=[94m
set YELLOW=[93m
set RED=[91m
set END=[0m

REM Check if running from correct directory
if not exist "requirements.txt" (
    echo Error: Please run this script from the Socrates root directory
    pause
    exit /b 1
)

cls
echo.
echo ========================================================
echo     Socrates AI - Development Startup (Windows)
echo ========================================================
echo.

REM Check Python
echo Checking prerequisites...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+
    pause
    exit /b 1
)
echo [OK] Python found

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js 14+
    pause
    exit /b 1
)
echo [OK] Node.js found

REM Install Python dependencies if needed
if not exist "venv" (
    echo.
    echo Installing Python dependencies...
    pip install -q -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install Python dependencies
        pause
        exit /b 1
    )
)
echo [OK] Python dependencies ready

REM Install Node dependencies if needed
if not exist "socrates-frontend\node_modules" (
    echo.
    echo Installing Node.js dependencies...
    cd socrates-frontend
    call npm install -q --legacy-peer-deps
    if errorlevel 1 (
        echo [ERROR] Failed to install Node dependencies
        pause
        exit /b 1
    )
    cd ..
)
echo [OK] Node.js dependencies ready

REM Start services
cls
echo.
echo ========================================================
echo     Starting Services
echo ========================================================
echo.
echo Frontend:       http://localhost:5173
echo Backend API:    http://localhost:8000
echo API Docs:       http://localhost:8000/docs
echo.
echo Press Ctrl+C in each terminal to stop services
echo.

REM Start Backend in one window
start cmd /k "title Socrates Backend && python -m uvicorn socratic_system.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a moment for backend to start
timeout /t 2 /nobreak

REM Start Frontend in another window
start cmd /k "title Socrates Frontend && cd socrates-frontend && npm run dev"

REM Keep main window open
echo.
echo [OK] Services started in separate windows
echo.
echo To stop:
echo   1. Close the backend window (Ctrl+C)
echo   2. Close the frontend window (Ctrl+C)
echo   3. Close this window
echo.
pause
