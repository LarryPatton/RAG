"""L4 解析层测试 — 验证 agent_service.py 中的纯函数：
parse_structured_output、extract_stage、_build_decision_prefix。

覆盖验证点 V3: 只有 JSON 没有文字时 clean_text 应为空字符串。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest

from api.services.agent_service import parse_structured_output, extract_stage, AgentService


# ---------------------------------------------------------------------------
# T4.1  parse_structured_output — 文字 + quick_replies
# ---------------------------------------------------------------------------
def test_parse_text_with_quick_replies():
    """有文字 + quick_replies JSON 块：text 为文字部分，quick_replies 为选项列表。"""
    text = "[意图澄清] 您的预算是多少？\n\n```json\n{\"type\": \"quick_replies\", \"options\": [\"200以内\", \"200-500\", \"500-1000\"]}\n```"
    result = parse_structured_output(text)
    assert result["text"].strip() == "[意图澄清] 您的预算是多少？", (
        f"text 应为问题文字，实际: {result['text']!r}"
    )
    assert result["quick_replies"] == ["200以内", "200-500", "500-1000"], (
        f"quick_replies 应为选项列表，实际: {result['quick_replies']}"
    )
    assert result["structured_data"] is None, "无推荐/订单 JSON 时 structured_data 应为 None"


# ---------------------------------------------------------------------------
# T4.2  parse_structured_output — recommendation JSON
# ---------------------------------------------------------------------------
def test_parse_recommendation_json():
    """recommendation JSON 块 + 尾部文字：structured_data 有 type=recommendation，text 为尾部文字。"""
    text = '```json\n{"type": "recommendation", "products": [{"rank":1,"name":"test"}], "verdict":"好"}\n```\n\n推荐第一款。'
    result = parse_structured_output(text)
    assert result["structured_data"] is not None, "recommendation JSON 应被解析"
    assert result["structured_data"]["type"] == "recommendation"
    assert result["text"].strip() == "推荐第一款。", (
        f"text 应为'推荐第一款。'，实际: {result['text']!r}"
    )


# ---------------------------------------------------------------------------
# T4.3  parse_structured_output — 纯文本（无 JSON）
# ---------------------------------------------------------------------------
def test_parse_plain_text():
    """纯文本（没有 JSON 块）：text 为原文，structured_data 和 quick_replies 均为 None。"""
    text = "[意图澄清] 请问您想找什么耳机？"
    result = parse_structured_output(text)
    assert result["text"] == text, f"纯文本应原样保留，实际: {result['text']!r}"
    assert result["structured_data"] is None
    assert result["quick_replies"] is None


# ---------------------------------------------------------------------------
# T4.4  parse_structured_output — 只有 JSON 没有文字（V3 关键边界）
# ---------------------------------------------------------------------------
def test_parse_json_only_no_text():
    """V3: 只有 JSON 块，没有任何额外文字时，clean_text 应为空字符串。"""
    text = '```json\n{"type": "quick_replies", "options": ["A", "B"]}\n```'
    result = parse_structured_output(text)
    assert result["text"] == "", (
        f"V3: 只有 JSON 时 text 应为空字符串，实际: {result['text']!r}"
    )
    assert result["quick_replies"] == ["A", "B"], (
        f"quick_replies 应为 ['A','B']，实际: {result['quick_replies']}"
    )


# ---------------------------------------------------------------------------
# T4.5  extract_stage — 各阶段识别
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("text,expected", [
    ("[意图澄清] 你好", "意图澄清"),
    ("[推荐方案] 推荐3款", "推荐方案"),
    ("[分析中] [搜索中] 正在处理", "搜索中"),  # 取最高级（搜索中 > 分析中）
    ("没有标签的回复", "未知"),
])
def test_extract_stage_from_text(text, expected):
    """extract_stage 应能从文本标签中提取最高级阶段。"""
    result = extract_stage(text)
    assert result == expected, f"文本 {text!r} 应提取阶段 {expected!r}，实际: {result!r}"


# ---------------------------------------------------------------------------
# T4.6  extract_stage — structured_data 推断
# ---------------------------------------------------------------------------
def test_extract_stage_from_structured_data():
    """structured_data 中的 type 字段可推断阶段。"""
    assert extract_stage("文字", {"type": "recommendation"}) == "推荐方案"
    assert extract_stage("文字", {"type": "order_confirm"}) == "订单确认"


# ---------------------------------------------------------------------------
# T4.7  _build_decision_prefix — 正常决策
# ---------------------------------------------------------------------------
def test_build_decision_prefix_normal():
    """_build_decision_prefix 应生成含决策信息的前缀字符串。"""
    svc = AgentService()
    prefix = svc._build_decision_prefix({"type": "头戴式", "budget": "≤¥500"})
    assert "[已确认的用户决策" in prefix, f"prefix 应含'[已确认的用户决策'，实际: {prefix!r}"
    assert "耳机类型: 头戴式" in prefix, f"prefix 应含耳机类型信息，实际: {prefix!r}"
    assert "预算: ≤¥500" in prefix, f"prefix 应含预算信息，实际: {prefix!r}"


# ---------------------------------------------------------------------------
# T4.8  _build_decision_prefix — 空决策
# ---------------------------------------------------------------------------
def test_build_decision_prefix_empty():
    """空决策字典应返回空字符串。"""
    svc = AgentService()
    prefix = svc._build_decision_prefix({})
    assert prefix == "", f"空决策应返回空字符串，实际: {prefix!r}"
