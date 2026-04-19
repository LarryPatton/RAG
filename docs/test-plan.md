# RAG 智能购物助手 — 自动化测试任务书

> 交付给 AI 工程师的测试规范，覆盖后端单元测试、集成测试和端到端链路验证。

---

## 运行环境

```bash
cd G:\RAG
python -m pytest tests/ -v -x -p no:asyncio
```

- Python 3.14+，依赖见 `requirements.txt`
- 需要 Ollama 运行中（`ollama serve`）且已拉取 `qwen2.5:14b`
- 测试文件统一放在 `tests/` 目录下
- 使用 `pytest`，不需要 `pytest-asyncio`（async 测试用 `asyncio.run()` 包裹）

---

## 测试分层概览

| 层级 | 覆盖范围 | 文件 |
|------|---------|------|
| L1 数据层 | 商品加载、查找、数据完整性 | `tests/test_data.py` |
| L2 工具层 | 4 个工具函数的输入/输出/边界 | `tests/test_tools.py`（扩充） |
| L3 RAG 层 | 索引构建、检索质量、预算硬过滤 | `tests/test_rag.py` |
| L4 解析层 | JSON 解析、阶段提取、决策提取 | `tests/test_parsing.py` |
| L5 Agent 层 | 信息门控、工具调用、完整对话 | `tests/test_agent_flow.py` |
| L6 API 层 | HTTP 接口、SSE 流、错误处理 | `tests/test_api_endpoints.py` |
| L7 端到端 | 完整购物流程（5轮对话 → 下单） | `tests/test_e2e.py` |

---

## L1: 数据层测试 — `tests/test_data.py`

### 测试目标
验证 `data/products.json` 和 `data/loader.py` 的数据完整性和查找功能。

### 测试用例

#### T1.1 商品数量验证
```
加载 products.json，断言总数 == 1500
```

#### T1.2 数据字段完整性
```
遍历所有商品，断言每条都有以下字段且类型正确：
- id: str, 格式 "hp_XXXX"
- name: str, 非空
- category: str
- type: str, 值为 ["入耳式", "头戴式", "骨传导", "耳挂式"] 之一
- brand: str, 非空
- price: int, 范围 50-6000
- platform: str, 值为 ["京东", "天猫", "拼多多"] 之一
- rating: float, 范围 3.8-4.9
- features: list[str], 长度 >= 3
- scenario: list[str], 长度 >= 1
- noise_cancellation: str
- description: str, 非空
- stock: int, 范围 0-100
- other_platform_prices: dict, 恰好 2 个键（另外两个平台）
```

#### T1.3 类型分布均匀性
```
统计四种类型的数量，断言每种至少占 10%（即 >= 150 条）
```

#### T1.4 平台分布均匀性
```
统计三个平台的数量，断言每个平台占比在 28%-40% 之间
```

#### T1.5 find_product 精确匹配
```
from data.loader import find_product
product = find_product("Sony WH-1000XM5 头戴式耳机")
断言 product 不为 None
断言 product["brand"] == "Sony"
```

#### T1.6 find_product 模糊匹配
```
product = find_product("WH-1000XM5")
断言 product 不为 None（4字符以上子串应命中）
```

#### T1.7 find_product 不存在的商品
```
product = find_product("不存在的商品ABC")
断言 product is None
```

---

## L2: 工具层测试 — `tests/test_tools_extended.py`

### 测试目标
验证 4 个 LangChain @tool 函数的输入/输出格式和边界条件。

### 前置：加载真实商品数据
```python
import json
products = json.load(open("data/products.json", "r", encoding="utf-8"))
# 取第一条已知商品用于测试
sample = products[0]
sample_name = sample["name"]
sample_platform = sample["platform"]
```

#### T2.1 compare_prices 正常调用
```
from tools.price_comparison import compare_prices
result = compare_prices.invoke({"product_name": sample_name})
断言 result 是 str
断言 result 包含 "京东" 或 "天猫" 或 "拼多多"
断言 result 包含 "最低价"
```

#### T2.2 compare_prices 商品不存在
```
result = compare_prices.invoke({"product_name": "完全不存在的商品XYZ"})
断言 result 包含 "未找到" 或 result 为空字符串
```

#### T2.3 check_inventory 有货商品
```
from tools.inventory import check_inventory
result = check_inventory.invoke({"product_name": sample_name, "platform": sample_platform})
断言 result 是 str
断言 result 包含 sample_name 的部分内容
断言 result 包含 "件" 或 "缺货" 或 "库存"
```

