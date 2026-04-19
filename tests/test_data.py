"""L1 数据层测试 — 验证 products.json 完整性和 data/loader.py 的 find_product 功能。

覆盖验证点 V10: 商品 1500 条，四种类型各 ≥10%
"""
import json
import os
import sys

# 确保项目根目录在 sys.path 中
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest

DATA_PATH = os.path.join(ROOT, "data", "products.json")

VALID_TYPES = {"入耳式", "头戴式", "骨传导", "耳挂式"}
VALID_PLATFORMS = {"京东", "天猫", "拼多多"}
ALL_PLATFORMS = ["京东", "天猫", "拼多多"]


@pytest.fixture(scope="module")
def products():
    """加载全部商品数据（模块级缓存）。"""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# T1.1  商品数量验证
# ---------------------------------------------------------------------------
def test_product_count(products):
    """V10: 必须恰好有 1500 条商品。"""
    assert len(products) == 1500, f"期望 1500 条，实际 {len(products)} 条"


# ---------------------------------------------------------------------------
# T1.2  数据字段完整性
# ---------------------------------------------------------------------------
def test_field_completeness(products):
    """验证每条商品的字段类型和约束。"""
    errors = []
    for i, p in enumerate(products):
        idx = f"[{i}] {p.get('name', '<unnamed>')}"

        # id
        if not isinstance(p.get("id"), str) or not p["id"].startswith("hp_"):
            errors.append(f"{idx}: id 格式错误 ({p.get('id')})")

        # name
        if not isinstance(p.get("name"), str) or not p["name"].strip():
            errors.append(f"{idx}: name 为空或类型错误")

        # category
        if not isinstance(p.get("category"), str):
            errors.append(f"{idx}: category 类型错误")

        # type
        if p.get("type") not in VALID_TYPES:
            errors.append(f"{idx}: type 值非法 ({p.get('type')})")

        # brand
        if not isinstance(p.get("brand"), str) or not p["brand"].strip():
            errors.append(f"{idx}: brand 为空或类型错误")

        # price
        price = p.get("price")
        if not isinstance(price, int) or not (50 <= price <= 6000):
            errors.append(f"{idx}: price 超范围或类型错误 ({price})")

        # platform
        if p.get("platform") not in VALID_PLATFORMS:
            errors.append(f"{idx}: platform 值非法 ({p.get('platform')})")

        # rating
        rating = p.get("rating")
        if not isinstance(rating, (int, float)) or not (3.8 <= rating <= 4.9):
            errors.append(f"{idx}: rating 超范围 ({rating})")

        # features
        features = p.get("features")
        if not isinstance(features, list) or len(features) < 3:
            errors.append(f"{idx}: features 长度不足 ({len(features) if isinstance(features, list) else '非列表'})")

        # scenario
        scenario = p.get("scenario")
        if not isinstance(scenario, list) or len(scenario) < 1:
            errors.append(f"{idx}: scenario 长度不足")

        # noise_cancellation
        if not isinstance(p.get("noise_cancellation"), str):
            errors.append(f"{idx}: noise_cancellation 类型错误")

        # description
        if not isinstance(p.get("description"), str) or not p["description"].strip():
            errors.append(f"{idx}: description 为空")

        # stock
        stock = p.get("stock")
        if not isinstance(stock, int) or not (0 <= stock <= 100):
            errors.append(f"{idx}: stock 超范围 ({stock})")

        # other_platform_prices
        opp = p.get("other_platform_prices")
        if not isinstance(opp, dict) or len(opp) != 2:
            errors.append(f"{idx}: other_platform_prices 键数量错误 ({opp})")
        else:
            # 应该是另外两个平台
            expected_other = set(ALL_PLATFORMS) - {p["platform"]}
            if set(opp.keys()) != expected_other:
                errors.append(f"{idx}: other_platform_prices 平台键不匹配 (期望 {expected_other}, 实际 {set(opp.keys())})")

    assert not errors, f"发现 {len(errors)} 个字段错误:\n" + "\n".join(errors[:20])


# ---------------------------------------------------------------------------
# T1.3  类型分布均匀性  (V10)
# ---------------------------------------------------------------------------
def test_type_distribution(products):
    """V10: 四种类型各至少占 10%（≥150 条）。"""
    from collections import Counter
    counts = Counter(p["type"] for p in products)
    total = len(products)
    for t in VALID_TYPES:
        cnt = counts.get(t, 0)
        pct = cnt / total * 100
        assert cnt >= 150, (
            f"类型「{t}」仅 {cnt} 条 ({pct:.1f}%)，不足 10%（150条）"
        )


# ---------------------------------------------------------------------------
# T1.4  平台分布均匀性
# ---------------------------------------------------------------------------
def test_platform_distribution(products):
    """三个平台各占比应在 28%-40% 之间。"""
    from collections import Counter
    counts = Counter(p["platform"] for p in products)
    total = len(products)
    for plat in VALID_PLATFORMS:
        cnt = counts.get(plat, 0)
        pct = cnt / total * 100
        assert 28 <= pct <= 40, (
            f"平台「{plat}」占比 {pct:.1f}%，不在 28%-40% 范围内（数量: {cnt}）"
        )


# ---------------------------------------------------------------------------
# T1.5  find_product — 精确匹配
# ---------------------------------------------------------------------------
def test_find_product_exact(products):
    """find_product 应能精确匹配已存在的商品名称。"""
    from data.loader import find_product
    # 使用 products[0] 作为已知商品
    sample_name = products[0]["name"]
    result = find_product(sample_name)
    assert result is not None, f"精确匹配 '{sample_name}' 应命中，返回 None"
    assert result["name"] == sample_name


# ---------------------------------------------------------------------------
# T1.6  find_product — 模糊匹配（子串）
# ---------------------------------------------------------------------------
def test_find_product_fuzzy(products):
    """find_product 应支持 4+ 字符子串模糊匹配。"""
    from data.loader import find_product
    # 取一个名称足够长的商品，截取中间部分
    sample = next(p for p in products if len(p["name"]) >= 8)
    # 截取名称中间 5 个字符作为模糊查询键
    query = sample["name"][2:7]
    result = find_product(query)
    assert result is not None, f"模糊匹配 '{query}' 应命中，返回 None"


# ---------------------------------------------------------------------------
# T1.7  find_product — 不存在的商品
# ---------------------------------------------------------------------------
def test_find_product_not_found():
    """find_product 对不存在的商品应返回 None。"""
    from data.loader import find_product
    result = find_product("不存在的商品ABC_XYZ_12345")
    assert result is None, f"不存在的商品应返回 None，实际返回: {result}"
