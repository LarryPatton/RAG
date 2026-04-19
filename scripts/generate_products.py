"""
Generate 1500 realistic Chinese headphone product entries.
Output: G:/RAG/data/products.json
"""

import json
import random
import os

random.seed(42)

# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

BRANDS = {
    # tier -> list of (brand_display_name, [product_lines])
    # product_line: (model_suffix, type, base_price, nc_profile)
    # nc_profile: "anc" | "tnc" | "pnc" | "none"
    "高端": [
        {
            "brand": "Sony",
            "lines": [
                ("WI-C100", "入耳式", 199, "pnc"),
                ("WF-C500", "入耳式", 399, "pnc"),
                ("WF-C700N", "入耳式", 699, "anc"),
                ("LinkBuds S", "入耳式", 999, "anc"),
                ("WF-1000XM5", "入耳式", 1599, "anc"),
                ("LinkBuds Open", "耳挂式", 1299, "none"),
                ("Float Run", "耳挂式", 899, "none"),
                ("WH-CH520", "头戴式", 299, "pnc"),
                ("WH-1000XM4", "头戴式", 1799, "anc"),
                ("WH-1000XM5", "头戴式", 1999, "anc"),
                ("WH-XB910N", "头戴式", 899, "anc"),
            ],
        },
        {
            "brand": "Bose",
            "lines": [
                ("QuietComfort Earbuds II", "入耳式", 1799, "anc"),
                ("QuietComfort 45", "头戴式", 1999, "anc"),
                ("QuietComfort Ultra 头戴版", "头戴式", 2499, "anc"),
                ("QuietComfort Ultra 耳塞版", "入耳式", 2199, "anc"),
                ("Ultra Open Earbuds", "耳挂式", 1499, "none"),
                ("SoundLink Flex", "入耳式", 899, "pnc"),
                ("Sport Earbuds", "入耳式", 699, "pnc"),
                ("Sport Open Earbuds", "耳挂式", 999, "none"),
            ],
        },
        {
            "brand": "森海塞尔",
            "lines": [
                ("CX True Wireless", "入耳式", 599, "tnc"),
                ("MOMENTUM True Wireless 3", "入耳式", 1299, "anc"),
                ("MOMENTUM True Wireless 4", "入耳式", 1699, "anc"),
                ("MOMENTUM 4 无线", "头戴式", 2199, "anc"),
                ("HD 560S", "头戴式", 1099, "pnc"),
                ("HD 600", "头戴式", 2799, "pnc"),
            ],
        },
        {
            "brand": "B&O",
            "lines": [
                ("Beoplay EX", "入耳式", 2499, "anc"),
                ("Beoplay H95", "头戴式", 4999, "anc"),
                ("Beoplay H9", "头戴式", 3299, "anc"),
                ("Beoplay E8 Sport", "入耳式", 1799, "pnc"),
            ],
        },
        {
            "brand": "AKG",
            "lines": [
                ("Y500 无线", "头戴式", 699, "pnc"),
                ("N400 真无线", "入耳式", 599, "anc"),
                ("N700NC M2", "头戴式", 1499, "anc"),
                ("K371", "头戴式", 799, "pnc"),
            ],
        },
    ],
    "中高端": [
        {
            "brand": "华为",
            "lines": [
                ("FreeBuds SE 2", "入耳式", 179, "pnc"),
                ("FreeBuds 5i", "入耳式", 399, "anc"),
                ("FreeBuds 5", "入耳式", 599, "anc"),
                ("FreeBuds Pro 3", "入耳式", 999, "anc"),
                ("FreeBuds Studio 2", "头戴式", 1099, "anc"),
                ("FreeLace Pro", "入耳式", 399, "anc"),
                ("FreeClip", "耳挂式", 1099, "none"),
            ],
        },
        {
            "brand": "三星",
            "lines": [
                ("Galaxy Buds FE", "入耳式", 399, "anc"),
                ("Galaxy Buds 2", "入耳式", 499, "anc"),
                ("Galaxy Buds 2 Pro", "入耳式", 999, "anc"),
                ("Galaxy Buds 3", "入耳式", 699, "anc"),
                ("Galaxy Buds 3 Pro", "入耳式", 1199, "anc"),
            ],
        },
        {
            "brand": "JBL",
            "lines": [
                ("Tune 130NC TWS", "入耳式", 299, "anc"),
                ("Tune 230NC TWS", "入耳式", 399, "anc"),
                ("Live Free 2 TWS", "入耳式", 599, "anc"),
                ("Live Pro 2 TWS", "入耳式", 799, "anc"),
                ("Soundgear Sense", "耳挂式", 799, "none"),
                ("Tour One M2", "头戴式", 1199, "anc"),
                ("Tune 770NC", "头戴式", 499, "anc"),
                ("Tune 510BT", "头戴式", 199, "pnc"),
            ],
        },
        {
            "brand": "铁三角",
            "lines": [
                ("ATH-CKS50TW", "入耳式", 699, "anc"),
                ("ATH-TWX7", "入耳式", 999, "anc"),
                ("ATH-M20xBT", "头戴式", 499, "pnc"),
                ("ATH-M50xBT2", "头戴式", 1199, "pnc"),
                ("ATH-ANC300TW", "入耳式", 599, "anc"),
            ],
        },
        {
            "brand": "万魔",
            "lines": [
                ("ComfoBuds Mini", "入耳式", 149, "tnc"),
                ("SonoFlow SE", "头戴式", 199, "anc"),
                ("SonoFlow", "头戴式", 399, "anc"),
                ("SonoFlow Pro", "头戴式", 699, "anc"),
                ("EVO", "入耳式", 399, "anc"),
                ("PistonBuds Pro Q30", "入耳式", 249, "anc"),
                ("Aero 开放式", "耳挂式", 499, "none"),
            ],
        },
    ],
    "性价比": [
        {
            "brand": "小米",
            "lines": [
                ("Redmi Buds 4 Lite", "入耳式", 69, "pnc"),
                ("Redmi Buds 5", "入耳式", 149, "tnc"),
                ("Redmi Buds 5 Pro", "入耳式", 299, "anc"),
                ("Buds 4", "入耳式", 349, "anc"),
                ("Buds 4 Pro", "入耳式", 599, "anc"),
                ("头戴式耳机 Pro", "头戴式", 449, "anc"),
                ("Redmi Buds 4 Active", "入耳式", 99, "pnc"),
            ],
        },
        {
            "brand": "漫步者",
            "lines": [
                ("W240BT", "入耳式", 79, "pnc"),
                ("W360BT", "入耳式", 129, "tnc"),
                ("NeoBuds Pro", "入耳式", 499, "anc"),
                ("NeoBuds Pro 2", "入耳式", 699, "anc"),
                ("Comfo Fit Open", "耳挂式", 299, "none"),
                ("W820NB Plus", "头戴式", 259, "anc"),
                ("W860NB", "头戴式", 399, "anc"),
                ("STAX Spirit S3", "头戴式", 1799, "anc"),
            ],
        },
        {
            "brand": "QCY",
            "lines": [
                ("T13", "入耳式", 79, "pnc"),
                ("T17S", "入耳式", 99, "tnc"),
                ("AilyBuds Pro+", "入耳式", 149, "anc"),
                ("Crossky Link", "耳挂式", 129, "none"),
                ("Crossky Link 2", "耳挂式", 199, "none"),
                ("H3", "头戴式", 99, "pnc"),
                ("HT07 ANC", "头戴式", 149, "anc"),
                ("HT05 MeloBuds ANC", "入耳式", 199, "anc"),
            ],
        },
        {
            "brand": "倍思",
            "lines": [
                ("Bowie EZ10", "入耳式", 59, "pnc"),
                ("Bowie MA10", "入耳式", 99, "tnc"),
                ("Bowie WM02", "入耳式", 149, "tnc"),
                ("Bowie H1i ANC", "头戴式", 199, "anc"),
                ("Bowie H2 ANC", "头戴式", 299, "anc"),
                ("Eli Sport 1", "耳挂式", 149, "none"),
            ],
        },
        {
            "brand": "联想",
            "lines": [
                ("LP40 Pro", "入耳式", 69, "pnc"),
                ("LP5", "入耳式", 99, "pnc"),
                ("XT88", "入耳式", 79, "tnc"),
                ("TH30 Pro", "头戴式", 129, "pnc"),
                ("TH40 Pro", "头戴式", 199, "anc"),
            ],
        },
    ],
    "运动骨传导": [
        {
            "brand": "韶音",
            "lines": [
                ("OpenRun", "骨传导", 699, "none"),
                ("OpenRun Pro", "骨传导", 999, "none"),
                ("OpenRun Pro 2", "骨传导", 1299, "none"),
                ("OpenRun Mini", "骨传导", 599, "none"),
                ("OpenSwim", "骨传导", 899, "none"),
                ("OpenSwim Pro", "骨传导", 1199, "none"),
                ("OpenFit", "耳挂式", 899, "none"),
                ("OpenFit Air", "耳挂式", 599, "none"),
            ],
        },
        {
            "brand": "南卡",
            "lines": [
                ("OE Mix", "耳挂式", 299, "none"),
                ("OE Mix 2", "耳挂式", 399, "none"),
                ("OE Pro", "耳挂式", 499, "none"),
                ("Runner Pro 5", "骨传导", 499, "none"),
                ("Runner CC 3", "骨传导", 299, "none"),
                ("Lite3", "骨传导", 299, "none"),
                ("CC Ultra", "骨传导", 699, "none"),
            ],
        },
        {
            "brand": "Oladance",
            "lines": [
                ("OWS 2", "耳挂式", 999, "none"),
                ("OWS Pro", "耳挂式", 1299, "none"),
                ("OWS Sports", "耳挂式", 799, "none"),
            ],
        },
        {
            "brand": "墨觉",
            "lines": [
                ("Run Plus", "骨传导", 499, "none"),
                ("Mojo 2", "骨传导", 799, "none"),
                ("HaptiFit Terra", "骨传导", 599, "none"),
            ],
        },
        {
            "brand": "Cleer",
            "lines": [
                ("Arc 开放式", "耳挂式", 999, "none"),
                ("Arc II Sport", "耳挂式", 799, "none"),
                ("Arc II Music", "耳挂式", 899, "none"),
            ],
        },
        {
            "brand": "Jaybird",
            "lines": [
                ("Vista 2", "入耳式", 699, "anc"),
                ("Run XT", "入耳式", 399, "pnc"),
            ],
        },
        {
            "brand": "Sanag",
            "lines": [
                ("A30S Pro", "骨传导", 199, "none"),
                ("A50S", "骨传导", 299, "none"),
                ("Z65 Pro", "耳挂式", 149, "none"),
            ],
        },
        {
            "brand": "Haylou",
            "lines": [
                ("PurFree BC01", "骨传导", 399, "none"),
                ("PurFree Lite", "骨传导", 249, "none"),
            ],
        },
    ],
    "游戏": [
        {
            "brand": "雷蛇",
            "lines": [
                ("BlackShark V2 X", "头戴式", 299, "pnc"),
                ("BlackShark V2 Pro", "头戴式", 799, "pnc"),
                ("Hammerhead True Wireless X", "入耳式", 299, "tnc"),
                ("Hammerhead Pro HyperSpeed", "入耳式", 699, "anc"),
                ("Opus X", "头戴式", 499, "anc"),
                ("Kraken V4", "头戴式", 599, "pnc"),
            ],
        },
        {
            "brand": "罗技",
            "lines": [
                ("G435 无线", "头戴式", 299, "pnc"),
                ("G733 无线", "头戴式", 499, "pnc"),
                ("G Pro X 2 无线", "头戴式", 999, "pnc"),
                ("G Fits", "入耳式", 599, "anc"),
            ],
        },
        {
            "brand": "HyperX",
            "lines": [
                ("Cloud Stinger 2", "头戴式", 199, "pnc"),
                ("Cloud Alpha 无线", "头戴式", 799, "pnc"),
                ("Cloud III 无线", "头戴式", 699, "pnc"),
                ("Cloud MIX Buds", "入耳式", 499, "anc"),
            ],
        },
        {
            "brand": "赛睿",
            "lines": [
                ("Arctis Nova 1", "头戴式", 299, "pnc"),
                ("Arctis Nova 3", "头戴式", 399, "pnc"),
                ("Arctis Nova 7 无线", "头戴式", 899, "anc"),
                ("Arctis Nova Pro 无线", "头戴式", 1799, "anc"),
            ],
        },
        {
            "brand": "西伯利亚",
            "lines": [
                ("S21 无线", "头戴式", 149, "pnc"),
                ("S25 无线", "头戴式", 199, "pnc"),
                ("X36 无线", "头戴式", 299, "pnc"),
                ("YMIR 2", "头戴式", 399, "pnc"),
            ],
        },
    ],
    "其他": [
        {
            "brand": "OPPO",
            "lines": [
                ("Enco Air3", "入耳式", 149, "pnc"),
                ("Enco Air3 Pro", "入耳式", 249, "anc"),
                ("Enco X3", "入耳式", 699, "anc"),
                ("Enco Free3", "入耳式", 399, "anc"),
            ],
        },
        {
            "brand": "vivo",
            "lines": [
                ("TWS 3e", "入耳式", 149, "pnc"),
                ("TWS 3 Pro", "入耳式", 299, "anc"),
                ("TWS Air", "入耳式", 99, "pnc"),
            ],
        },
        {
            "brand": "魅族",
            "lines": [
                ("PANDAER 真无线", "入耳式", 199, "anc"),
                ("POP5 Pro", "入耳式", 299, "anc"),
                ("HD60 ANC", "头戴式", 249, "anc"),
            ],
        },
        {
            "brand": "realme",
            "lines": [
                ("Buds Air 5", "入耳式", 149, "anc"),
                ("Buds Air 5 Pro", "入耳式", 299, "anc"),
                ("Buds T300", "入耳式", 99, "tnc"),
            ],
        },
        {
            "brand": "Nothing",
            "lines": [
                ("Ear (2)", "入耳式", 799, "anc"),
                ("Ear (a)", "入耳式", 399, "anc"),
                ("CMF Buds Pro", "入耳式", 199, "anc"),
            ],
        },
        {
            "brand": "飞利浦",
            "lines": [
                ("TAT2556", "入耳式", 149, "pnc"),
                ("TAT3509", "入耳式", 299, "anc"),
                ("TAH8506", "头戴式", 599, "anc"),
                ("TAH5209", "头戴式", 299, "anc"),
            ],
        },
        {
            "brand": "松下",
            "lines": [
                ("RZ-S500W", "入耳式", 599, "anc"),
                ("RZ-B310W", "入耳式", 199, "pnc"),
                ("RB-M700B", "头戴式", 499, "anc"),
            ],
        },
        {
            "brand": "Beats",
            "lines": [
                ("Fit Pro", "入耳式", 899, "anc"),
                ("Studio Buds+", "入耳式", 999, "anc"),
                ("Studio Pro", "头戴式", 1199, "anc"),
                ("Powerbeats Pro", "耳挂式", 1199, "pnc"),
                ("Solo 4", "头戴式", 999, "pnc"),
            ],
        },
        {
            "brand": "Marshall",
            "lines": [
                ("Minor IV", "入耳式", 699, "pnc"),
                ("Motif II ANC", "入耳式", 999, "anc"),
                ("Monitor II ANC", "头戴式", 1699, "anc"),
                ("Major V", "头戴式", 799, "pnc"),
            ],
        },
    ],
}

