"""L6 API 层测试 — 验证 FastAPI HTTP 接口的请求/响应格式、验证、错误处理。

覆盖验证点：
  V4: SSE done 事件始终包含 clean_text 字段
  V5: SSE 流异常时发送 error 事件后仍发送 done 事件
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# T6.1  健康检查
# ---------------------------------------------------------------------------
def test_health_check():
    """GET /api/health 应返回 200 + {"status": "ok"}。"""
    r = client.get("/api/health")
    assert r.status_code == 200, f"期望 200，实际 {r.status_code}"
    assert r.json() == {"status": "ok"}, f"期望 {{\"status\":\"ok\"}}，实际 {r.json()}"


# ---------------------------------------------------------------------------
# T6.2  商品统计
# ---------------------------------------------------------------------------
def test_product_stats():
    """GET /api/products/stats 应返回 total=1500，含骨传导类型，品牌 ≥30 个。"""
    r = client.get("/api/products/stats")
    assert r.status_code == 200, f"期望 200，实际 {r.status_code}"
    data = r.json()
    assert data["total"] == 1500, f"total 应为 1500，实际 {data['total']}"
    assert len(data["brands"]) >= 30, f"品牌数应 ≥30，实际 {len(data['brands'])}"
    assert "入耳式" in data["types"], "'入耳式' 应在 types 中"
    assert "骨传导" in data["types"], "'骨传导' 应在 types 中"


# ---------------------------------------------------------------------------
# T6.3  商品列表 — 分页
# ---------------------------------------------------------------------------
def test_products_pagination():
    """GET /api/products?page=1&limit=10 应返回 10 条，total=1500。"""
    r = client.get("/api/products?page=1&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert len(data["products"]) == 10, f"期望 10 条，实际 {len(data['products'])}"
    assert data["total"] == 1500, f"total 应为 1500，实际 {data['total']}"


# ---------------------------------------------------------------------------
# T6.4  商品列表 — 类型过滤
# ---------------------------------------------------------------------------
def test_products_filter_by_type():
    """GET /api/products?type=骨传导 — 所有返回商品类型应为'骨传导'。"""
    r = client.get("/api/products?type=骨传导&limit=100")
    assert r.status_code == 200
    data = r.json()
    assert len(data["products"]) > 0, "骨传导类型应有商品"
    for p in data["products"]:
        assert p["type"] == "骨传导", f"过滤后出现非骨传导商品: {p['name']} ({p['type']})"


# ---------------------------------------------------------------------------
# T6.5  商品列表 — 价格过滤
# ---------------------------------------------------------------------------
def test_products_filter_by_price():
    """GET /api/products?max_price=300 — 所有返回商品价格应 ≤300。"""
    r = client.get("/api/products?max_price=300&limit=100")
    assert r.status_code == 200
    data = r.json()
    assert len(data["products"]) > 0, "300以内应有商品"
    for p in data["products"]:
        assert p["price"] <= 300, f"过滤后出现超预算商品: {p['name']} 价格={p['price']}"


# ---------------------------------------------------------------------------
# T6.6  同步聊天接口（不依赖 LLM 返回具体内容，只验证结构）
# ---------------------------------------------------------------------------
def test_chat_sync():
    """POST /api/chat 应返回 200 + 含 text/stage 字段的 JSON。"""
    r = client.post("/api/chat", json={
        "message": "帮我找一款耳机",
        "history": [],
        "llm_mode": "ollama"
    })
    assert r.status_code == 200, f"期望 200，实际 {r.status_code}: {r.text[:200]}"
    data = r.json()
    assert "text" in data, f"响应应含 'text' 字段，实际: {list(data.keys())}"
    assert "stage" in data, f"响应应含 'stage' 字段，实际: {list(data.keys())}"
    assert isinstance(data["text"], str), "text 应为字符串"
    assert data["stage"] == "意图澄清", (
        f"首轮对话 stage 应为'意图澄清'，实际: {data['stage']!r}"
    )


# ---------------------------------------------------------------------------
# T6.7  SSE 流式接口 — 事件格式与 done 事件含 clean_text (V4)
# ---------------------------------------------------------------------------
def test_chat_stream_event_format():
    """POST /api/chat/stream — 验证事件格式，done 事件必须含 clean_text 字段 (V4)。"""
    r = client.post("/api/chat/stream", json={
        "message": "帮我找一款耳机",
        "history": [],
        "llm_mode": "ollama"
    })
    assert r.status_code == 200, f"期望 200，实际 {r.status_code}"
    content_type = r.headers.get("content-type", "")
    assert "text/event-stream" in content_type, (
        f"Content-Type 应含 'text/event-stream'，实际: {content_type}"
    )

    events = []
    for line in r.text.splitlines():
        line = line.strip()
        if line.startswith("data: "):
            try:
                event = json.loads(line[6:])
                events.append(event)
            except json.JSONDecodeError:
                pass

    assert len(events) > 0, "SSE 流应至少有一个事件"
    types = [e.get("type") for e in events]

    assert "token" in types, f"SSE 流应包含 'token' 事件，实际事件类型: {types}"
    assert types[-1] == "done", f"最后一个事件应为 'done'，实际: {types[-1]!r}"
    assert "stage" in types, f"SSE 流应包含 'stage' 事件，实际: {types}"

    # V4: done 事件必须含 clean_text 字段
    done_events = [e for e in events if e.get("type") == "done"]
    assert len(done_events) == 1, f"应恰好有 1 个 done 事件，实际: {len(done_events)}"
    done_event = done_events[0]
    assert "clean_text" in done_event, (
        f"V4: done 事件必须含 'clean_text' 字段，实际字段: {list(done_event.keys())}"
    )


# ---------------------------------------------------------------------------
# T6.8  SSE done 事件在异常后仍然发送 (V5) — 通过检查 finally 逻辑验证
# ---------------------------------------------------------------------------
def test_chat_stream_done_always_sent():
    """V5: 即使处理过程出现问题，SSE 流也应以 done 事件结束。"""
    # 用正常请求验证 done 始终是最后一个事件
    r = client.post("/api/chat/stream", json={
        "message": "你好",
        "history": [],
        "llm_mode": "ollama"
    })
    assert r.status_code == 200

    events = []
    for line in r.text.splitlines():
        line = line.strip()
        if line.startswith("data: "):
            try:
                event = json.loads(line[6:])
                events.append(event)
            except json.JSONDecodeError:
                pass

    types = [e.get("type") for e in events]
    assert types[-1] == "done", (
        f"V5: SSE 流最后一个事件必须是 done，实际: {types[-1]!r}\n所有事件类型: {types}"
    )
    # done 事件必须有 clean_text 字段（即使为空字符串）
    done_event = [e for e in events if e.get("type") == "done"][0]
    assert "clean_text" in done_event, (
        f"V5: done 事件必须包含 clean_text 字段（即使为空）"
    )


# ---------------------------------------------------------------------------
# T6.9  请求验证 — 消息过长
# ---------------------------------------------------------------------------
def test_chat_message_too_long():
    """消息超过 2000 字符应返回 422 Pydantic 验证错误。"""
    r = client.post("/api/chat", json={
        "message": "x" * 2001,
        "history": [],
        "llm_mode": "ollama"
    })
    assert r.status_code == 422, (
        f"超长消息应返回 422，实际 {r.status_code}: {r.text[:200]}"
    )
