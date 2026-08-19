@echo off
REM One-click launcher for Lamp Studio. Opens the app in your browser.
cd /d "%~dp0"
start "" pythonw server.py
timeout /t 2 >nul
start "" http://127.0.0.1:8776/
exit
