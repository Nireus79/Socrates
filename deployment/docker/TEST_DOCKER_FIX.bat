@echo off
REM Docker Configuration Fix Test - Windows Batch Script

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Docker Configuration Fix Test
echo ========================================
echo.

REM Check Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed or not in PATH
    exit /b 1
)

echo [OK] Docker and Docker Compose are installed
echo.

REM Get current directory
set DOCKER_DIR=%~dp0
cd /d "%DOCKER_DIR%"

echo [1/8] Checking environment configuration...
findstr /M "SOCRATES_DATA_DIR=/app/data" docker-compose.yml >nul
if errorlevel 1 (
    echo [ERROR] SOCRATES_DATA_DIR not found in docker-compose.yml
    exit /b 1
)
echo [OK] SOCRATES_DATA_DIR is set to /app/data

findstr /M "VITE_API_URL: http://localhost:8000" docker-compose.yml >nul
if errorlevel 1 (
    echo [ERROR] Frontend API URL not configured correctly
    exit /b 1
)
echo [OK] Frontend VITE_API_URL is set to http://localhost:8000
echo.

echo [2/8] Stopping existing containers...
docker-compose down --remove-orphans >nul 2>&1
echo [OK] Containers stopped
echo.

echo [3/8] Removing old data volumes...
docker volume rm socrates_data >nul 2>&1
docker volume rm socrates_logs >nul 2>&1
echo [OK] Old volumes cleaned
echo.

echo [4/8] Checking .env file...
if not exist ".env" (
    echo [WARNING] .env file not found. Creating from .env.docker...
    copy .env.docker .env >nul
    echo [WARNING] Please edit .env and add your ANTHROPIC_API_KEY
    echo [WARNING] Then run this script again
    exit /b 0
) else (
    echo [OK] .env file exists
)
echo.

echo [5/8] Building Docker images (this may take a few minutes)...
docker-compose build --no-cache
if errorlevel 1 (
    echo [ERROR] Docker build failed
    exit /b 1
)
echo [OK] Build complete
echo.

echo [6/8] Starting containers...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start containers
    exit /b 1
)
echo [OK] Containers started
echo.

echo [7/8] Waiting for services to be healthy...
echo Please wait (this can take 30-60 seconds)...
echo.

setlocal enabledelayedexpansion
set max_attempts=30
set attempt=0

:wait_loop
if !attempt! geq !max_attempts! (
    echo [ERROR] Services failed to start within timeout
    docker-compose logs api
    exit /b 1
)

docker-compose ps | findstr "api.*Up" >nul
if errorlevel 1 (
    set /a attempt=!attempt!+1
    timeout /t 2 /nobreak >nul
    goto wait_loop
)

echo [OK] API is up
echo.

echo [8/8] Verifying configuration...

REM Check SOCRATES_DATA_DIR in running container
for /f "delims=" %%i in ('docker-compose exec api env ^| findstr SOCRATES_DATA_DIR 2^>nul') do set DATA_DIR=%%i
if "!DATA_DIR!"=="" (
    echo [ERROR] SOCRATES_DATA_DIR not set in running container
    exit /b 1
)
echo [OK] SOCRATES_DATA_DIR is set: !DATA_DIR!
echo.

echo ========================================
echo [SUCCESS] ALL CHECKS PASSED!
echo ========================================
echo.

echo Next Steps:
echo 1. Open http://localhost:3000 in your browser
echo 2. Create a test user account
echo 3. Create a test project
echo 4. Run the persistence test (see below)
echo.

echo Persistence Test:
echo To verify data persists across restarts:
echo.
echo   docker-compose down
echo   docker-compose up -d
echo.
echo   Verify your user and project still exist at http://localhost:3000
echo.

echo Useful Commands:
echo   docker-compose logs -f api        # Watch API logs
echo   docker-compose logs -f frontend   # Watch frontend logs
echo   docker-compose exec api cmd       # Access API container
echo   docker volume ls                  # List volumes
echo.

echo Service URLs:
echo   Frontend:     http://localhost:3000
echo   API:          http://localhost:8000
echo   API Docs:     http://localhost:8000/docs
echo.

endlocal