#### T2.4 check_inventory 跨平台查询
```
other_platform = [p for p in ["京东", "天猫", "拼多多"] if p != sample_platform][0]
result = check_inventory.invoke({"product_name": sample_name, "platform": other_platform})
断言 result 是 str 且非空
```

#### T2.5 place_order 正常下单
```
from tools.order import place_order
result = place_order.invoke({"product_name": sample_name, "platform": "京东", "price": 299.0})
断言 result 包含 "订单号"
断言 result 包含 "JD"（京东平台代码）
断言 result 包含 "明天"
```

#### T2.6 place_order 各平台代码
```
分别测试 platform="京东"/"天猫"/"拼多多"
断言订单号前缀分别为 "JD"/"TM"/"PDD"
```

---

## L3: RAG 层测试 — `tests/test_rag.py`

### 测试目标
验证向量索引构建、检索质量、预算硬过滤。

#### T3.1 索引构建
```
from rag.indexer import build_index
import json
products = json.load(open("data/products.json", "r", encoding="utf-8"))
index = build_index(products)
断言 index 不为 None
```

#### T3.2 product_search 基本检索
```
from rag.query import create_product_search_tool
tool = create_product_search_tool(index)
result = tool.invoke({"query": "降噪耳机 通勤"})
断言 result 包含 "商品1"
断言 result 包含 "降噪" 或 "通勤"
```

#### T3.3 预算硬过滤 — 不返回超预算商品
```
result = tool.invoke({"query": "300以内入耳式降噪耳机"})
# 提取所有价格
import re
prices = [int(p) for p in re.findall(r"价格: ¥(\d+)", result)]
断言 所有价格 <= 300（硬性过滤，不允许任何超预算）
```

#### T3.4 预算硬过滤 — 极低预算
```
result = tool.invoke({"query": "50以内耳机"})
断言 result 不包含 "¥100" 以上的价格，或者返回"未找到"提示
```

#### T3.5 类型过滤
```
result = tool.invoke({"query": "头戴式耳机 500以内"})
# 检查返回结果中类型字段
types = re.findall(r"类型: (\S+)", result)
断言 所有类型 == "头戴式"（至少有 3 条结果时才严格过滤）
```

#### T3.6 骨传导/耳挂式类型识别
```
result = tool.invoke({"query": "骨传导耳机 运动"})
断言 result 包含 "骨传导"

result2 = tool.invoke({"query": "耳挂式开放式耳机"})
断言 result2 包含 "耳挂式"
```

---

## L4: 解析层测试 — `tests/test_parsing.py`

### 测试目标
验证 `agent_service.py` 中的纯函数：JSON 解析、阶段提取、决策提取。

#### T4.1 parse_structured_output — 文字 + quick_replies
```
from api.services.agent_service import parse_structured_output

text = '''[意图澄清] 您的预算是多少？

```json
{"type": "quick_replies", "options": ["200以内", "200-500", "500-1000"]}
```'''

result = parse_structured_output(text)
断言 result["text"].strip() == "[意图澄清] 您的预算是多少？"
断言 result["quick_replies"] == ["200以内", "200-500", "500-1000"]
断言 result["structured_data"] is None
```

#### T4.2 parse_structured_output — recommendation JSON
```
text = '''```json
{"type": "recommendation", "products": [{"rank":1,"name":"test"}], "verdict":"好"}
```

推荐第一款。'''

result = parse_structured_output(text)
断言 result["structured_data"]["type"] == "recommendation"
断言 result["text"].strip() == "推荐第一款。"
```

#### T4.3 parse_structured_output — 纯文本（无 JSON）
```
text = "[意图澄清] 请问您想找什么耳机？"
result = parse_structured_output(text)
断言 result["text"] == text
断言 result["structured_data"] is None
断言 result["quick_replies"] is None
```

#### T4.4 parse_structured_output — 空字符串边界
```
# 关键测试：只有 JSON 没有文字时，clean_text 应该是空字符串
text = '''```json
{"type": "quick_replies", "options": ["A", "B"]}
```'''
result = parse_structured_output(text)
断言 result["text"] == ""  # 这是预期行为
断言 result["quick_replies"] == ["A", "B"]
```

#### T4.5 extract_stage — 各阶段识别
```
from api.services.agent_service import extract_stage

断言 extract_stage("[意图澄清] 你好") == "意图澄清"
断言 extract_stage("[推荐方案] 推荐3款") == "推荐方案"
断言 extract_stage("[分析中] [搜索中] 正在处理") == "搜索中"  # 取最高级
断言 extract_stage("没有标签的回复") == "未知"
```

