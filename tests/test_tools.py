from tools.order import place_order
from rag.query import create_product_search_tool
from rag.indexer import build_index

SAMPLE_PRODUCTS = [
    {
        "id": "t001",
        "name": "Sony 测试降噪入耳耳机",
        "category": "耳机",
        "type": "入耳式",
        "brand": "Sony",
        "price": 399,
        "platform": "京东",
        "rating": 4.5,
        "features": ["主动降噪", "蓝牙5.0"],
        "scenario": ["通勤"],
        "noise_cancellation": "主动降噪",
        "description": "测试降噪耳机，通勤使用"
    },
    {
        "id": "t002",
        "name": "JBL 测试运动耳机",
        "category": "耳机",
        "type": "入耳式",
        "brand": "JBL",
        "price": 199,
        "platform": "淘宝",
        "rating": 4.0,
        "features": ["防水", "运动"],
        "scenario": ["运动"],
        "noise_cancellation": "无",
        "description": "测试运动耳机"
    },
]


def test_product_search_tool_returns_results():
    index = build_index(SAMPLE_PRODUCTS)
    search_tool = create_product_search_tool(index)
    result = search_tool.invoke("降噪耳机 通勤")
    assert isinstance(result, str)
    assert len(result) > 0


def test_place_order_returns_confirmation():
    result = place_order.invoke({
        "product_name": "Sony WI-C100",
        "platform": "京东",
        "price": 299.0
    })
    assert "下单成功" in result
    assert "订单号" in result
    assert "Sony WI-C100" in result
    assert "京东" in result
    assert "299" in result
