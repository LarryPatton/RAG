import random
from datetime import datetime

from langchain_core.tools import tool

PLATFORM_CODES = {"京东": "JD", "天猫": "TM", "拼多多": "PDD"}


@tool
def place_order(product_name: str, platform: str, price: float) -> str:
    """在指定平台下单购买商品。用户确认后才能调用此工具。
    参数：
    - product_name: 商品名称
    - platform: 购买平台（京东/天猫/拼多多）
    - price: 商品价格"""
    code = PLATFORM_CODES.get(platform, platform[:3].upper())
    order_id = (
        f"{code}{datetime.now().strftime('%Y%m%d')}"
        f"{random.randint(1000, 9999)}"
    )
    return (
        f"下单成功！\n"
        f"订单号：{order_id}\n"
        f"商品：{product_name}\n"
        f"平台：{platform}\n"
        f"金额：¥{price}\n"
        f"预计送达：明天 18:00 前"
    )
