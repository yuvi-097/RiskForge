@echo off
echo Running RiskForge API Tests (Bypassing Execution Policy)...
PowerShell -NoProfile -ExecutionPolicy Bypass -File "%~dp0test_api.ps1"
if %errorlevel% neq 0 (
    echo.
    echo Validating server availability...
    timeout /t 2 >nul
    curl -s http://127.0.0.1:8080/health >nul 2>&1
    if %errorlevel% neq 0 (
        echo Error: API Gateway is not running on port 8080.
        echo Please starting it with: python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
    )
    pause
)
