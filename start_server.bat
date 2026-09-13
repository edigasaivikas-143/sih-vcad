@echo off
title V-CAD Automated 3D Engine Server (SIH 2026)
cls
echo ====================================================================
echo   V-CAD: Automated 3D Model Generation ^& 3D ULPIN Engine
echo   Smart India Hackathon 2026 - SVAMITVA 3D Cadastre
echo ====================================================================
echo.
echo Starting backend HTTP web server on port 8080...
echo Keep this window OPEN while using the application.
echo.
echo Open your browser at:
echo   http://localhost:8080
echo.
python -u server.py 8080
pause