# ---------------------------------------------------------------------------
# Feature pools
# ---------------------------------------------------------------------------

FEATURES_POOL = {
    "降噪": ["主动降噪", "混合降噪", "深度降噪", "智能降噪", "通话降噪", "环境音模式", "自适应降噪"],
    "音质": ["LDAC", "Hi-Res认证", "LHDC", "aptX", "AAC", "SBC", "空间音频", "低音增强", "高解析音频", "DSEE"],
    "连接": ["蓝牙5.0", "蓝牙5.2", "蓝牙5.3", "蓝牙5.4", "多点连接", "双设备连接", "NFC配对", "星闪连接"],
    "续航": [
        "6小时续航", "8小时续航", "10小时续航", "24小时续航", "30小时续航",
        "40小时续航", "50小时续航", "60小时续航", "无线充电", "快充10分钟听2小时",
    ],
    "防护": ["IPX4防水", "IPX5防水", "IP54防水防尘", "IP55防水", "IPX7防水"],
    "佩戴": ["轻量设计", "可折叠", "记忆海绵耳塞", "鲨鱼鳍耳翼", "人体工学", "不入耳设计", "耳挂式", "半入耳"],
    "游戏": ["低延迟游戏模式", "7.1虚拟环绕", "RGB灯效", "可拆卸麦克风", "50mm大驱动单元"],
    "其他": ["触控操作", "语音助手", "找耳机功能", "佩戴检测", "多设备切换"],
}

