@echo off
REM Activate Socrates venv and run the CLI
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python socrates.py
pause
