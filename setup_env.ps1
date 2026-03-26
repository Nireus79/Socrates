# Setup environment for Socrates monorepo development
# Usage: .\setup_env.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendSrc = Join-Path $ScriptDir "backend\src"
$CliSrc = Join-Path $ScriptDir "cli\src"

# Set PYTHONPATH to include local code
$env:PYTHONPATH = "$BackendSrc;$CliSrc;$env:PYTHONPATH"

Write-Host "=================================================" -ForegroundColor Green
Write-Host "Socrates Monorepo Environment Setup" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""
Write-Host "PYTHONPATH configured for local imports:" -ForegroundColor Yellow
Write-Host "  Backend: $BackendSrc"
Write-Host "  CLI:     $CliSrc"
Write-Host ""
Write-Host "You can now run:" -ForegroundColor Yellow
Write-Host "  python -m socrates_api         # Start API server"
Write-Host "  cd frontend && npm run dev     # Start frontend"
Write-Host ""
