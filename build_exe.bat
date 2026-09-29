@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
pyinstaller --noconfirm --clean --windowed --name NoToto --collect-all yt_dlp main.py
echo.
echo EXE built. Audio playback does not require mpv.
pause
