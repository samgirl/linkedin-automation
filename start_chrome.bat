@echo off
echo ============================================
echo   AI Content Radar - Chrome Launcher
echo ============================================
echo.
echo This opens Chrome with remote debugging so
echo the app can control it (search LinkedIn,
echo post comments) without opening a new window.
echo.
echo 1. A Chrome window will open
echo 2. Log into LinkedIn in that window
echo 3. Keep this Chrome open while using the app
echo.
echo Press any key to open Chrome...
pause > nul

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

echo.
echo Chrome is running. Keep it open and use the app.
echo Press any key to close this window...
pause > nul
