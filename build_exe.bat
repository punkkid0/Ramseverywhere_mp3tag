@echo off
setlocal
cd /d "%~dp0"

echo === Ramseverywhere MP3 Tag - Windows build ===
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Install Python 3.11+ and try again.
    pause
    exit /b 1
)

echo [1/4] Installing dependencies...
pip install -r requirements-build.txt
if errorlevel 1 goto :fail

echo [2/4] Building icon...
python scripts\make_icon.py
if errorlevel 1 goto :fail

echo [3/4] Running PyInstaller...
python -m PyInstaller --noconfirm --clean mp3tag.spec
if errorlevel 1 goto :fail

echo [4/4] Done!
echo.
echo Your .exe is here:
echo   dist\Ramseverywhere_MP3_Tag.exe
echo.
echo Send that file to workers. They do NOT need Python installed.
echo Optional: put config.yaml next to the .exe to override site names / comment.
echo Workers still need ffmpeg on PATH if remux is required.
echo.
pause
exit /b 0

:fail
echo Build failed.
pause
exit /b 1