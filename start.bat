@echo off
rem Free My Fire Stick for Windows: double-click this file.
cd /d "%~dp0"
where py >nul 2>nul && (py -3 firestick.py %* & goto :end)
where python >nul 2>nul && (python firestick.py %* & goto :end)
echo Python 3 is needed. Installing it with winget (Windows 10/11)...
winget install -e --id Python.Python.3.12 --accept-source-agreements
echo.
echo Done. Close this window and double-click start.bat again.
:end
pause
