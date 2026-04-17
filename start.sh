#!/bin/bash
# ============================================
# RAG Shopping Agent - 一键启动脚本
# ============================================
# 用法:
#   启动: ./start.sh
#   停止: ./stop.sh
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/.pids"
OLLAMA_MODEL="qwen2.5:14b"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  RAG 购物助手 - 启动中...${NC}"
echo -e "${GREEN}========================================${NC}"

# 清理旧 PID 文件
> "$PID_FILE"

# --- Step 1: 检查并启动 Ollama ---
echo ""
echo -e "${YELLOW}[1/3] 检查 Ollama...${NC}"

if command -v ollama &> /dev/null; then
    # 检查 ollama 是否已经在运行
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "  Ollama 已在运行"
    else
        echo "  启动 Ollama 服务..."
        ollama serve > /dev/null 2>&1 &
        OLLAMA_PID=$!
        echo "ollama:$OLLAMA_PID" >> "$PID_FILE"
        echo "  等待 Ollama 就绪..."
        for i in {1..30}; do
            if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done
    fi

    # 检查模型是否已下载
    if ollama list 2>/dev/null | grep -q "$OLLAMA_MODEL"; then
        echo "  模型 $OLLAMA_MODEL 已就绪"
    else
        echo -e "  ${YELLOW}模型 $OLLAMA_MODEL 未找到，正在拉取（首次可能需要几分钟）...${NC}"
        ollama pull "$OLLAMA_MODEL"
    fi
else
    echo -e "  ${RED}未找到 Ollama，请先安装: https://ollama.ai${NC}"
    echo -e "  ${YELLOW}你仍然可以使用 Qwen API 模式运行${NC}"
fi

# --- Step 2: 构建向量索引（预热） ---
echo ""
echo -e "${YELLOW}[2/3] 预热向量索引（首次启动需下载 embedding 模型 ~100MB）...${NC}"

cd "$SCRIPT_DIR"
python -c "
import json, sys
from rag.indexer import build_index
with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)
print(f'  加载 {len(products)} 条商品数据')
index = build_index(products)
print('  向量索引构建完成')
" 2>&1 | grep -v "UserWarning"

# --- Step 3: 启动 Streamlit ---
echo ""
echo -e "${YELLOW}[3/3] 启动 Streamlit 应用...${NC}"

streamlit run app.py \
    --server.headless true \
    --server.port 8501 \
    --browser.gatherUsageStats false \
    > /dev/null 2>&1 &
STREAMLIT_PID=$!
echo "streamlit:$STREAMLIT_PID" >> "$PID_FILE"

# 等待 Streamlit 就绪
sleep 3

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  启动成功！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  浏览器访问: ${GREEN}http://localhost:8501${NC}"
echo ""
echo -e "  停止服务:   ${YELLOW}./stop.sh${NC}"
echo ""
