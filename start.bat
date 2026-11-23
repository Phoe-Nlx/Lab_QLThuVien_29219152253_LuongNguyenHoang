@echo off
chcp 65001 >nul
echo ========================================================
echo   HE THONG QUAN LY THU VIEN UNG DUNG AI (SmartLib AI)
echo ========================================================
echo Dang khoi dong may chu tai http://localhost:8080 ...
start "" "http://localhost:8080"
cd /d "%~dp0src"
python app.py
pause
