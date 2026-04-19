# AI 自动化测试执行提示词

你是一名 AI 测试工程师，负责为 RAG 智能购物助手项目编写并执行自动化测试。

## 项目信息

- **项目路径**: `G:\RAG`
- **语言**: Python 3.14 + React 18
- **测试框架**: pytest
- **运行命令**: `cd G:\RAG && python -m pytest tests/ -v -x`
- **LLM**: Ollama 本地运行 qwen2.5:14b（需要 `ollama serve` 已启动）

## 你的任务

1. 阅读测试计划文档 `docs/test-plan.md`，理解每个测试用例的意图和断言条件
2. 按照文档中的 7 个层级（L1-L7），**逐层编写测试代码并执行**
3. 每完成一层，运行该层测试，修复发现的 bug，确认全部通过后再进入下一层
4. 最终输出一份测试报告

## 执行顺序（严格按此顺序）

### 第一批：纯函数测试（无 LLM 依赖，秒级完成）

1. **L1 数据层** → 写入 `tests/test_data.py`
   - 验证 products.json 的 1500 条数据完整性、字段类型、分布均匀性
   - 验证 `data/loader.py` 的 find_product 精确/模糊/不存在三种情况

2. **L2 工具层** → 写入 `tests/test_tools_extended.py`
   - 测试 compare_prices、check_inventory、place_order 的正常和异常输入
   - 注意：工具函数是 LangChain @tool，调用方式为 `tool.invoke({"param": value})`

3. **L4 解析层** → 写入 `tests/test_parsing.py`
   - 测试 `parse_structured_output`、`extract_stage`、`_build_decision_prefix`
   - **关键**：验证只有 JSON 没有文字时 clean_text 为空字符串（这是已知边界case）

### 第二批：RAG 检索测试（需要构建索引，约 30 秒初始化）

4. **L3 RAG 层** → 写入 `tests/test_rag.py`
   - 构建索引后测试检索质量
   - **关键**：验证预算硬过滤（搜索结果中绝不能出现超预算商品）
   - **关键**：验证骨传导、耳挂式的类型识别

### 第三批：API 和集成测试（需要 Ollama）

5. **L6 API 层** → 写入 `tests/test_api_endpoints.py`
   - 使用 `from fastapi.testclient import TestClient` + `from api.main import app`
   - 测试 `/api/health`、`/api/products`、`/api/chat`、`/api/chat/stream`
   - **关键**：SSE 流的事件格式和顺序验证

6. **L5 Agent 层** → 写入 `tests/test_agent_flow.py`
   - 测试信息门控（extract_confirmed_info）
   - 测试同步对话的阶段流转

7. **L7 端到端** → 写入 `tests/test_e2e.py`
   - 模拟完整 5-8 轮对话购物流程
   - 这个最慢（每轮 30-120 秒），放在最后

### 第四批：多步交互合理性测试（最慢，每场景 3-10 分钟）

8. **L8 交互合理性** → 写入 `tests/test_interaction_quality.py`
   - 这是最重要的测试层，验证每一步回复的**语义合理性**
   - 8 个场景（A-H），每个场景是一个完整的多轮对话
   - **不检查具体措辞，检查语义**：用关键词包含/不包含来断言
   - 关键检查项：
     - 每步只问一个问题，不同时追问多个维度
     - 不重复提问用户已经回答过的信息
     - 按正确顺序推进阶段（意图澄清 → 分析中 → 搜索中 → 推荐方案 → 订单确认 → 下单完成）
     - 5 个维度全部问完前不提前搜索
     - 推荐结果的每个字段都完整且合理（rank连续、价格不超预算、pros/cons非空）
     - 订单确认阶段不调用 place_order，确认后才调用
     - 中途改需求后重新搜索，新结果在新预算范围内
     - 不合理输入（闲聊、乱码）不会崩溃，能引导回购物话题

## 重要规则

- **Windows 环境**：路径用正斜杠或 `os.path.join`，终端编码可能是 GBK，打印中文时注意
- **Python 3.14**：会有 Pydantic V1 兼容警告，忽略即可
- **索引缓存**：`index_cache/` 目录可能不存在（已被删除），首次 `build_index` 会重建
- **LLM 测试不确定性**：涉及 LLM 的测试（L5-L8），断言应检查语义而非具体措辞——用关键词包含/不包含来验证，不要断言完整句子。例如断言 `"预算" in text` 而非 `text == "请问您的预算是多少？"`
- **测试隔离**：每个测试文件应能独立运行（`python -m pytest tests/test_xxx.py -v`）
- **发现 bug 时**：先记录问题，尝试修复代码，重跑测试确认修复，然后继续下一个测试
- **不要修改 `docs/test-plan.md`**：这是参考文档，只读

## 关键验证点（必须全部覆盖）

这 15 个验证点来自历史 bug 和交互质量要求，优先级最高：

| # | 验证点 | 对应文件 |
|---|--------|---------|
| V1 | 预算硬过滤：搜索结果不允许超预算商品 | `rag/query.py` |
| V2 | 类型识别支持骨传导和耳挂式 | `rag/query.py` |
| V3 | parse_structured_output 只有 JSON 时 text 为空 | `api/services/agent_service.py` |
| V4 | SSE done 事件包含 clean_text 字段 | `api/routes/chat.py` |
| V5 | SSE 异常后仍发送 done 事件 | `api/routes/chat.py` |
| V6 | order_confirm 价格从缓存覆盖 | `api/services/agent_service.py` |
| V7 | 五个需求维度全部询问后才搜索 | `agent/prompts.py` |
| V8 | 推荐恰好 3 款商品 | `agent/prompts.py` |
| V9 | price_comparison 字段值是整数 | `agent/prompts.py` |
| V10 | 商品 1500 条，四种类型各 ≥10% | `data/products.json` |
| V11 | 每步只问一个问题，不同时追问多个维度 | L8 场景 A |
| V12 | 不重复提问用户已回答的信息 | L8 场景 A |
| V13 | 推荐结果字段完整（rank/name/price/pros/cons/reason） | L8 场景 D |
| V14 | 订单确认不调用 place_order，确认后才调用 | L8 场景 E/F |
| V15 | 中途改需求后重新搜索且结果在新预算范围内 | L8 场景 H |

## 输出要求

每完成一层测试后，输出：
```
✅ L1 数据层：7/7 通过
  - test_product_count: PASS
  - test_field_completeness: PASS
  - ...
```

如果发现需要修复的代码 bug，输出：
```
🐛 发现问题: [描述]
📁 修复文件: [文件路径]
🔧 修复内容: [改了什么]
✅ 修复后重跑: PASS
```

全部完成后，输出完整测试报告摘要。
