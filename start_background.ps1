# Start V-CAD as a detached Windows background process
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$Port = if ($args[0]) { $args[0] } else { 8080 }
Write-Host "Starting V-CAD Background Server on port $Port..." -ForegroundColor Cyan

python daemon_service.py start $Port

Write-Host ""
Write-Host "Server runs detached in the background." -ForegroundColor Green
Write-Host "You can safely CLOSE this PowerShell window." -ForegroundColor Yellow
Write-Host "Access web app at: http://localhost:$Port" -ForegroundColor Cyan
