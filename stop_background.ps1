# Stop V-CAD background server
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "Stopping V-CAD Background Server..." -ForegroundColor Yellow
python daemon_service.py stop
