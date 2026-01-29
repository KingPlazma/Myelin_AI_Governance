@echo off
echo ==================================================
echo      MYELIN AI GOVERNANCE - WEB DEMO LAUNCHER
echo ==================================================
echo.

echo [1/3] Checking dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Starting API Server (Backend)...
start "MYELIN API SERVER" cmd /k "python orchestrator\api_server_all_pillars.py"

echo.
echo [3/3] Opening Frontend Dashboard...
timeout /t 5 >nul
start frontend\index.html

echo.
echo ==================================================
echo    SYSTEM IS RUNNING!
echo    - API Server: http://localhost:8000
echo    - Frontend: Opened in your default browser
echo ==================================================
echo.
echo Close the API Server window to stop the system.
pause
