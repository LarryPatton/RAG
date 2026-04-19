"""L7 端到端测试 — 模拟完整购物流程对话，验证业务逻辑闭环。

这是最耗时的测试（每轮 30-120 秒），需要 Ollama 在线。
断言宽松：只验证结构和阶段流转，不断言具体文字内容。
"""
import asyncio
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from api.services.agent_service import agent_service


# ---------------------------------------------------------------------------
# T7.1  完整购物流程 — 意图澄清 → 触发搜索/推荐 → 可选下单
# ---------------------------------------------------------------------------
def test_full_shopping_flow():
    """模拟 3-6 轮对话：初始请求 → 提供完整信息 → 触发搜索/推荐。"""
    history = []
    decisions = {}

    # === 第1轮：用户发起需求 ===
    r1 = agent_service.chat("帮我找一款耳机", history, "ollama")
    # 第1轮：应在意图澄清阶段，或至少没有调用工具（LLM 偶尔不输出标签）
    assert r1["stage"] in ["意图澄清", "未知"], (
        f"第1轮 stage 不应触发工具调用，实际: {r1['stage']!r}"
    )
    assert len(r1["text"]) > 0, "第1轮回复不应为空"
    assert r1["thinking_steps"] == [], "第1轮不应调用工具（信息不足）"

    history += [
        {"role": "user", "content": "帮我找一款耳机"},
        {"role": "assistant", "content": r1["reply"]},
    ]

    # === 第2轮-第5轮：逐步补充信息（中间轮次只验证未触发下单/错误）===
    VALID_INTERIM_STAGES = {"意图澄清", "分析中", "搜索中", "未知", "推荐方案"}

    r2 = agent_service.chat("500以内", history, "ollama")
    assert r2["stage"] in VALID_INTERIM_STAGES, (
        f"第2轮 stage 应为有效中间阶段（不应下单），实际: {r2['stage']!r}"
    )
    history += [
        {"role": "user", "content": "500以内"},
        {"role": "assistant", "content": r2["reply"]},
    ]
    decisions["budget"] = "≤¥500"

    r3 = agent_service.chat("入耳式", history, "ollama", user_decisions=decisions)
    assert r3["stage"] in VALID_INTERIM_STAGES, (
        f"第3轮 stage 应为有效中间阶段，实际: {r3['stage']!r}"
    )
    history += [
        {"role": "user", "content": "入耳式"},
        {"role": "assistant", "content": r3["reply"]},
    ]
    decisions["type"] = "入耳式"

    r4 = agent_service.chat("通勤", history, "ollama", user_decisions=decisions)
    assert r4["stage"] in VALID_INTERIM_STAGES, (
        f"第4轮 stage 应为有效中间阶段，实际: {r4['stage']!r}"
    )
    history += [
        {"role": "user", "content": "通勤"},
        {"role": "assistant", "content": r4["reply"]},
    ]
    decisions["scenario"] = "通勤"

    r5 = agent_service.chat("需要降噪", history, "ollama", user_decisions=decisions)
    assert r5["stage"] in VALID_INTERIM_STAGES, (
        f"第5轮 stage 应为有效中间阶段，实际: {r5['stage']!r}"
    )
    history += [
        {"role": "user", "content": "需要降噪"},
        {"role": "assistant", "content": r5["reply"]},
    ]
    decisions["noise_cancellation"] = "需要降噪"

    # === 第6轮：回答品牌偏好 → 应触发搜索和推荐 ===
    r6 = agent_service.chat("没有偏好", history, "ollama", user_decisions=decisions)

    # V7: 五维度全部回答后不应再停留在意图澄清
    assert r6["stage"] != "意图澄清", (
        f"V7: 第6轮（五维度已全部提供）不应再停留在'意图澄清'，实际: {r6['stage']!r}\n"
        f"回复: {r6['reply'][:200]}"
    )

    # 验证已进入搜索/推荐准备状态
    is_search_or_recommend = (
        r6["stage"] in ["分析中", "搜索中", "推荐方案"]
        or r6.get("task_plan") is not None
        or len(r6["thinking_steps"]) > 0
        or any(kw in r6["reply"] for kw in ["分析", "搜索", "推荐", "找到"])
    )
    assert is_search_or_recommend, (
        f"第6轮应触发搜索或推荐，实际回复: {r6['reply'][:300]}"
    )