SCENARIOS_POOL = ["通勤", "运动", "办公", "游戏", "日常", "飞行", "跑步", "骑行", "健身", "学习", "音乐", "会议"]

PLATFORMS = ["京东", "天猫", "拼多多"]
PLATFORM_WEIGHTS = [0.34, 0.33, 0.33]

# ---------------------------------------------------------------------------
# Description templates
# ---------------------------------------------------------------------------

DESC_TEMPLATES = [
    "{brand}{model}，{feat1}与{feat2}完美融合，{scene}场景的绝佳选择。",
    "主打{feat1}的{type}耳机，{feat2}加持，{scene}族的得力助手。",
    "{price_tier}价位标杆之作，{feat1}表现出色，{scene}和{scene2}两相宜。",
    "采用{feat1}技术，{feat2}持久续航，专为{scene}打造。",
    "{brand}旗下人气机型，{feat1}效果业界领先，{scene}好评如潮。",
    "轻盈{type}设计，{feat1}带来沉浸体验，{scene}利器。",
    "{feat1}加{feat2}双保障，音质细腻，{scene}场景游刃有余。",
    "性价比之选，{feat1}达到更高价位水准，学生党和{scene}族必备。",
    "{brand}经典{type}，{feat1}音质媲美专业设备，发烧友的{scene}伴侣。",
    "搭载{feat1}，{feat2}保驾护航，满足{scene}与{scene2}多场景需求。",
    "旗舰{feat1}体验，全天{feat2}续航，出行{scene}首选。",
    "百元级惊喜，{feat1}效果超越预期，{scene}入门不将就。",
    "专业{scene}耳机，{feat1}精准定位，竞技玩家的胜负关键。",
    "骨传导新选择，不堵耳感知周围，{scene}安全无忧。",
    "{feat1}技术加持，{feat2}连接稳定，{scene}时光高品质享受。",
]

