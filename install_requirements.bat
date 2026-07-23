@echo off
echo ==========================================
echo Installing Python Dependencies...
echo ==========================================

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Installation Complete!
pause
