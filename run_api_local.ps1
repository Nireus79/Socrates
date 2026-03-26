# Run API with LOCAL code (monorepo)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$ScriptDir\backend\src;$ScriptDir\cli\src;$env:PYTHONPATH"

Write-Host "Starting Socrates API with LOCAL code (monorepo)" -ForegroundColor Green
Write-Host "PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Yellow
Write-Host ""

python -m socrates_api
