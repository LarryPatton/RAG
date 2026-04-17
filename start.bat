@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo   RAG Shopping Agent - Starting...
echo ========================================
echo.

REM --- Step 1: Check Ollama ---
echo [1/4] Checking Ollama...
where ollama >nul 2>&1
if errorlevel 1 (
    echo   Ollama not found. Install from https://ollama.ai
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

REM --- Step 2: Check index cache ---
echo.
echo [2/4] Checking vector index...
python -c "from rag.indexer import index_exists; print('EXISTS' if index_exists() else 'MISSING')" 2>nul | findstr "EXISTS" >nul 2>&1
if errorlevel 1 (
    echo   Building index from 500 products (first time only)...
    python -c "import json; from rag.indexer import build_index; data=json.load(open('data/products.json','r',encoding='utf-8')); build_index(data); print('  Index built.')"
) else (
    echo   Index cache found.
)

REM --- Step 3: Start FastAPI ---
echo.
echo [3/4] Starting FastAPI backend...
start "RAG-FastAPI" uvicorn api.main:app --host 0.0.0.0 --port 8000
timeout /t 3 /nobreak >nul

REM --- Step 4: Start Vite ---
echo.
echo [4/4] Starting React frontend...
cd web
start "RAG-Vite" cmd /c "npm run dev"
cd ..
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   Started successfully!
echo ========================================
echo.
echo   Frontend: http://localhost:5173
echo   API:      http://localhost:8000/docs
echo   Stop:     stop.bat
echo.
pause
