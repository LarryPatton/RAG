"""L2 工具层测试 — 验证 LangChain @tool 函数的输入/输出格式和边界条件。

注意：工具函数通过 tool.invoke({"param": value}) 调用。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest

# ---------------------------------------------------------------------------
# 加载真实商品数据（供测试使用）
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def sample():
    """返回 (sample_name, sample_platform) 元组。"""
    data_path = os.path.join(ROOT, "data", "products.json")
    with open(data_path, "r", encoding="utf-8") as f:
        products = json.load(f)
    p = products[0]
    return p["name"], p["platform"]


# ---------------------------------------------------------------------------
# T2.1  compare_prices — 正常调用
# ---------------------------------------------------------------------------
def test_compare_prices_normal(sample):
    """compare_prices 应返回包含平台名称和最低价的字符串。"""
    from tools.price_comparison import compare_prices
    product_name, _ = sample
    result = compare_prices.invoke({"product_name": product_name})
    assert isinstance(result, str), "结果应为字符串"
    assert any(p in result for p in ["京东", "天猫", "拼多多"]), "结果应包含平台名称"
    assert "最低价" in result, "结果应包含'最低价'字段"


# ---------------------------------------------------------------------------
# T2.2  compare_prices — 商品不存在
# ---------------------------------------------------------------------------
def test_compare_prices_not_found():
    """不存在的商品名称应返回包含'未找到'的提示或空字符串。"""
    from tools.price_comparison import compare_prices
    result = compare_prices.invoke({"product_name": "完全不存在的商品XYZ_QWERTY_99999"})
    assert isinstance(result, str)
    # 应包含"未找到"，或结果为空字符串
    assert "未找到" in result or result == "", f"预期'未找到'提示，实际: {result!r}"


# ---------------------------------------------------------------------------
# T2.3  check_inventory — 有货商品（主平台）
# ---------------------------------------------------------------------------
def test_check_inventory_in_stock(sample):
    """check_inventory 对主平台商品应返回含'件'或'缺货'或'库存'的字符串。"""
    from tools.inventory import check_inventory
    product_name, platform = sample
    result = check_inventory.invoke({"product_name": product_name, "platform": platform})
    assert isinstance(result, str), "结果应为字符串"
    # 结果中应包含商品名称的部分（或商品相关信息）
    assert any(kw in result for kw in ["件", "缺货", "库存"]), (
        f"结果应包含'件'/'缺货'/'库存'，实际: {result!r}"
    )


# ---------------------------------------------------------------------------
# T2.4  check_inventory — 跨平台查询（非主平台）
# ---------------------------------------------------------------------------
def test_check_inventory_cross_platform(sample):
    """check_inventory 对非主平台查询也应返回非空字符串。"""
    from tools.inventory import check_inventory
    product_name, platform = sample
    other_platform = [p for p in ["京东", "天猫", "拼多多"] if p != platform][0]
    result = check_inventory.invoke({"product_name": product_name, "platform": other_platform})
    assert isinstance(result, str) and result.strip(), "跨平台查询应返回非空字符串"


# ---------------------------------------------------------------------------
# T2.5  place_order — 正常下单（京东）
# ---------------------------------------------------------------------------
def test_place_order_normal(sample):
    """place_order 应返回含订单号、JD 前缀、'明天'的字符串。"""
    from tools.order import place_order
    product_name, _ = sample
    result = place_order.invoke({"product_name": product_name, "platform": "京东", "price": 299.0})
    assert isinstance(result, str)
    assert "订单号" in result, f"结果应含'订单号'，实际: {result!r}"
    assert "JD" in result, f"京东订单号前缀应为'JD'，实际: {result!r}"
    assert "明天" in result, f"结果应含'明天'（预计送达），实际: {result!r}"


# ---------------------------------------------------------------------------
# T2.6  place_order — 各平台订单号前缀
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("platform,prefix", [
    ("京东", "JD"),
    ("天猫", "TM"),
    ("拼多多", "PDD"),
])
def test_place_order_platform_codes(sample, platform, prefix):
    """各平台的订单号前缀应分别为 JD / TM / PDD。"""
    from tools.order import place_order
    product_name, _ = sample
    result = place_order.invoke({"product_name": product_name, "platform": platform, "price": 199.0})
    assert prefix in result, (
        f"平台'{platform}'的订单号应含前缀'{prefix}'，实际: {result!r}"
    )