#### T4.6 extract_stage — structured_data 推断
```
断言 extract_stage("文字", {"type": "recommendation"}) == "推荐方案"
断言 extract_stage("文字", {"type": "order_confirm"}) == "订单确认"
```

#### T4.7 _build_decision_prefix — 决策前缀构建
```
from api.services.agent_service import AgentService
svc = AgentService()

prefix = svc._build_decision_prefix({"type": "头戴式", "budget": "≤¥500"})
断言 "[已确认的用户决策" in prefix
断言 "耳机类型: 头戴式" in prefix
断言 "预算: ≤¥500" in prefix
```

#### T4.8 _build_decision_prefix — 空决策
```
prefix = svc._build_decision_prefix({})
断言 prefix == ""
```

---

## L5: Agent 层测试 — `tests/test_agent_flow.py`

### 测试目标
验证 LangGraph Agent 的信息门控和完整对话流程。需要真实 LLM。

> 注意：这些测试需要 Ollama 运行中，执行时间较长（每个 30-120 秒）。

#### T5.1 信息门控 — 拦截缺少信息的工具调用
```
from agent.graph import extract_confirmed_info
from langchain_core.messages import HumanMessage

messages = [HumanMessage(content="帮我找一款耳机")]
confirmed = extract_confirmed_info(messages)
断言 "budget" not in confirmed
断言 "type" not in confirmed
断言 "scenario" not in confirmed
```

#### T5.2 信息提取 — 从消息中识别已确认信息
```
messages = [
    HumanMessage(content="帮我找一款500以内的入耳式耳机，通勤用"),
]
confirmed = extract_confirmed_info(messages)
断言 "budget" in confirmed
断言 "type" in confirmed
断言 "scenario" in confirmed
```

#### T5.3 信息提取 — 从决策前缀中识别
```
messages = [
    HumanMessage(content="[已确认的用户决策，请勿再次询问以下信息：]\n- 预算: ≤¥500\n- 耳机类型: 入耳式\n- 使用场景: 通勤\n\n好的"),
]
confirmed = extract_confirmed_info(messages)
断言 "budget" in confirmed
断言 "type" in confirmed
断言 "scenario" in confirmed
```

#### T5.4 同步对话 — 意图澄清阶段
```
from api.services.agent_service import agent_service

result = agent_service.chat("帮我找一款耳机", [], "ollama")
断言 result["stage"] == "意图澄清"
断言 len(result["text"]) > 0
断言 result["thinking_steps"] == []  # 不应调用工具
```

#### T5.5 同步对话 — 带完整信息应触发搜索
```
history = [
    {"role": "user", "content": "帮我找一款耳机"},
    {"role": "assistant", "content": "[意图澄清] 预算多少？"},
    {"role": "user", "content": "500以内"},
    {"role": "assistant", "content": "[意图澄清] 什么类型？"},
    {"role": "user", "content": "入耳式"},
    {"role": "assistant", "content": "[意图澄清] 什么场景？"},
    {"role": "user", "content": "通勤"},
    {"role": "assistant", "content": "[意图澄清] 需要降噪吗？"},
    {"role": "user", "content": "需要"},
    {"role": "assistant", "content": "[意图澄清] 品牌偏好？"},
]
decisions = {"type": "入耳式", "budget": "≤¥500", "scenario": "通勤", "noise_cancellation": "需要降噪"}

result = agent_service.chat("没有偏好", history, "ollama", user_decisions=decisions)
# 应该进入搜索/推荐阶段
断言 result["stage"] in ["分析中", "搜索中", "推荐方案"]
断言 len(result["thinking_steps"]) > 0  # 应调用了工具
```

---

## L6: API 层测试 — `tests/test_api_endpoints.py`

### 测试目标
验证 HTTP 接口的请求/响应格式、验证、错误处理。使用 FastAPI TestClient。

#### T6.1 健康检查
```
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)
r = client.get("/api/health")
断言 r.status_code == 200
断言 r.json() == {"status": "ok"}
```

#### T6.2 商品统计
```
r = client.get("/api/products/stats")
断言 r.status_code == 200
data = r.json()
断言 data["total"] == 1500
断言 len(data["brands"]) >= 30
断言 "入耳式" in data["types"]
断言 "骨传导" in data["types"]
```

#### T6.3 商品列表 — 分页
```
r = client.get("/api/products?page=1&limit=10")
断言 r.status_code == 200
data = r.json()
断言 len(data["products"]) == 10
断言 data["total"] == 1500
```

#### T6.4 商品列表 — 类型过滤
```
r = client.get("/api/products?type=骨传导&limit=100")
data = r.json()
断言 所有 product["type"] == "骨传导"
```

