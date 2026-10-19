@echo off
chcp 65001 >nul
cd /d "%~dp0"
python --version >/dev/null 2>&1 || (
  echo Python was not found. Install Python 3.11 64-bit from python.org
  echo and tick "Add python.exe to PATH" during setup, then run this again.
  pause
  exit /b 1
)
python -m pip install --upgrade pip
python -m pip install faster-whisper
echo.
echo Installed. Open your timeline in DaVinci Resolve and double-click run.bat
pause
