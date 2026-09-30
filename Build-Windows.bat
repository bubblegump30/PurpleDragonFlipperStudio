@echo off
setlocal
cd /d "%~dp0"
call Setup.bat
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m pip install PyInstaller==6.16.0
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm PurpleDragon.spec
if errorlevel 1 goto failed
echo Build complete: dist\PurpleDragonFlipperStudio\PurpleDragonFlipperStudio.exe
echo Distribute the entire PurpleDragonFlipperStudio folder, including _internal.
echo This is a GUI preview build; device services still require integration.
pause
exit /b 0
:failed
echo Build failed. Review the messages above.
pause
exit /b 1