#### T6.5 商品列表 — 价格过滤
```
r = client.get("/api/products?max_price=300&limit=100")
data = r.json()
断言 所有 product["price"] <= 300
```

#### T6.6 同步聊天接口
```
r = client.post("/api/chat", json={
    "message": "帮我找一款耳机",
    "history": [],
    "llm_mode": "ollama"
})
断言 r.status_code == 200
data = r.json()
断言 "text" in data
断言 "stage" in data
断言 data["stage"] == "意图澄清"
```

#### T6.7 SSE 流式接口 — 事件格式
```
r = client.post("/api/chat/stream", json={
    "message": "帮我找一款耳机",
    "history": [],
    "llm_mode": "ollama"
}, stream=True)
断言 r.status_code == 200
断言 r.headers["content-type"] 包含 "text/event-stream"

events = []
for line in r.iter_lines():
    if line.startswith("data: "):
        event = json.loads(line[6:])
        events.append(event)

# 验证事件序列
types = [e["type"] for e in events]
断言 "token" in types          # 必须有 token 事件
断言 types[-1] == "done"       # 最后一个必须是 done
断言 "stage" in types          # 必须有 stage 事件

# done 事件必须有 clean_text 字段
done_event = [e for e in events if e["type"] == "done"][0]
断言 "clean_text" in done_event
```

#### T6.8 SSE 流式接口 — 完整搜索流程
```
# 用包含完整信息的对话触发搜索
r = client.post("/api/chat/stream", json={
    "message": "没有偏好",
    "history": [
        {"role": "user", "content": "帮我找500以内入耳式降噪耳机通勤用"},
        {"role": "assistant", "content": "[意图澄清] 需要降噪吗？"},
        {"role": "user", "content": "需要"},
        {"role": "assistant", "content": "[意图澄清] 品牌偏好？"},
    ],
    "llm_mode": "ollama",
    "user_decisions": {"type": "入耳式", "budget": "≤¥500", "scenario": "通勤", "noise_cancellation": "需要降噪"}
}, stream=True)

events = [json.loads(l[6:]) for l in r.iter_lines() if l.startswith("data: ")]
types = [e["type"] for e in events]

断言 "tool_start" in types     # 必须调用了工具
断言 "tool_end" in types
断言 "structured_data" in types # 必须有推荐数据

# 验证 tool 调用顺序
tool_starts = [e["tool"] for e in events if e["type"] == "tool_start"]
断言 "product_search" in tool_starts
# compare_prices 和 check_inventory 可能存在也可能不存在（取决于LLM）

# 验证 structured_data
sd_events = [e for e in events if e["type"] == "structured_data"]
if sd_events:
    sd = sd_events[0]["data"]
    断言 sd["type"] in ["recommendation", "task_plan"]
```

#### T6.9 请求验证 — 消息过长
```
r = client.post("/api/chat", json={
    "message": "x" * 2001,  # 超过 2000 字符限制
    "history": [],
    "llm_mode": "ollama"
})
断言 r.status_code == 422  # Pydantic 验证失败
```

---

## L7: 端到端测试 — `tests/test_e2e.py`

### 测试目标
模拟完整的 5 轮对话购物流程，验证每个阶段的输入/输出契约。

> 使用 agent_service 直接调用（绕过 HTTP），减少网络变量。
> 每个测试预计 2-5 分钟。

#### T7.1 完整购物流程（意图澄清 → 推荐 → 下单）

