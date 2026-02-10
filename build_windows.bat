@echo off
REM Build standalone Windows EXE for virtualMarker Strategy 2 GUI
REM Requirements:
REM   - Python 3.10+
REM   - pip install pyinstaller

SET SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo Building virtualmarker_app.exe with PyInstaller...
pyinstaller --noconfirm --onefile --name virtualmarker_app app.py

echo.
echo Build finished. Check the dist folder for virtualmarker_app.exe
echo.
pause

