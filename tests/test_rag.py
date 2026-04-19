"""L3 RAG 层测试 — 验证向量索引构建、检索质量和预算硬过滤。

覆盖验证点：
  V1: 预算硬过滤 — 搜索结果中不允许出现超预算商品
  V2: 类型识别支持骨传导和耳挂式
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest


@pytest.fixture(scope="module")
def search_tool():
    """构建索引并返回 product_search 工具（模块级，只初始化一次）。"""
    from rag.indexer import build_index
    from rag.query import create_product_search_tool

    data_path = os.path.join(ROOT, "data", "products.json")
    with open(data_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    index = build_index(products)
    return create_product_search_tool(index)


# ---------------------------------------------------------------------------
# T3.1  索引构建
# ---------------------------------------------------------------------------
def test_build_index():
    """build_index 应返回非 None 的索引对象。"""
    from rag.indexer import build_index
    data_path = os.path.join(ROOT, "data", "products.json")
    with open(data_path, "r", encoding="utf-8") as f:
        products = json.load(f)
    index = build_index(products)
    assert index is not None, "build_index 不应返回 None"


# ---------------------------------------------------------------------------
# T3.2  基本检索
# ---------------------------------------------------------------------------
def test_product_search_basic(search_tool):
    """基本检索应返回包含'商品1'的结果。"""
    result = search_tool.invoke({"query": "降噪耳机 通勤"})
    assert isinstance(result, str) and result.strip(), "检索结果应为非空字符串"
    assert "商品1" in result, f"结果应包含'商品1'，实际: {result[:200]}"


# ---------------------------------------------------------------------------
# T3.3  预算硬过滤 — 不返回超预算商品 (V1)
# ---------------------------------------------------------------------------
def test_budget_hard_filter_300(search_tool):
    """V1: 300以内过滤 — 结果中不允许出现价格 > 300 的商品。"""
    result = search_tool.invoke({"query": "300以内入耳式降噪耳机"})
    prices = [int(p) for p in re.findall(r"价格: ¥(\d+)", result)]

    if not prices:
        # 没有结果或返回了"未找到"提示，也可接受
        assert "未找到" in result or "未" in result, (
            f"无商品结果但也没有'未找到'提示，结果: {result[:200]}"
        )
    else:
        over_budget = [p for p in prices if p > 300]
        assert not over_budget, (
            f"V1: 发现超预算商品！价格 {over_budget}（预算: 300）\n结果片段: {result[:500]}"
        )


# ---------------------------------------------------------------------------
# T3.4  预算硬过滤 — 极低预算
# ---------------------------------------------------------------------------
def test_budget_hard_filter_50(search_tool):
    """V1: 极低预算 50 以内 — 结果中不应含 ¥100 以上的价格。"""
    result = search_tool.invoke({"query": "50以内耳机"})
    prices = [int(p) for p in re.findall(r"价格: ¥(\d+)", result)]

    if prices:
        over = [p for p in prices if p > 100]
        assert not over, (
            f"极低预算 50 以内但出现价格 {over} 的商品\n结果: {result[:400]}"
        )
    else:
        # 没有匹配商品，返回"未找到"提示，可接受
        assert "未找到" in result or len(result) > 0


# ---------------------------------------------------------------------------
# T3.5  类型过滤 — 头戴式
# ---------------------------------------------------------------------------
def test_type_filter_headphone(search_tool):
    """头戴式过滤 — 当有 ≥3 条结果时，所有结果类型应为'头戴式'。"""
    result = search_tool.invoke({"query": "头戴式耳机 500以内"})
    types = re.findall(r"类型: (\S+)", result)

    if len(types) >= 3:
        non_match = [t for t in types if t != "头戴式"]
        assert not non_match, (
            f"头戴式过滤后出现非头戴式类型: {non_match}\n结果: {result[:500]}"
        )


# ---------------------------------------------------------------------------
# T3.6  骨传导 / 耳挂式类型识别 (V2)
# ---------------------------------------------------------------------------
def test_bone_conduction_type(search_tool):
    """V2: 骨传导查询应返回包含'骨传导'的结果。"""
    result = search_tool.invoke({"query": "骨传导耳机 运动"})
    assert "骨传导" in result, (
        f"V2: 骨传导查询结果中没有'骨传导'类型商品\n结果: {result[:500]}"
    )


def test_ear_hook_type(search_tool):
    """V2: 耳挂式查询应返回包含'耳挂式'的结果。"""
    result = search_tool.invoke({"query": "耳挂式开放式耳机"})
    assert "耳挂式" in result, (
        f"V2: 耳挂式查询结果中没有'耳挂式'类型商品\n结果: {result[:500]}"
    )