PRICE_TIER_LABELS = {
    (0, 100): "超百元内",
    (100, 200): "百元级",
    (200, 300): "入门级",
    (300, 500): "中端",
    (500, 800): "中高端",
    (800, 1200): "高端",
    (1200, 2000): "旗舰级",
    (2000, 9999): "超旗舰",
}

def get_price_tier(price):
    for (lo, hi), label in PRICE_TIER_LABELS.items():
        if lo <= price < hi:
            return label
    return "旗舰级"


def pick_nc(nc_profile, headphone_type, price):
    """Determine noise_cancellation field."""
    if headphone_type in ("骨传导", "耳挂式"):
        return "无"
    if nc_profile == "anc":
        if price < 150:
            return random.choice(["通话降噪", "被动降噪"])
        return "主动降噪"
    if nc_profile == "tnc":
        return "通话降噪"
    if nc_profile == "pnc":
        if price >= 300:
            # some pnc products upgraded to ANC at mid range
            return random.choice(["被动降噪", "被动降噪", "通话降噪"])
        return "被动降噪"
    # none
    if price < 100:
        return random.choice(["无", "被动降噪"])
    return "无"


def pick_features(headphone_type, price, nc_val, brand, n=3):
    """Pick realistic features for a product."""
    pool = []

    # Always add a bluetooth version
    if headphone_type not in ("骨传导",):
        if price >= 800:
            pool.append(random.choice(["蓝牙5.3", "蓝牙5.4"]))
        elif price >= 300:
            pool.append(random.choice(["蓝牙5.2", "蓝牙5.3"]))
        else:
            pool.append(random.choice(["蓝牙5.0", "蓝牙5.2"]))

    # Noise-cancellation feature tag
    if nc_val == "主动降噪":
        pool.extend(random.sample(["主动降噪", "混合降噪", "深度降噪", "智能降噪", "自适应降噪", "环境音模式"], 2))
    elif nc_val == "通话降噪":
        pool.append("通话降噪")
    elif nc_val == "被动降噪":
        pool.append(random.choice(["记忆海绵耳塞", "人体工学", "被动隔音"]))

    # Audio codec
    if price >= 1000:
        pool.extend(random.sample(["LDAC", "Hi-Res认证", "空间音频", "LHDC", "DSEE"], 2))
    elif price >= 500:
        pool.append(random.choice(["LDAC", "aptX", "AAC", "空间音频"]))
    else:
        pool.append(random.choice(["AAC", "SBC", "aptX"]))

    # Battery
    if headphone_type == "头戴式":
        if price >= 800:
            pool.append(random.choice(["30小时续航", "40小时续航", "无线充电"]))
        else:
            pool.append(random.choice(["24小时续航", "30小时续航"]))
    elif headphone_type in ("骨传导", "耳挂式"):
        pool.append(random.choice(["8小时续航", "10小时续航", "12小时续航"]))
    else:
        if price >= 500:
            pool.append(random.choice(["8小时续航", "无线充电", "快充10分钟听2小时"]))
        else:
            pool.append(random.choice(["6小时续航", "8小时续航", "快充10分钟听2小时"]))

    # Waterproof (earbuds/sport more likely)
    if headphone_type in ("入耳式", "骨传导", "耳挂式"):
        pool.append(random.choice(["IPX4防水", "IPX5防水", "IP54防水防尘"]))

    # Open ear special
    if headphone_type in ("骨传导", "耳挂式"):
        pool.append(random.choice(["不入耳设计", "轻量设计", "人体工学"]))

    # Gaming extras
    if brand in ("雷蛇", "罗技", "HyperX", "赛睿", "西伯利亚"):
        pool.extend(random.sample(["低延迟游戏模式", "7.1虚拟环绕", "RGB灯效", "可拆卸麦克风", "50mm大驱动单元"], 2))

    # Misc
    pool.append(random.choice(["触控操作", "语音助手", "多设备切换", "佩戴检测", "多点连接"]))

    # Deduplicate and cap
    seen = set()
    result = []
    for f in pool:
        if f not in seen:
            seen.add(f)
            result.append(f)
    if len(result) < n:
        extras = [f for cat in FEATURES_POOL.values() for f in cat if f not in seen]
        random.shuffle(extras)
        for f in extras:
            result.append(f)
            seen.add(f)
            if len(result) >= n:
                break
    return result[:max(n, 3)]


