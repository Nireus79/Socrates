@echo off
REM Complete Socrates Startup Script for Windows
REM Starts API server, frontend, and displays CLI instructions

setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0"
set "API_PORT=8000"
set "FRONTEND_PORT=5173"

cls
echo.
echo ======================================================================
echo          ^>^> SOCRATES - Complete Modular System Startup
echo ======================================================================
echo.

REM 1. Start API Server
echo [%date% %time%] Starting Socrates API server...

cd /d "%PROJECT_ROOT%backend"

REM Check if venv exists
if not exist ".venv" (
    echo [WARNING] Virtual environment not found. Creating...
    python -m venv .venv
)

REM Activate venv
call .venv\Scripts\activate.bat

REM Install dependencies
pip list | find "fastapi" >nul
if errorlevel 1 (
    echo [WARNING] Installing dependencies...
    pip install -q -e .
)

REM Start API in new window
start "Socrates API Server" cmd /k "cd /d "%PROJECT_ROOT%backend" && .venv\Scripts\activate.bat && python -m uvicorn socrates_api.main:app --reload --host 0.0.0.0 --port %API_PORT%"

REM Wait for API to be ready
echo [%date% %time%] Waiting for API server to be ready...
setlocal disabledelayedexpansion
for /L %%i in (1,1,30) do (
    timeout /t 1 /nobreak >nul
    curl -s http://localhost:%API_PORT%/health >nul 2>&1
    if not errorlevel 1 (
        echo [^✓^] API server is ready on http://localhost:%API_PORT%
        goto api_ready
    )
)
echo [ERROR] API server failed to start
exit /b 1

:api_ready

REM 2. Start Frontend
echo [%date% %time%] Starting Socrates Frontend...

cd /d "%PROJECT_ROOT%socrates-frontend"

REM Check if node_modules exists
if not exist "node_modules" (
    echo [WARNING] Installing frontend dependencies...
    call npm install
)

REM Start frontend in new window
start "Socrates Frontend" cmd /k "cd /d "%PROJECT_ROOT%socrates-frontend" && npm run dev -- --port %FRONTEND_PORT%"

REM Wait for frontend
timeout /t 5 /nobreak >nul
echo [^✓^] Frontend started on http://localhost:%FRONTEND_PORT%

REM 3. Display instructions
cls
echo.
echo ======================================================================
echo              ^>^> SOCRATES IS RUNNING - Choose Your Interface
echo ======================================================================
echo.

echo [WEB FRONTEND - Recommended for Chat]
echo   URL: http://localhost:%FRONTEND_PORT%
echo   - Interactive Socratic chat interface
echo   - Visual project management
echo   - Real-time specs and conflicts
echo.

echo [REST API]
echo   URL: http://localhost:%API_PORT%
echo   - Full REST API for programmatic access
echo   - OpenAPI docs: http://localhost:%API_PORT%/docs
echo.

echo [COMMAND LINE INTERFACE - CLI]
echo   Usage: python -m socrates_cli ^<command^>
echo.
echo   Quick start:
echo   - socrates project create --name "My Project"
echo   - socrates chat                              # Interactive Socratic chat
echo   - socrates project list                      # List projects
echo   - socrates maturity status                   # Check maturity
echo   - socrates subscription status               # Check subscription
echo.
echo   For more commands:
echo   - socrates --help
echo.

echo ======================================================================
echo              SYSTEM COMPONENTS
echo ======================================================================
echo.

echo [v] API Server        (localhost:%API_PORT%)
echo [v] Web Frontend      (localhost:%FRONTEND_PORT%)
echo [v] CLI Tool          (ready for commands)
echo.

echo ======================================================================
echo              INTEGRATION NOTES
echo ======================================================================
echo.

echo Environment Variables:
echo   SOCRATES_API_URL=http://localhost:%API_PORT% (for CLI^)
echo   ANTHROPIC_API_KEY=^<your-key^>                   (for LLM^)
echo.

echo Key Features:
echo   v Socratic Question Generation
echo   v Spec Extraction from Responses
echo   v Conflict Detection
echo   v Maturity Tracking
echo   v Phase Transitions
echo   v Real-time Feedback
echo.

echo ======================================================================
echo              TESTING YOUR SETUP
echo ======================================================================
echo.

echo 1. Test API Health:
echo    curl http://localhost:%API_PORT%/health
echo.

echo 2. Create a Project (via CLI^):
echo    python -m socrates_cli project create --name "Calculator App"
echo.

echo 3. Start Interactive Chat (via CLI^):
echo    python -m socrates_cli chat
echo.

echo 4. Open Web Frontend:
echo    Open browser to: http://localhost:%FRONTEND_PORT%
echo.

echo ======================================================================
echo              STOPPING SOCRATES
echo ======================================================================
echo.

echo To stop all services:
echo   1. Close the API and Frontend windows
echo   2. Press Ctrl+C to close this window
echo.

echo ======================================================================
echo.
echo To view all available CLI commands:
echo   python -m socrates_cli --help
echo.

pause
