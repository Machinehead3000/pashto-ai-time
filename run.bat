@echo off
set VENV_DIR=.venv

echo Checking for virtual environment...
if not exist "%VENV_DIR%" (
    echo Creating virtual environment in %VENV_DIR%...
    python -m venv %VENV_DIR%
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment. Please ensure Python is installed and in your PATH.
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call "%VENV_DIR%\\Scripts\\activate.bat"

echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo Starting the application...
python main.py

echo.
echo Application has been closed.
pause 