```python
from api.services.agent_service import agent_service

history = []
decisions = {}

# === 第1轮：用户发起需求 ===
r1 = agent_service.chat("帮我找一款耳机", history, "ollama")
断言 r1["stage"] == "意图澄清"
断言 len(r1["text"]) > 0
断言 r1["thinking_steps"] == []

history += [
    {"role": "user", "content": "帮我找一款耳机"},
    {"role": "assistant", "content": r1["reply"]},
]

# === 第2轮：回答预算 ===
r2 = agent_service.chat("500以内", history, "ollama")
断言 r2["stage"] == "意图澄清"  # 还需要更多信息
history += [
    {"role": "user", "content": "500以内"},
    {"role": "assistant", "content": r2["reply"]},
]
decisions["budget"] = "≤¥500"

# === 第3轮：回答类型 ===
r3 = agent_service.chat("入耳式", history, "ollama", user_decisions=decisions)
断言 r3["stage"] == "意图澄清"
history += [
    {"role": "user", "content": "入耳式"},
    {"role": "assistant", "content": r3["reply"]},
]
decisions["type"] = "入耳式"

# === 第4轮：回答场景 ===
r4 = agent_service.chat("通勤", history, "ollama", user_decisions=decisions)
断言 r4["stage"] == "意图澄清"  # 还要问降噪和品牌
history += [
    {"role": "user", "content": "通勤"},
    {"role": "assistant", "content": r4["reply"]},
]
decisions["scenario"] = "通勤"

# === 第5轮：回答降噪 ===
r5 = agent_service.chat("需要降噪", history, "ollama", user_decisions=decisions)
断言 r5["stage"] == "意图澄清"  # 还要问品牌
history += [
    {"role": "user", "content": "需要降噪"},
    {"role": "assistant", "content": r5["reply"]},
]
decisions["noise_cancellation"] = "需要降噪"

# === 第6轮：回答品牌 → 应触发搜索和推荐 ===
r6 = agent_service.chat("没有偏好", history, "ollama", user_decisions=decisions)
断言 r6["stage"] in ["分析中", "搜索中", "推荐方案"]
断言 len(r6["thinking_steps"]) > 0  # 调用了工具

# 如果是推荐阶段，验证推荐数据
if r6["structured_data"] and r6["structured_data"].get("type") == "recommendation":
    sd = r6["structured_data"]
    断言 len(sd["products"]) == 3  # 必须恰好 3 款
    for p in sd["products"]:
        断言 p["price"] <= 500  # 不超预算
        断言 "name" in p
        断言 "platform" in p

    # === 第7轮：选择商品 ===
    chosen = sd["products"][0]
    history += [
        {"role": "user", "content": "没有偏好"},
        {"role": "assistant", "content": r6["reply"]},
    ]
    decisions["brand_preference"] = "无偏好"

    r7 = agent_service.chat(
        f"我选择 {chosen['name']}，帮我下单{chosen['platform']}的",
        history, "ollama", user_decisions=decisions
    )
    断言 r7["stage"] == "订单确认"
    断言 r7["structured_data"]["type"] == "order_confirm"
    断言 r7["structured_data"]["price"] == chosen["price"]  # 价格一致

    # === 第8轮：确认下单 ===
    history += [
        {"role": "user", "content": f"我选择 {chosen['name']}"},
        {"role": "assistant", "content": r7["reply"]},
    ]

    r8 = agent_service.chat("确认下单", history, "ollama", user_decisions=decisions)
    断言 r8["stage"] == "下单完成"
    断言 "订单号" in r8["text"]
```

#### T7.2 中途改需求

```
# 走到推荐阶段后，用户说"预算放宽到1000"
# 验证 agent 重新搜索而非从头开始
# 验证新推荐的价格在新预算范围内
```

#### T7.3 流式对话完整性

```python
import asyncio
from api.services.agent_service import agent_service

async def test_stream_flow():
    events = []
    async for event in agent_service.stream_chat("帮我找一款500以内的入耳式降噪耳机通勤用", [], "ollama"):
        events.append(event)

    types = [e["type"] for e in events]

    # 基本事件完整性
    断言 "token" in types
    断言 "stage" in types
    断言 "done" in types
    断言 types[-1] == "done"  # done 必须是最后一个

    # done 事件的 clean_text 不应为空（如果有 token 输出）
    token_content = "".join(e["content"] for e in events if e["type"] == "token")
    done_event = [e for e in events if e["type"] == "done"][0]
    if len(token_content) > 0:
        断言 len(done_event.get("clean_text", "")) > 0 or len(token_content) > 0

asyncio.run(test_stream_flow())
```

---

## L8: 多步交互合理性测试 — `tests/test_interaction_quality.py`

### 测试目标
验证多轮对话中**每一步返回内容的语义合理性**，确保 AI 没有答非所问、漏掉信息、重复提问、提前搜索。

> 使用 `agent_service.chat()` 逐轮调用，每步都做内容合理性断言。
> 这些测试不检查具体措辞，而是检查回复是否**语义相关、结构完整、阶段正确**。

### 场景 A：标准 5 轮澄清流程

