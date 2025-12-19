# Activate Socrates venv and run the CLI
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
& .\.venv\Scripts\Activate.ps1
python socrates.py
