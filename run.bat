@echo off
cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo [Error] Virtual environment not found in this folder.
    echo Run this first, one time only:
    echo     python -m venv venv
    echo     venv\Scripts\activate
    echo     pip install -r requirements.txt
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

python app.py
if errorlevel 1 (
    echo.
    echo [Error] The app exited with an error - see the message above.
    pause
    exit /b 1
)

pause