@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\pyvenv.cfg" (
    echo Complete the Windows setup in README.md, then open Play.cmd again.
    pause
    exit /b 1
)
set "gamePython=%CD%\.venv\Scripts\python.exe"
for /f "tokens=1,* delims==" %%A in ('findstr /b /c:"home = " ".venv\pyvenv.cfg"') do set "gameHome=%%B"
if defined gameHome if exist "%gameHome:~1%\python.exe" set "gamePython=%gameHome:~1%\python.exe"
set "PYTHONPATH=%CD%\src;%CD%\.venv\Lib\site-packages"
"%gamePython%" -m smart_racing %*
if errorlevel 1 (
    pause
    exit /b 1
)
