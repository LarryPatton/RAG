@echo off
chcp 65001 >nul 2>&1

echo ========================================
echo   RAG Shopping Agent - Stopping...
echo ========================================
echo.

REM --- 1. Kill Streamlit ---
echo [1/2] Stopping Streamlit...
taskkill /FI "WINDOWTITLE eq RAG-Agent-Streamlit*" /F >nul 2>&1

REM Kill all python processes running streamlit
for /f "tokens=2 delims=," %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH 2^>nul') do (
    wmic process where "ProcessId=%%~i" get CommandLine 2>nul | findstr /C:"streamlit" >nul 2>&1
    if not errorlevel 1 (
        taskkill /F /PID %%~i >nul 2>&1
    )
)
echo   Streamlit stopped. Memory released.

REM --- 2. Ollama ---
echo.
echo [2/2] Ollama status...
echo   Ollama kept running (shared resource).
echo   To free GPU memory, run: taskkill /F /IM ollama.exe

echo.
echo ========================================
echo   All services stopped.
echo ========================================
echo.
echo   Restart: start.bat
echo.
pause
