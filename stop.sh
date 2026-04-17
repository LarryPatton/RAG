#!/bin/bash
# ============================================
# RAG Shopping Agent - 一键停止脚本
# ============================================
# 停止 Streamlit 和 Ollama（如果由 start.sh 启动）
# 释放内存和显存
# ============================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/.pids"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${RED}========================================${NC}"
echo -e "${RED}  RAG 购物助手 - 停止中...${NC}"
echo -e "${RED}========================================${NC}"

# --- 1. 停止 Streamlit ---
echo ""
echo -e "${YELLOW}[1/3] 停止 Streamlit...${NC}"

# 通过 PID 文件停止
if [ -f "$PID_FILE" ]; then
    while IFS= read -r line; do
        name="${line%%:*}"
        pid="${line##*:}"
        if [ "$name" = "streamlit" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            echo "  已停止 Streamlit (PID: $pid)"
        fi
    done < "$PID_FILE"
fi

# 兜底：杀掉所有 streamlit 进程
if pgrep -f "streamlit run" > /dev/null 2>&1; then
    pkill -f "streamlit run" 2>/dev/null
    echo "  已清理残留 Streamlit 进程"
else
    echo "  Streamlit 未在运行"
fi

# --- 2. 停止 Ollama（仅停止由 start.sh 启动的） ---
echo ""
echo -e "${YELLOW}[2/3] 停止 Ollama...${NC}"

if [ -f "$PID_FILE" ]; then
    while IFS= read -r line; do
        name="${line%%:*}"
        pid="${line##*:}"
        if [ "$name" = "ollama" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            echo "  已停止 Ollama 服务 (PID: $pid)"
            echo -e "  ${GREEN}显存已释放${NC}"
        fi
    done < "$PID_FILE"
else
    echo "  Ollama 非由 start.sh 启动，保持运行"
    echo -e "  ${YELLOW}如需手动停止: ollama stop${NC}"
fi

# --- 3. 清理 Python 缓存进程 ---
echo ""
echo -e "${YELLOW}[3/3] 清理 Python 缓存进程...${NC}"

# 清理可能残留的 Python 子进程（embedding model 等）
if pgrep -f "from rag.indexer" > /dev/null 2>&1; then
    pkill -f "from rag.indexer" 2>/dev/null
    echo "  已清理残留索引进程"
fi

# 清理 PID 文件
rm -f "$PID_FILE"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  已停止所有服务，资源已释放${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  重新启动: ${YELLOW}./start.sh${NC}"
echo ""
