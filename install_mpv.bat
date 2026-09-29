@echo off
echo Installing mpv with winget...
winget install --id=shinchiro.mpv -e --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
  echo.
  echo mpv installation failed. Check that winget is available and try again.
  pause
  exit /b 1
)
echo.
echo Finished. Close and reopen PowerShell, then run .\run.bat
pause