def pick_scenarios(headphone_type, brand, price):
    """Pick 2 realistic scenarios with broader distribution."""
    if brand in ("雷蛇", "罗技", "HyperX", "赛睿", "西伯利亚"):
        return random.sample(["游戏", "日常", "音乐", "学习"], 2)
    if headphone_type in ("骨传导", "耳挂式"):
        return random.sample(["运动", "跑步", "骑行", "健身", "通勤", "日常"], 2)
    if price >= 1200:
        return random.sample(["飞行", "音乐", "通勤", "办公", "日常"], 2)
    # General: sample from full pool for even distribution
    return random.sample(SCENARIOS_POOL, 2)


def make_description(brand, model, headphone_type, price, features, scenarios, nc_val):
    tmpl = random.choice(DESC_TEMPLATES)
    tier = get_price_tier(price)
    feat1 = features[0] if features else "高品质音质"
    feat2 = features[1] if len(features) > 1 else "长续航"
    scene = scenarios[0] if scenarios else "日常"
    scene2 = scenarios[1] if len(scenarios) > 1 else "通勤"

    desc = tmpl.format(
        brand=brand,
        model=model,
        type=headphone_type,
        feat1=feat1,
        feat2=feat2,
        scene=scene,
        scene2=scene2,
        price_tier=tier,
    )
    # Ensure 30-60 chars
    if len(desc) < 30:
        desc += f"，是{scene}场景的理想之选，音质表现令人满意。"
    if len(desc) > 60:
        desc = desc[:58] + "。"
    return desc


