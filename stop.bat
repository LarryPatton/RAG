@echo off
chcp 65001 >nul 2>&1

echo ========================================
echo   RAG Shopping Agent - Stopping...
echo ========================================
echo.

echo [1/2] Stopping FastAPI...
taskkill /FI "WINDOWTITLE eq RAG-FastAPI*" /F >nul 2>&1
for /f "tokens=2 delims=," %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH 2^>nul') do (
    wmic process where "ProcessId=%%~i" get CommandLine 2>nul | findstr /C:"uvicorn" >nul 2>&1
    if not errorlevel 1 taskkill /F /PID %%~i >nul 2>&1
)
echo   FastAPI stopped.

echo.
echo [2/2] Stopping Vite dev server...
taskkill /FI "WINDOWTITLE eq RAG-Vite*" /F >nul 2>&1
for /f "tokens=2 delims=," %%i in ('tasklist /FI "IMAGENAME eq node.exe" /FO CSV /NH 2^>nul') do (
    wmic process where "ProcessId=%%~i" get CommandLine 2>nul | findstr /C:"vite" >nul 2>&1
    if not errorlevel 1 taskkill /F /PID %%~i >nul 2>&1
)
echo   Vite stopped.

echo.
echo ========================================
echo   All services stopped.
echo ========================================
echo.
echo   Restart: start.bat
echo   Free GPU: taskkill /F /IM ollama.exe
echo.
pause
