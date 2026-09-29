@echo off
cd /d "%~dp0"

python -c "import PySide6; from PySide6.QtWebEngineWidgets import QWebEngineView" >nul 2>&1
if errorlevel 1 (
  echo Installing Python dependencies...
  python -m pip install -r requirements.txt
  if errorlevel 1 exit /b 1
)

python main.py
pause
