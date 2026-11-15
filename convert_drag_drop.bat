@echo off
title 3GP Instant Converter (Drag and Drop)
cd /d "%~dp0"
echo ========================================================
echo       3GP BUTTON PHONE INSTANT DRAG & DROP CONVERTER
echo ========================================================
echo.

if "%~1"=="" (
    echo [!] Kono file ba folder drop kora hoyni!
    echo.
    echo Usage: Eita te kono MP4 ba video file tene ene chere din (Drag and Drop).
    echo Ba shob video ekta folder a rekhe folder ta drop korun.
    echo.
    echo Default e Web Interface chalate "run.bat" double click korun.
    echo ========================================================
    pause
    exit /b
)

echo [*] File convert shuru hocche...
python cli.py "%~1" -p standard

echo.
echo ========================================================
echo [*] Converted 3GP file "output" folder e paben:
explorer.exe "%~dp0output"
echo ========================================================
pause