# ---------------------------------------------------------------------------
# Collect all product line templates
# ---------------------------------------------------------------------------

ALL_LINES = []  # list of (brand, model, type, base_price, nc_profile)
for tier_brands in BRANDS.values():
    for brand_info in tier_brands:
        brand = brand_info["brand"]
        for line in brand_info["lines"]:
            model_suffix, htype, base_price, nc_profile = line
            ALL_LINES.append((brand, model_suffix, htype, base_price, nc_profile))

# ---------------------------------------------------------------------------
# Type-aware sampling weights
# ---------------------------------------------------------------------------
# Give higher weight to underrepresented types (骨传导, 耳挂式)
TYPE_WEIGHT = {"入耳式": 1.0, "头戴式": 1.0, "骨传导": 2.5, "耳挂式": 2.5}
LINE_WEIGHTS = [TYPE_WEIGHT.get(line[2], 1.0) for line in ALL_LINES]

# ---------------------------------------------------------------------------
# Price jitter helpers to hit distribution targets
# ---------------------------------------------------------------------------

PRICE_BUCKETS = [
    (50, 100, 90),
    (100, 200, 240),
    (200, 300, 240),
    (300, 500, 300),
    (500, 800, 240),
    (800, 1200, 180),
    (1200, 2000, 150),
    (2000, 5000, 60),
]

