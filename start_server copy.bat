@echo off
cd /d "%~dp0"

REM 
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 "detection_server.py"
) else (
    python "detection_server.py"
)

pause