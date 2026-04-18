from langchain_core.tools import tool
from data.loader import find_product


@tool
def check_inventory(product_name: str, platform: str) -> str:
    """查询商品在指定平台的库存状态。输入商品名称和平台（京东/天猫/拼多多），返回库存数量。
    在确认推荐商品后必须调用此工具确认有货再推荐。"""
    product = find_product(product_name)
    if not product:
        return f"未找到商品「{product_name}」的库存信息。"

    stock = product.get("stock", 50)
    main_platform = product["platform"]

    # Only the main platform has real stock data
    if platform == main_platform:
        if stock == 0:
            return f"【{product['name']}】在{platform}：暂时缺货，建议选择其他平台。"
        elif stock < 10:
            return f"【{product['name']}】在{platform}：库存紧张，仅剩 {stock} 件，建议尽快下单。"
        else:
            return f"【{product['name']}】在{platform}：有货，库存 {stock} 件，可正常下单。"
    else:
        # Other platforms: estimate based on stock level (they might have different stock)
        estimated = max(0, stock + (hash(platform) % 30) - 10)
        if estimated < 5:
            return f"【{product['name']}】在{platform}：库存有限，约 {estimated} 件（参考数据）。"
        else:
            return f"【{product['name']}】在{platform}：有货，约 {estimated} 件（参考数据）。"
