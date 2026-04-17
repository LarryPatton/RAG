@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo   RAG Shopping Agent - Starting...
echo ========================================
echo.

REM --- Step 1: Check Ollama ---
echo [1/3] Checking Ollama...

where ollama >nul 2>&1
if errorlevel 1 (
    echo   Ollama not found. Install from https://ollama.ai
    echo   You can still use Qwen API mode.
    goto :skip_ollama
)

curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo   Starting Ollama...
    start "" ollama serve
    timeout /t 5 /nobreak >nul
) else (
    echo   Ollama is running.
)

ollama list 2>nul | findstr "qwen2.5:14b" >nul 2>&1
if errorlevel 1 (
    echo   Pulling qwen2.5:14b ...
    ollama pull qwen2.5:14b
) else (
    echo   Model qwen2.5:14b ready.
)

:skip_ollama

REM --- Step 2: Build or load index ---
echo.
echo [2/3] Checking vector index...

python -c "from rag.indexer import index_exists; print('EXISTS' if index_exists() else 'MISSING')" 2>nul | findstr "EXISTS" >nul 2>&1
if errorlevel 1 (
    echo   Index not found. Building from 500 products...
    echo   (First time only, takes ~30 seconds)
    python -c "import json; from rag.indexer import build_index; data=json.load(open('data/products.json','r',encoding='utf-8')); print(f'  Loaded {len(data)} products'); build_index(data); print('  Index built and saved to ./qdrant_data/')"
) else (
    echo   Index found on disk. Skipping build.
)

if errorlevel 1 (
    echo   ERROR: Index build failed. Check dependencies.
    pause
    exit /b 1
)

REM --- Step 3: Start Streamlit ---
echo.
echo [3/3] Starting Streamlit...

start "RAG-Agent-Streamlit" streamlit run app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   Started successfully!
echo ========================================
echo.
echo   Open browser: http://localhost:8501
echo   Stop service: stop.bat
echo.
pause
