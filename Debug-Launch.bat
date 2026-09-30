@echo off
setlocal
cd /d "%~dp0"
call Setup.bat
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" app.py
pause
