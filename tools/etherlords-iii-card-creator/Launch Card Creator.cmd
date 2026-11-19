@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    python -m venv ".venv"
    if errorlevel 1 py -3 -m venv ".venv"
    if not exist ".venv\Scripts\pythonw.exe" goto setup_failed
)
".venv\Scripts\python.exe" -c "import tkinter, PIL, sys; assert sys.version_info >= (3, 11) and sys.maxsize > 2**32"
if errorlevel 1 (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto setup_failed
    ".venv\Scripts\python.exe" -c "import tkinter, PIL, sys; assert sys.version_info >= (3, 11) and sys.maxsize > 2**32"
    if errorlevel 1 goto setup_failed
)
start "" ".venv\Scripts\pythonw.exe" "%~dp0app.py"
exit /b
:setup_failed
echo Install 64-bit Python 3.11 or newer with Tcl/Tk and the Python Launcher, then retry.
pause
exit /b 1