```python
from api.services.agent_service import agent_service
import re

history = []
decisions = {}

# ── 第1轮：模糊需求 ──
r1 = agent_service.chat("我想买个耳机", history, "ollama")

# 合理性验证：
断言 r1["stage"] == "意图澄清"
断言 r1["thinking_steps"] == []              # 不应调用任何工具
断言 len(r1["text"]) > 5                     # 不能是空回复
断言 r1["text"] 不包含 "推荐" 和 "下单"        # 不应跳阶段
# 应该在问预算（第一优先级）
断言 r1["text"] 包含 "预算" 或 "价格" 或 "多少钱" 或 "价位" 之一
# 不应同时问两个问题
问题标记 = ["预算", "类型", "场景", "降噪", "品牌"]
命中数 = sum(1 for kw in 问题标记 if kw in r1["text"])
断言 命中数 <= 2  # 最多涉及1-2个关键词，不是同时问所有

history += [{"role":"user","content":"我想买个耳机"}, {"role":"assistant","content":r1["reply"]}]

# ── 第2轮：回答预算 ──
r2 = agent_service.chat("500以内", history, "ollama")

断言 r2["stage"] == "意图澄清"
断言 r2["thinking_steps"] == []
# 不应重复问预算
断言 r2["text"] 不包含 "预算"
# 应该在问下一个维度（类型或场景）
断言 r2["text"] 包含 "类型" 或 "入耳" 或 "头戴" 或 "场景" 或 "用途" 之一

history += [{"role":"user","content":"500以内"}, {"role":"assistant","content":r2["reply"]}]
decisions["budget"] = "≤¥500"

# ── 第3轮：回答类型 ──
r3 = agent_service.chat("入耳式", history, "ollama", user_decisions=decisions)

断言 r3["stage"] == "意图澄清"
断言 r3["thinking_steps"] == []
# 不应重复问预算或类型
断言 r3["text"] 不包含 "预算"
断言 r3["text"] 不包含 "入耳式还是"  # 不应反问已确认的类型
# 应继续问下一个维度
断言 r3["text"] 包含 "场景" 或 "用途" 或 "通勤" 或 "运动" 或 "办公" 或 "降噪" 或 "品牌" 之一

history += [{"role":"user","content":"入耳式"}, {"role":"assistant","content":r3["reply"]}]
decisions["type"] = "入耳式"

# ── 第4轮：回答场景 ──
r4 = agent_service.chat("通勤", history, "ollama", user_decisions=decisions)

断言 r4["stage"] == "意图澄清"
断言 r4["thinking_steps"] == []
# 三个核心维度齐了但不应提前搜索（还需问降噪和品牌）
断言 r4["text"] 不包含 "搜索" 和 "推荐"
# 应问降噪或品牌
断言 r4["text"] 包含 "降噪" 或 "品牌" 或 "牌子" 之一

history += [{"role":"user","content":"通勤"}, {"role":"assistant","content":r4["reply"]}]
decisions["scenario"] = "通勤"

# ── 第5轮：回答降噪 ──
r5 = agent_service.chat("需要降噪", history, "ollama", user_decisions=decisions)

断言 r5["stage"] == "意图澄清"
断言 r5["thinking_steps"] == []
# 应该在问最后一个维度：品牌
断言 r5["text"] 包含 "品牌" 或 "牌子" 或 "偏好" 之一
# 不应重复问已确认的信息
断言 r5["text"] 不包含 "降噪" 的提问句式（如 "是否需要降噪"）

history += [{"role":"user","content":"需要降噪"}, {"role":"assistant","content":r5["reply"]}]
decisions["noise_cancellation"] = "需要降噪"

# ── 第6轮：回答品牌 → 应触发搜索 ──
r6 = agent_service.chat("没有偏好", history, "ollama", user_decisions=decisions)

# 5个维度全部回答，必须进入搜索/推荐
断言 r6["stage"] in ["分析中", "搜索中", "推荐方案"]
断言 len(r6["thinking_steps"]) > 0             # 必须调用了工具
断言 r6["stage"] != "意图澄清"                  # 绝不能还在澄清
```

### 场景 B：用户一次性给出多个信息

```python
# 用户第一句话就包含多个信息
r = agent_service.chat("帮我找一款500以内的入耳式降噪耳机，通勤用", [], "ollama")

断言 r["stage"] == "意图澄清"
# 预算、类型、场景、降噪都给了，应该只问品牌
断言 r["text"] 不包含 "预算"
断言 r["text"] 不包含 "类型" 或 "入耳还是头戴"
断言 r["thinking_steps"] == []  # 还缺品牌，不应搜索
```

### 场景 C：多选回答的合理处理

```python
history = [
    {"role":"user","content":"帮我找一款耳机"},
    {"role":"assistant","content":"[意图澄清] 您的预算大概是多少？"},
    {"role":"user","content":"500-1000"},
    {"role":"assistant","content":"[意图澄清] 您想要什么类型的耳机？"},
]

r = agent_service.chat("头戴式 + 入耳式", history, "ollama",
    user_decisions={"budget": "¥500-1000"})

断言 r["stage"] == "意图澄清"
# 不应忽略多选，不应只提及其中一种
# 不应重复问类型
断言 r["text"] 不包含 "类型" 或 "入耳还是头戴"
# 应继续问下一个维度
断言 r["text"] 包含 "场景" 或 "降噪" 或 "品牌" 之一
```

