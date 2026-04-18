@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo   RAG Shopping Agent - Starting...
echo ========================================
echo.

REM --- Step 1: Check Ollama ---
echo [1/5] Checking Ollama...
where ollama >nul 2>&1
if errorlevel 1 (
    echo   Ollama not found. Skipping.
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
echo [2/5] Checking vector index...
if exist "%~dp0index_cache\embeddings.npz" (
    echo   Index cache found.
) else (
    echo   Building index from 500 products ^(first time only^)...
    python -c "import json; from rag.indexer import build_index; data=json.load(open('data/products.json','r',encoding='utf-8')); build_index(data); print('  Index built.')"
)

REM --- Step 3: Start FastAPI ---
echo.
echo [3/5] Starting FastAPI backend on port 8000...
call :kill_port 8000
start "RAG-FastAPI" /D "%~dp0" cmd /k "python -m uvicorn api.main:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul

REM --- Step 4: Check npm dependencies ---
echo.
echo [4/5] Checking npm dependencies...
if not exist "%~dp0web\node_modules" (
    echo   Installing npm packages...
    cd /d "%~dp0web" && npm install
    cd /d "%~dp0"
) else (
    echo   node_modules found.
)

REM --- Step 5: Start Vite ---
echo.
echo [5/5] Starting React frontend on port 5173...
call :kill_port 5173
start "RAG-Vite" /D "%~dp0web" cmd /k "npm run dev"
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
goto :eof

REM ============================================
REM  Kill all processes occupying a given port
REM  Usage: call :kill_port <port>
REM ============================================
:kill_port
set "_port=%~1"
set "_killed=0"
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":%_port% " ^| findstr "LISTENING"') do (
    if not "%%p"=="0" (
        echo   Port %_port% occupied by PID %%p, killing...
        taskkill /F /PID %%p >nul 2>&1
        set "_killed=1"
    )
)
if "%_killed%"=="1" (
    echo   Waiting for port %_port% to be released...
    timeout /t 2 /nobreak >nul
)
goto :eof
