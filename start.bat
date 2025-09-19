@echo off
echo Starting Traffic Simulator...
echo.

REM Start backend in a new window
echo Starting Backend Server...
start "Backend Server" cmd /k "cd /d "%~dp0backend" && ..\.venv\Scripts\python.exe app.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
echo Starting Frontend Server...
start "Frontend Server" cmd /k "cd /d "%~dp0frontend" && npm start"

echo.
echo Both servers are starting in separate windows...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit this script (servers will continue running)...
pause >nul