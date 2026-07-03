@echo off
REM Generate secure encryption and JWT keys for Socrates Docker deployment
REM Usage: generate-keys.bat [output-file]

setlocal enabledelayedexpansion

if "%~1"=="" (
    set OUTPUT_FILE=.env
) else (
    set OUTPUT_FILE=%~1
)

echo.
echo ============================================================
echo      Socrates Docker Key Generation Tool
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python and add to PATH
    exit /b 1
)

echo Generating secure keys...
echo.

REM Generate keys using Python
for /f "delims=" %%i in ('python -c "import secrets; print(secrets.token_urlsafe(32))"') do set JWT_SECRET=%%i
for /f "delims=" %%i in ('python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"') do set ENCRYPTION_KEY=%%i
for /f "delims=" %%i in ('python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"') do set DB_ENCRYPTION=%%i

echo [OK] JWT_SECRET_KEY generated
echo [OK] SOCRATES_ENCRYPTION_KEY generated
echo [OK] DATABASE_ENCRYPTION_KEY generated
echo.

REM Check if file exists
if exist "%OUTPUT_FILE%" (
    echo WARNING: File '%OUTPUT_FILE%' already exists
    set /p OVERWRITE="Overwrite? (y/n): "
    if /i not "!OVERWRITE!"=="y" (
        echo Cancelled.
        exit /b 0
    )
)

REM Create .env file
(
    echo # Socrates Production Environment Configuration
    echo # Generated on %date% %time%
    echo # IMPORTANT: Keep this file secure and never commit to version control^^!
    echo.
    echo # ============================================================================
    echo # ENCRYPTION ^& SECURITY (Generated - UNIQUE for each environment^)
    echo # ============================================================================
    echo.
    echo # Encryption key for storing provider API keys and sensitive data in database
    echo SOCRATES_ENCRYPTION_KEY=%ENCRYPTION_KEY%
    echo.
    echo # Encryption key for database-level encryption
    echo DATABASE_ENCRYPTION_KEY=%DB_ENCRYPTION%
    echo.
    echo # JWT Secret Key - CRITICAL for session persistence across container restarts
    echo # MUST BE CONSISTENT across all deployments to prevent invalidating user sessions
    echo JWT_SECRET_KEY=%JWT_SECRET%
    echo.
    echo # ============================================================================
    echo # API KEY (REQUIRED - Add your Anthropic API key here^)
    echo # ============================================================================
    echo.
    echo # Anthropic API Key (get from https://console.anthropic.com^)
    echo ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE
    echo.
    echo # ============================================================================
    echo # DATABASE CONFIGURATION
    echo # ============================================================================
    echo.
    echo # PostgreSQL credentials (for production use^)
    echo POSTGRES_USER=socrates
    echo POSTGRES_PASSWORD=socrates_dev_password
    echo POSTGRES_DB=socrates_db
    echo.
    echo # ============================================================================
    echo # REDIS CACHE CONFIGURATION
    echo # ============================================================================
    echo.
    echo REDIS_URL=redis://redis:6379/0
    echo.
    echo # ============================================================================
    echo # API CONFIGURATION
    echo # ============================================================================
    echo.
    echo # API host binding (0.0.0.0 for Docker^)
    echo SOCRATES_API_HOST=0.0.0.0
    echo.
    echo # API port
    echo SOCRATES_API_PORT=8000
    echo.
    echo # Allowed hosts
    echo ALLOWED_HOSTS=localhost,127.0.0.1,api,host.docker.internal
    echo.
    echo # CORS allowed origins
    echo CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://api:3000
    echo.
    echo # ============================================================================
    echo # RUNTIME CONFIGURATION
    echo # ============================================================================
    echo.
    echo # Environment (development, staging, production^)
    echo ENVIRONMENT=development
    echo.
    echo # Logging level (DEBUG, INFO, WARNING, ERROR^)
    echo LOG_LEVEL=INFO
    echo.
    echo # Python configuration
    echo PYTHONUNBUFFERED=1
    echo.
    echo # ============================================================================
    echo # NEXT STEPS
    echo # ============================================================================
    echo # 1. Add your ANTHROPIC_API_KEY above (replace sk-ant-YOUR-KEY-HERE^)
    echo # 2. For production, change ENVIRONMENT=production
    echo # 3. For production, generate new POSTGRES_PASSWORD
    echo # 4. Start containers: docker-compose up -d
    echo # 5. Access at: http://localhost:3000
) > "%OUTPUT_FILE%"

echo [OK] Created %OUTPUT_FILE%
echo.
echo ==============================================================
echo IMPORTANT: Next steps
echo ==============================================================
echo 1. Add your Anthropic API key:
echo    - Get from: https://console.anthropic.com
echo    - Edit %OUTPUT_FILE% and replace: sk-ant-YOUR-KEY-HERE
echo.
echo 2. Start Docker:
echo    docker-compose up -d
echo.
echo 3. Access Socrates:
echo    Frontend: http://localhost:3000
echo    API: http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo.
echo [SUCCESS] Keys generated successfully^^!
echo.
