@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto setup
".venv\Scripts\python.exe" -c "from setup_bootstrap import supported; import sys,struct,platform,sysconfig; assert supported({'version':list(sys.version_info[:2]),'bits':struct.calcsize('P')*8,'implementation':platform.python_implementation(),'free_threaded':bool(sysconfig.get_config_var('Py_GIL_DISABLED'))}); import PySide6, serial" >nul 2>nul
if errorlevel 1 goto setup
goto launch
:setup
call Setup.bat
if errorlevel 1 exit /b 1
:launch
start "" ".venv\Scripts\pythonw.exe" "%~dp0app.py"