### 场景 D：推荐结果的合理性验证

```python
# 直接构造一个完整信息的对话，触发推荐
history = [
    {"role":"user","content":"帮我找500以内入耳式降噪耳机通勤用"},
    {"role":"assistant","content":"[意图澄清] 品牌有偏好吗？"},
    {"role":"user","content":"国产优先"},
    {"role":"assistant","content":"[意图澄清] 需要降噪功能吗？"},
    {"role":"user","content":"需要"},
]
decisions = {"budget":"≤¥500","type":"入耳式","scenario":"通勤","brand_preference":"国产优先","noise_cancellation":"需要降噪"}

r = agent_service.chat("开始搜索吧", history, "ollama", user_decisions=decisions)

# 如果进入推荐阶段
if r["structured_data"] and r["structured_data"].get("type") == "recommendation":
    sd = r["structured_data"]

    # --- 数量验证 ---
    断言 len(sd["products"]) == 3

    # --- 价格合理性 ---
    for p in sd["products"]:
        断言 p["price"] <= 500            # 不超预算
        断言 p["price"] > 0               # 价格为正
        断言 type(p["price"]) == int      # 价格是整数

    # --- 排名合理性 ---
    ranks = [p["rank"] for p in sd["products"]]
    断言 ranks == [1, 2, 3]               # 排名连续

    # --- 字段完整性 ---
    for p in sd["products"]:
        断言 p.get("name") 非空
        断言 p.get("brand") 非空
        断言 p.get("platform") in ["京东", "天猫", "拼多多"]
        断言 p.get("rating") 在 1.0-5.0 之间
        断言 len(p.get("pros", [])) >= 1   # 至少1个优点
        断言 len(p.get("cons", [])) >= 1   # 至少1个缺点
        断言 p.get("reason") 非空          # 推荐理由不为空

    # --- decision_process 合理性 ---
    dp = sd.get("decision_process", {})
    断言 dp.get("total_products", 0) > 0
    断言 dp.get("retrieved", 0) > 0
    断言 dp.get("final_candidates") == 3
    断言 dp.get("primary_criterion") 非空

    # --- user_profile 回显正确性 ---
    up = sd.get("user_profile", {})
    断言 "500" in str(up.get("budget", ""))   # 预算回显
    断言 "入耳" in str(up.get("type", ""))    # 类型回显

    # --- verdict 合理性 ---
    断言 sd.get("verdict") 非空
    断言 len(sd["verdict"]) >= 10             # verdict 不能太短

    # --- comparisons 合理性 ---
    if sd.get("comparisons"):
        for key, values in sd["comparisons"].items():
            断言 len(values) == 3             # 每个维度3个值（对应3个商品）
```

### 场景 E：订单确认的合理性验证

```python
# 承接场景 D 的推荐结果
if r["structured_data"] and r["structured_data"].get("type") == "recommendation":
    chosen = sd["products"][0]
    history_full = history + [
        {"role":"user","content":"开始搜索吧"},
        {"role":"assistant","content": r["reply"]},
    ]

    r_order = agent_service.chat(
        f"我选择 {chosen['name']}，帮我下单{chosen['platform']}的",
        history_full, "ollama", user_decisions=decisions
    )

    # --- 阶段验证 ---
    断言 r_order["stage"] == "订单确认"
    断言 r_order["structured_data"]["type"] == "order_confirm"

    oc = r_order["structured_data"]

    # --- 订单信息一致性 ---
    断言 oc["product"] == chosen["name"]       # 商品名一致
    断言 oc["price"] == chosen["price"]         # 价格一致（缓存覆盖）
    断言 oc["platform"] == chosen["platform"]   # 平台一致

    # --- price_comparison 格式 ---
    if oc.get("price_comparison"):
        pc = oc["price_comparison"]
        断言 len(pc) >= 2                       # 至少2个平台
        for platform, price in pc.items():
            断言 type(price) == int             # 价格必须是整数
            断言 price > 0
            断言 platform in ["京东", "天猫", "拼多多"]

    # --- delivery 字段 ---
    断言 oc.get("delivery") 非空

    # --- 不应在此轮调用 place_order ---
    tool_names = [s["tool"] for s in r_order.get("thinking_steps", [])]
    断言 "place_order" not in tool_names        # 确认前不能下单
```

### 场景 F：下单完成的合理性验证

