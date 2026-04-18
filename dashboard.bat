@echo off
cd /d "%~dp0"
title RAG Shopping Agent

echo ==========================================
echo   RAG Shopping Agent
echo ==========================================
echo.

echo [1/3] Clearing ports...
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":5173 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":7788 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
)

:wait8000
netstat -ano 2>nul | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 ( timeout /t 1 /nobreak >nul & goto wait8000 )

:wait5173
netstat -ano 2>nul | findstr ":5173 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 ( timeout /t 1 /nobreak >nul & goto wait5173 )

:wait7788
netstat -ano 2>nul | findstr ":7788 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 ( timeout /t 1 /nobreak >nul & goto wait7788 )

echo [2/3] Starting services...
call pm2 delete rag-api rag-web rag-dashboard >nul 2>&1
call pm2 start "%~dp0ecosystem.config.cjs"
if errorlevel 1 (
    echo [ERROR] pm2 start failed
    pause
    exit /b 1
)

timeout /t 3 /nobreak >nul

echo.
echo [3/3] Done!
echo.
echo   Dashboard: http://localhost:7788
echo   Frontend:  http://localhost:5173
echo   API Docs:  http://localhost:8000/docs
echo.
echo   To stop:   pm2 stop all
echo   To restart: use the dashboard web page
echo.
echo ==========================================
echo   Opening dashboard in browser...
echo ==========================================

start http://localhost:7788

echo.
echo   Press any key to close this window.
echo   (Services will keep running in background)
pause >nul
