@echo off
title Turbo YouTube to 3GP Converter
cd /d "%~dp0"

echo ====================================================================
echo        ⚡ TURBO YOUTUBE TO 3GP CONVERTER (For Button Phones)
echo       Nokia, Symphony, Walton, Itel, Sanee, Samsung Feature Phones
echo ====================================================================
echo.

if "%~1"=="" (
    python yt3gp.py
) else (
    python yt3gp.py "%~1"
)
