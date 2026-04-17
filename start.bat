@echo off
chcp 65001 >nul
REM ============================================
REM RAG Shopping Agent - 一键启动 (Windows)
REM ============================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PID_FILE=%SCRIPT_DIR%.pids"
set "OLLAMA_MODEL=qwen2.5:14b"

echo ========================================
echo   RAG 购物助手 - 启动中...
echo ========================================

REM 清理旧 PID 文件
echo. > "%PID_FILE%"

REM --- Step 1: 检查并启动 Ollama ---
echo.
echo [1/3] 检查 Ollama...

where ollama >nul 2>&1
if %errorlevel%==0 (
    REM 检查 ollama 是否已在运行
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if !errorlevel!==0 (
        echo   Ollama 已在运行
    ) else (
        echo   启动 Ollama 服务...
        start /B ollama serve >nul 2>&1
        echo   等待 Ollama 就绪...
        timeout /t 5 /nobreak >nul
    )

    REM 检查模型
    ollama list 2>nul | findstr /C:"%OLLAMA_MODEL%" >nul 2>&1
    if !errorlevel!==0 (
        echo   模型 %OLLAMA_MODEL% 已就绪
    ) else (
        echo   模型 %OLLAMA_MODEL% 未找到，正在拉取...
        ollama pull %OLLAMA_MODEL%
    )
) else (
    echo   未找到 Ollama，请先安装: https://ollama.ai
    echo   你仍然可以使用 Qwen API 模式运行
)

REM --- Step 2: 预热索引 ---
echo.
echo [2/3] 预热向量索引...

cd /d "%SCRIPT_DIR%"
python -c "import json; from rag.indexer import build_index; products = json.load(open('data/products.json', 'r', encoding='utf-8')); print(f'  加载 {len(products)} 条商品数据'); index = build_index(products); print('  向量索引构建完成')"

REM --- Step 3: 启动 Streamlit ---
echo.
echo [3/3] 启动 Streamlit 应用...

start "RAG-Shopping-Agent" /B streamlit run app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   启动成功！
echo ========================================
echo.
echo   浏览器访问: http://localhost:8501
echo.
echo   停止服务:   stop.bat
echo.

REM 保持窗口打开
pause