def jitter_price(base_price):
    """Add small random variation to base price (±12%) and round to nice number."""
    factor = random.uniform(0.88, 1.12)
    raw = base_price * factor
    # Round to nearest 10
    rounded = round(raw / 10) * 10
    return max(50, rounded)


def assign_to_bucket(price):
    for lo, hi, _ in PRICE_BUCKETS:
        if lo <= price < hi:
            return (lo, hi)
    return (2000, 5000)


# ---------------------------------------------------------------------------
# Generate 1500 products
# ---------------------------------------------------------------------------

TARGET = 1500
products = []
idx = 1

bucket_counts = {(lo, hi): 0 for lo, hi, _ in PRICE_BUCKETS}
bucket_targets = {(lo, hi): t for lo, hi, t in PRICE_BUCKETS}

attempts = 0
max_attempts = 60000

rng_enrich = random.Random(123)  # separate RNG for stock/prices

while len(products) < TARGET and attempts < max_attempts:
    attempts += 1
    brand, model, htype, base_price, nc_profile = random.choices(ALL_LINES, weights=LINE_WEIGHTS, k=1)[0]

    price = jitter_price(base_price)
    bucket = assign_to_bucket(price)

    # Soft-enforce bucket targets: skip if bucket already over-full
    if bucket_counts[bucket] >= bucket_targets[bucket] * 1.3:
        continue

    nc_val = pick_nc(nc_profile, htype, price)
    features = pick_features(htype, price, nc_val, brand, n=random.randint(3, 5))
    scenarios = pick_scenarios(htype, brand, price)
    desc = make_description(brand, model, htype, price, features, scenarios, nc_val)

    rating = round(random.uniform(3.8, 4.9), 1)
    platform = random.choices(PLATFORMS, weights=PLATFORM_WEIGHTS, k=1)[0]

    # Stock and cross-platform prices (previously in enrich_products.py)
    stock = rng_enrich.randint(0, 100)
    other_platforms = [pl for pl in PLATFORMS if pl != platform]
    other_prices = {}
    for pl in other_platforms:
        multiplier = rng_enrich.uniform(0.85, 1.15)
        other_prices[pl] = round(int(price) * multiplier)

    product = {
        "id": f"hp_{idx:03d}",
        "name": f"{brand} {model} {htype}耳机",
        "category": "耳机",
        "type": htype,
        "brand": brand,
        "price": int(price),
        "platform": platform,
        "rating": rating,
        "features": features,
        "scenario": scenarios,
        "noise_cancellation": nc_val,
        "description": desc,
        "stock": stock,
        "other_platform_prices": other_prices,
    }
    products.append(product)
    bucket_counts[bucket] += 1
    idx += 1