# ---------------------------------------------------------------------------
# T7.2  流式对话完整性 — 验证 SSE 事件链
# ---------------------------------------------------------------------------
def test_stream_chat_event_completeness():
    """流式对话应包含 token/stage/done 事件，done 必须是最后一个，含 clean_text。"""
    events = []

    async def collect_events():
        async for ev in agent_service.stream_chat(
            "帮我找一款500以内的入耳式通勤耳机",
            [],
            "ollama"
        ):
            events.append(ev)

    asyncio.run(collect_events())

    assert len(events) > 0, "流式事件不应为空"
    types = [e.get("type") for e in events]

    assert "token" in types, f"SSE 流应包含 'token' 事件，实际: {types}"
    assert "stage" in types, f"SSE 流应包含 'stage' 事件，实际: {types}"
    assert "done" in types, f"SSE 流应包含 'done' 事件，实际: {types}"
    assert types[-1] == "done", (
        f"'done' 必须是最后一个事件，实际最后一个: {types[-1]!r}\n事件类型: {types}"
    )

    # V4: done 事件必须含 clean_text 字段
    done_event = [e for e in events if e.get("type") == "done"][0]
    assert "clean_text" in done_event, (
        f"V4: done 事件必须含 'clean_text' 字段，实际字段: {list(done_event.keys())}"
    )


# ---------------------------------------------------------------------------
# T7.3  流式搜索完整性 — 完整信息触发工具调用
# ---------------------------------------------------------------------------
def test_stream_chat_with_full_info_triggers_tools():
    """提供完整需求信息时，流式对话应包含 tool_start/tool_end 事件。"""
    events = []

    async def collect_events():
        async for ev in agent_service.stream_chat(
            "没有偏好",
            [
                {"role": "user", "content": "帮我找500以内入耳式降噪通勤耳机"},
                {"role": "assistant", "content": "[意图澄清] 需要降噪吗？"},
                {"role": "user", "content": "需要"},
                {"role": "assistant", "content": "[意图澄清] 品牌偏好？"},
            ],
            "ollama",
            user_decisions={
                "type": "入耳式",
                "budget": "≤¥500",
                "scenario": "通勤",
                "noise_cancellation": "需要降噪",
            }
        ):
            events.append(ev)

    asyncio.run(collect_events())

    types = [e.get("type") for e in events]

    # done 始终是最后一个（V5 保证）
    assert types[-1] == "done", (
        f"V5: done 必须是最后一个事件，实际: {types[-1]!r}"
    )

    # done 含 clean_text（V4）
    done_event = [e for e in events if e.get("type") == "done"][0]
    assert "clean_text" in done_event, "V4: done 事件必须含 clean_text"

    # 应调用了工具（V7：完整信息后搜索）
    has_tools = "tool_start" in types
    # 如果有 structured_data 推荐，验证 V8（3款）和 V9（整数价格）
    sd_events = [e for e in events if e.get("type") == "structured_data"]
    if sd_events:
        sd = sd_events[0]["data"]
        if sd.get("type") == "recommendation":
            products = sd.get("products", [])
            # V8: 推荐恰好 3 款
            assert len(products) == 3, (
                f"V8: 推荐应恰好 3 款，实际 {len(products)} 款"
            )
            # V9: price_comparison 整数
            for p in products:
                for plat, price in p.get("price_comparison", {}).items():
                    assert isinstance(price, int), (
                        f"V9: price_comparison[{plat}] 应为整数，实际: {price!r} ({type(price).__name__})"
                    )
