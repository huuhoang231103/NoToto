@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
pyinstaller --noconfirm --clean --windowed --name NoToto --icon app_icon.ico --add-data "app_icon.ico;." --add-data "app_icon.png;." main.py
echo.
echo EXE built with NoToto app icon.
pause