# If somehow we're short, fill up without bucket restrictions
while len(products) < TARGET:
    brand, model, htype, base_price, nc_profile = random.choices(ALL_LINES, weights=LINE_WEIGHTS, k=1)[0]
    price = jitter_price(base_price)
    nc_val = pick_nc(nc_profile, htype, price)
    features = pick_features(htype, price, nc_val, brand, n=random.randint(3, 5))
    scenarios = pick_scenarios(htype, brand, price)
    desc = make_description(brand, model, htype, price, features, scenarios, nc_val)
    rating = round(random.uniform(3.8, 4.9), 1)
    platform = random.choices(PLATFORMS, weights=PLATFORM_WEIGHTS, k=1)[0]
    stock = rng_enrich.randint(0, 100)
    other_platforms = [pl for pl in PLATFORMS if pl != platform]
    other_prices = {}
    for pl in other_platforms:
        multiplier = rng_enrich.uniform(0.85, 1.15)
        other_prices[pl] = round(int(price) * multiplier)
    product = {
        "id": f"hp_{idx:03d}",
        "name": f"{brand} {model} {htype}耳机",
        "category": "耳机",
        "type": htype,
        "brand": brand,
        "price": int(price),
        "platform": platform,
        "rating": rating,
        "features": features,
        "scenario": scenarios,
        "noise_cancellation": nc_val,
        "description": desc,
        "stock": stock,
        "other_platform_prices": other_prices,
    }
    products.append(product)
    idx += 1

# Trim to exactly TARGET just in case
products = products[:TARGET]

# Re-assign IDs sequentially (use 4-digit for 1500)
for i, p in enumerate(products, start=1):
    p["id"] = f"hp_{i:04d}"

# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------

output_path = os.path.join(os.path.dirname(__file__), "..", "data", "products.json")
output_path = os.path.normpath(output_path)

os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

print(f"Written {len(products)} products to {output_path}")

# Quick stats
from collections import Counter
bucket_summary = Counter()
for p in products:
    b = assign_to_bucket(p["price"])
    bucket_summary[b] += 1

print("\nPrice bucket distribution:")
for lo, hi, target in PRICE_BUCKETS:
    count = bucket_summary.get((lo, hi), 0)
    print(f"  {lo:>5}-{hi:<5}: {count:>3} (target {target})")

brands_found = set(p["brand"] for p in products)
print(f"\nBrands represented: {len(brands_found)}")
types_c = Counter(p["type"] for p in products)
print("Type distribution:", dict(types_c))
nc_c = Counter(p["noise_cancellation"] for p in products)
print("Noise cancellation:", dict(nc_c))
scenario_c = Counter()
for p in products:
    for s in p["scenario"]:
        scenario_c[s] += 1
print("Scenario distribution:", dict(scenario_c.most_common()))
platform_c = Counter(p["platform"] for p in products)
print("Platform distribution:", dict(platform_c))
