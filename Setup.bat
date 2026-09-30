@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 goto launcher
where python >nul 2>nul
if not errorlevel 1 goto python
echo Python was not found. Install standard 64-bit Python 3.10-3.14 from https://www.python.org/downloads/windows/
echo Enable the Python launcher during installation, then run Setup.bat again.
pause
exit /b 1
:launcher
py -3 setup_bootstrap.py
if errorlevel 1 goto failed
exit /b 0
:python
python setup_bootstrap.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo Setup could not finish. Review the message above.
pause
exit /b 1
