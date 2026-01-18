@echo off
REM Socrates AI - Full Stack Launcher
REM Launches Socrates with API + Frontend + Browser
REM This script should be placed in the same directory as socrates.exe

echo.
echo ========================================
echo Socrates AI - Full Stack
echo ========================================
echo.

if not exist "socrates.exe" (
    echo Error: socrates.exe not found!
    echo Make sure this batch file is in the same directory as socrates.exe
    pause
    exit /b 1
)

echo Starting Socrates with:
echo   - API Server (FastAPI)
echo   - React Frontend
echo   - Browser (auto-open)
echo.
echo A browser window will open automatically.
echo Press Ctrl+C to stop the server.
echo.

socrates.exe --full