```python
    # 承接场景 E
    history_order = history_full + [
        {"role":"user","content":f"我选择 {chosen['name']}"},
        {"role":"assistant","content": r_order["reply"]},
    ]

    r_done = agent_service.chat("确认下单", history_order, "ollama", user_decisions=decisions)

    # --- 阶段验证 ---
    断言 r_done["stage"] == "下单完成"

    # --- 工具调用验证 ---
    tool_names = [s["tool"] for s in r_done.get("thinking_steps", [])]
    断言 "place_order" in tool_names            # 必须调用了 place_order

    # --- 回复内容验证 ---
    断言 "订单号" in r_done["text"]              # 必须包含订单号
    断言 chosen["name"][:4] in r_done["text"] or "成功" in r_done["text"]  # 提及商品或成功
```

### 场景 G：不合理输入的容错

```python
# 用户输入无关内容
r = agent_service.chat("今天天气怎么样", [], "ollama")
断言 r["stage"] == "意图澄清"
断言 r["thinking_steps"] == []    # 不应调用工具
断言 len(r["text"]) > 0           # 应有回复（引导回购物话题）

# 用户输入空有效内容
r2 = agent_service.chat("???", [], "ollama")
断言 r2["stage"] == "意图澄清"
断言 len(r2["text"]) > 0
```

### 场景 H：中途改需求后推荐内容更新

```python
# 先走到推荐阶段（500以内入耳式）
# ... (前6轮同场景A) ...

# 假设 r6 已经返回推荐结果
if r6["structured_data"] and r6["structured_data"].get("type") == "recommendation":
    old_products = r6["structured_data"]["products"]
    old_max_price = max(p["price"] for p in old_products)
    断言 old_max_price <= 500

    # 用户改需求
    history_change = history + [
        {"role":"user","content":"没有偏好"},
        {"role":"assistant","content": r6["reply"]},
    ]

    r_change = agent_service.chat("预算放宽到1000", history_change, "ollama", user_decisions=decisions)

    # 应重新搜索
    断言 len(r_change["thinking_steps"]) > 0
    # 回复应提及需求变化
    断言 r_change["text"] 包含 "1000" 或 "预算" 或 "调整" 之一

    # 如果返回了新推荐
    if r_change["structured_data"] and r_change["structured_data"].get("type") == "recommendation":
        new_products = r_change["structured_data"]["products"]
        new_max_price = max(p["price"] for p in new_products)
        断言 new_max_price <= 1000  # 新预算范围内
```

---

## 关键验证点清单

以下是从已知 bug 中提炼的重点检查项，**必须全部通过**：

| # | 验证点 | 出处 |
|---|--------|------|
| V1 | 预算硬过滤：搜索结果中不允许出现超预算商品 | `rag/query.py` |
| V2 | 类型识别支持骨传导和耳挂式 | `rag/query.py:_extract_type` |
| V3 | `parse_structured_output` 只有 JSON 没有文字时 `text` 为空字符串 | `agent_service.py` |
| V4 | SSE 流 `done` 事件始终包含 `clean_text` 字段 | `chat.py` |
| V5 | SSE 流异常时发送 `error` 事件后仍发送 `done` 事件 | `chat.py:finally` |
| V6 | `order_confirm` 的价格从缓存覆盖，不信任 LLM 输出 | `agent_service.py` |
| V7 | 五个需求维度全部询问后才触发搜索 | `prompts.py` |
| V8 | 推荐必须恰好 3 款商品 | `prompts.py` |
| V9 | `price_comparison` 字段值必须是整数 | `prompts.py` |
| V10 | 商品数据 1500 条，四种类型各占 ≥10% | `products.json` |
| V11 | 每步只问一个问题，不同时追问多个维度 | `prompts.py` |
| V12 | 不重复提问用户已回答的信息 | `prompts.py` |
| V13 | 推荐结果字段完整（rank/name/price/pros/cons/reason） | `prompts.py` |
| V14 | 订单确认不调用 place_order，确认后才调用 | `prompts.py` |
| V15 | 中途改需求后重新搜索且结果在新预算范围内 | 端到端 |

---

## 执行优先级

1. **先跑 L1 + L2 + L4**（纯函数，秒级，无外部依赖）
2. **再跑 L3**（需要构建索引，约 30 秒初始化）
3. **再跑 L6**（需要 FastAPI TestClient + Ollama）
4. **再跑 L5 + L7**（需要真实 LLM 推理，每轮 30-120 秒）
5. **最后跑 L8**（多步交互合理性，最慢，每场景 3-10 分钟）
3. **再跑 L6**（需要 FastAPI TestClient + Ollama）
4. **最后跑 L5 + L7**（需要真实 LLM 推理，每轮 30-120 秒）
