@echo off
REM ============================================================
REM Draait de scraper lokaal en pusht de resultaten naar GitHub.
REM Dit bestand kun je dubbelklikken om 'm handmatig te draaien,
REM of instellen als dagelijkse taak in Windows Taskplanner.
REM ============================================================

cd /d "%~dp0"

echo Dependencies controleren/installeren...
pip install -r requirements.txt >nul 2>&1
playwright install chromium >nul 2>&1

echo.
echo Scraper draaien...
python run_local.py

echo.
echo Klaar. Dit venster sluit automatisch over 10 seconden.
timeout /t 10 >nul
