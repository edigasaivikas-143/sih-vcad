@echo off
title 3D ULPIN Property Portal + V-CAD 3D Engine (Localhost)
cls
echo ====================================================================
echo   3D ULPIN Property Portal ^& V-CAD Cadastre Engine
echo   Smart India Hackathon (SIH) - SVAMITVA / DILRMP Cadastre
echo ====================================================================
echo.
echo [1] Checking and freeing port 8080 if previously in use...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo.
echo [2] Local Storage Subsystem:
echo     - Blueprints: storage\blueprints\
echo     - Properties: storage\properties.json
echo     - 3D Models:  storage\models\
echo.
echo [3] Starting Unified HTTP Server on port 8080...
echo.
echo --------------------------------------------------------------------
echo   Open your browser at:
echo   http://localhost:8080
echo --------------------------------------------------------------------
echo.
timeout /t 2 /nobreak >nul
start "" "http://localhost:8080"
python -u local_server.py 8080
pause