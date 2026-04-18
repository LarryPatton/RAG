from langchain_core.tools import tool
from data.loader import find_product


@tool
def compare_prices(product_name: str) -> str:
    """查询商品在各平台的价格对比。输入商品名称，返回京东/天猫/拼多多的完整价格信息。
    在推荐商品后必须调用此工具获取跨平台价格数据。"""
    product = find_product(product_name)
    if not product:
        return f"未找到商品「{product_name}」的价格信息。"

    main_platform = product["platform"]
    main_price = product["price"]
    other_prices = product.get("other_platform_prices", {})

    lines = [f"【{product['name']}】价格对比："]
    all_prices = {main_platform: main_price, **other_prices}
    for platform, price in sorted(all_prices.items(), key=lambda x: x[1]):
        tag = "✓ 在售" if platform == main_platform else "参考"
        lines.append(f"  {platform}：¥{price}（{tag}）")

    cheapest = min(all_prices, key=lambda k: all_prices[k])
    lines.append(f"最低价平台：{cheapest}（¥{all_prices[cheapest]}）")
    return "\n".join(lines)
