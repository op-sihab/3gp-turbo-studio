@echo off
title YouTube to 3GP Turbo Downloader & Converter
cd /d "%~dp0"
echo ========================================================
echo   YOUTUBE TO 3GP TURBO DOWNLOADER (Core i3 Optimized)
echo ========================================================
echo.
set /p "YT_URL=Enter YouTube Video URL: "
if "%YT_URL%"=="" (
    echo [!] URL cannot be empty!
    pause
    exit /b
)
echo.
python ytdlp_download.py "%YT_URL%" standard
echo.
echo Opening output folder...
explorer.exe "%~dp0output"
pause
