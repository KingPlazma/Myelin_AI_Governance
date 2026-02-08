@echo off
echo ==================================================
echo      MYELIN AI GOVERNANCE - DEMO INSTALLER
echo ==================================================
echo.
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies. Please check your Python installation.
    pause
    exit /b %errorlevel%
)

echo.
echo ==================================================
echo           STARTING MYELIN ORCHESTRATOR
echo ==================================================
echo.
python orchestrator\main.py
pause
