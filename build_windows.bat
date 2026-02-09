@echo off
REM Build standalone Windows EXE for vertualMarker Strategy 2 GUI
REM Requirements:
REM   - Python 3.10+
REM   - pip install pyinstaller

SET SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo Building vertualMarker_app.exe with PyInstaller...
pyinstaller --noconfirm --onefile --name vertualmarker_app app.py

echo.
echo Build finished. Check the dist folder for vertualmarker_app.exe
echo.
pause

