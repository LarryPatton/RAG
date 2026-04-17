@echo off
chcp 65001 >nul
REM ============================================
REM RAG Shopping Agent - 一键停止 (Windows)
REM ============================================
REM 停止 Streamlit 和释放内存/显存
REM ============================================

echo ========================================
echo   RAG 购物助手 - 停止中...
echo ========================================

REM --- 1. 停止 Streamlit ---
echo.
echo [1/3] 停止 Streamlit...
taskkill /F /FI "WINDOWTITLE eq RAG-Shopping-Agent*" >nul 2>&1
taskkill /F /IM "streamlit.exe" >nul 2>&1

REM 杀掉 streamlit 相关的 python 进程
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST 2^>nul ^| findstr "PID"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /C:"streamlit" >nul 2>&1
    if not errorlevel 1 (
        taskkill /F /PID %%a >nul 2>&1
        echo   已停止 Streamlit 进程 PID: %%a
    )
)
echo   Streamlit 已停止

REM --- 2. 停止 Ollama (可选) ---
echo.
echo [2/3] Ollama 状态...
echo   Ollama 保持运行（手动停止: taskkill /F /IM ollama.exe）
echo   如需释放显存，请手动执行上述命令

REM --- 3. 清理临时文件 ---
echo.
echo [3/3] 清理临时文件...
set "SCRIPT_DIR=%~dp0"
del /F /Q "%SCRIPT_DIR%.pids" >nul 2>&1
echo   已清理

echo.
echo ========================================
echo   已停止所有服务，内存已释放
echo ========================================
echo.
echo   重新启动: start.bat
echo.
echo   彻底释放显存（停止 Ollama）:
echo     taskkill /F /IM ollama.exe
echo.

pause
