# RAG 智能购物助手

基于 **LangGraph + LlamaIndex + Qdrant** 的 AI 购物助手 Demo，用于学术/课堂演示 RAG + Agent + Tools 的协作原理。

## 效果展示

用户用自然语言描述购物需求 → AI 多轮对话理解意图 → 语义检索商品库 → 对比推荐 → 确认下单。

```
👤 帮我找一款500以内的降噪耳机，主要通勤用
🤖 入耳式还是头戴式？有品牌偏好吗？
👤 入耳式，国产品牌优先
🤖 为你推荐3款：
   | 商品名称              | 价格  | 评分 | 核心特点         |
   | 小米 Redmi Buds 5 Pro | ¥299  | 4.4  | 52dB降噪、LDAC  |
   | 华为 FreeBuds 5i      | ¥449  | 4.5  | 主动降噪、多设备 |
   | 漫步者 NeoBuds Pro 2   | ¥499  | 4.6  | 50dB降噪、Hi-Res|
👤 第一款不错，帮我下单
🤖 下单成功！订单号：拼多多20260417-7823
```

## 技术架构

```
用户界面 (Streamlit)
       │
  AI Agent (LangGraph + Qwen 大模型)
       │
  ┌────┴────┐
  │         │
RAG 检索   业务工具
(LlamaIndex (Mock 下单)
+ Qdrant)
```

| 层级 | 技术 | 作用 |
|------|------|------|
| 大模型 | Qwen 2.5 (14B) / Qwen API | 理解意图、生成回复、自主决策 |
| Agent | LangGraph | 编排决策流程、调用工具 |
| 检索 | LlamaIndex + Qdrant | 500条商品的语义检索 |
| Embedding | BGE-small-zh | 中文向量化（本地免费） |
| 前端 | Streamlit | 聊天界面 + 推理日志侧边栏 |

## 快速开始

### 环境要求

- Python 3.10+
- [Ollama](https://ollama.ai)（本地模式）或 Qwen API Key（云端模式）

### 安装

```bash
git clone https://github.com/LarryPatton/RAG.git
cd RAG
pip install -r requirements.txt
```

### 运行

**Windows 一键启动：**

```bash
start.bat          # 启动（自动检查 Ollama、构建索引、启动 Streamlit）
stop.bat           # 停止（释放内存）
```

**手动启动：**

```bash
# 1. 启动 Ollama 并拉取模型
ollama pull qwen2.5:14b

# 2. 启动应用
streamlit run app.py
```

浏览器访问 http://localhost:8501

### 切换大模型

侧边栏可一键切换：

| 模式 | 适用场景 | 配置 |
|------|---------|------|
| Ollama (本地) | 开发测试 | 需 16GB+ 显存 |
| Qwen API (云端) | 正式演示 | 设置 `DASHSCOPE_API_KEY` 环境变量 |

## 项目结构

```
RAG/
├── app.py                  # Streamlit 入口
├── config.py               # LLM 配置（Ollama/API 切换）
├── start.bat / stop.bat    # Windows 一键启停
├── agent/
│   ├── graph.py            # LangGraph Agent 定义
│   └── prompts.py          # System Prompt
├── rag/
│   ├── indexer.py          # 向量索引构建（含缓存）
│   ├── query.py            # 商品检索工具
│   └── compat.py           # Python 3.14 兼容补丁
├── tools/
│   └── order.py            # Mock 下单工具
├── data/
│   └── products.json       # 500条商品数据
├── scripts/
│   └── generate_products.py # 商品数据生成脚本
├── tests/                  # 单元测试（9个）
├── docs/
│   ├── architecture-brief.md  # 技术架构（产品经理版）
│   └── user-flow.md           # 完整用户交互流程
└── index_cache/            # 向量索引缓存（自动生成）
```

## 商品数据

500 条耳机商品，覆盖 32 个品牌、¥50-5570 价格区间。

如需重新生成：

```bash
python scripts/generate_products.py    # 生成 data/products.json
rm -rf index_cache                     # 删除旧缓存，下次启动自动重建
```

## 测试

```bash
python -m pytest tests/ -v -p no:asyncio
```

## 文档

- [技术架构说明（产品经理版）](docs/architecture-brief.md)
- [完整用户交互流程](docs/user-flow.md)
