"""L8 多步交互合理性测试 — 验证多轮对话中每一步返回内容的语义合理性。

覆盖验证点：
  V1  预算硬过滤
  V7  五维度全部询问后才搜索
  V8  推荐恰好 3 款
  V9  price_comparison 值为整数
  V11 每步只问一个问题
  V12 不重复提问已回答信息
  V13 推荐字段完整
  V14 订单确认不调用 place_order
  V15 中途改需求后重新搜索且结果在新预算内

重要：LLM 输出有不确定性，断言检查语义而非具体措辞。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from api.services.agent_service import agent_service

# ─── 共用工具函数 ────────────────────────────────────────────────────────────

def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(kw in text for kw in keywords)

def _tool_names(result: dict) -> list[str]:
    return [s["tool"] for s in result.get("thinking_steps", [])]

# ─── 场景 A：标准 5 轮澄清流程 ───────────────────────────────────────────────

def test_scenario_a_standard_5round_clarification():
    """场景A: 标准5轮逐步澄清 → 第6轮必须触发搜索。

    覆盖: V7(5维度后搜索), V11(每步只问一个问题), V12(不重复提问)
    """
    history = []
    decisions = {}

    # ── 第1轮：模糊需求 ──
    r1 = agent_service.chat("我想买个耳机", history, "ollama")

    assert r1["stage"] in ["意图澄清", "未知"], (
        f"第1轮 stage 应为'意图澄清'，实际: {r1['stage']!r}"
    )
    assert r1["thinking_steps"] == [], "第1轮不应调用工具"
    assert len(r1["text"]) > 5, "第1轮回复不能为空"
    # 不应跳阶段
    assert not _contains_any(r1["text"], ["推荐", "下单"]), (
        f"第1轮不应提到推荐或下单，实际: {r1['text'][:200]}"
    )
    # 第一优先级：问某个维度（理想是预算，但 LLM 随机性允许问类型/场景等）
    DIMENSION_KW = ["预算", "价格", "多少钱", "价位", "多少", "类型", "入耳", "头戴", "场景", "用途", "降噪", "品牌"]
    assert _contains_any(r1["text"], DIMENSION_KW), (
        f"第1轮应问某个需求维度，实际: {r1['text'][:200]}"
    )
    # V11: 不应在一条回复中提出多个独立问题（通过问号数量检测）
    # 允许列举选项（比如 "入耳式/头戴式/骨传导"），但不允许多个问句并列
    question_count = r1["text"].count("？") + r1["text"].count("?")
    assert question_count <= 2, (
        f"V11: 第1轮不应包含多个问句（共{question_count}个问号）: {r1['text'][:200]}"
    )

    history += [{"role": "user", "content": "我想买个耳机"},
                {"role": "assistant", "content": r1["reply"]}]

    # ── 第2轮：回答预算 ──
    decisions["budget"] = "≤¥500"
    r2 = agent_service.chat("500以内", history, "ollama", user_decisions=decisions)

    assert r2["stage"] in ["意图澄清", "未知"], (
        f"第2轮 stage 应为'意图澄清'，实际: {r2['stage']!r}"
    )
    assert r2["thinking_steps"] == [], "第2轮不应调用工具"
    # V12: 不应重复以问句形式询问预算（允许复述预算作为确认）
    assert "预算大概是多少" not in r2["text"] and "价格大概是多少" not in r2["text"], (
        f"V12: 第2轮已回答预算，不应以问句形式再次询问，实际: {r2['text'][:200]}"
    )
    # 应继续问某个未回答的维度（类型/场景/降噪/品牌均可）
    assert _contains_any(r2["text"], ["类型", "入耳", "头戴", "场景", "用途", "骨传导", "耳挂", "降噪", "品牌", "牌子"]), (
        f"第2轮应询问某个需求维度，实际: {r2['text'][:200]}"
    )

    history += [{"role": "user", "content": "500以内"},
                {"role": "assistant", "content": r2["reply"]}]

    # ── 第3轮：回答类型 ──
    r3 = agent_service.chat("入耳式", history, "ollama", user_decisions=decisions)

    assert r3["stage"] in ["意图澄清", "未知"], (
        f"第3轮 stage 应为'意图澄清'，实际: {r3['stage']!r}"
    )
    assert r3["thinking_steps"] == [], "第3轮不应调用工具"
    # V12: 不应再以问句形式询问预算
    assert "预算大概是多少" not in r3["text"] and "价格大概是多少" not in r3["text"], (
        f"V12: 第3轮已回答预算，不应再以问句形式询问，实际: {r3['text'][:200]}"
    )
    # V12: 不应反问已确认的类型
    assert "入耳式还是" not in r3["text"], (
        f"V12: 不应反问已确认的类型，实际: {r3['text'][:200]}"
    )
    # 应继续问下一个维度
    assert _contains_any(r3["text"], ["场景", "用途", "通勤", "运动", "办公", "降噪", "品牌", "使用"]), (
        f"第3轮应询问使用场景或降噪，实际: {r3['text'][:200]}"
    )

    history += [{"role": "user", "content": "入耳式"},
                {"role": "assistant", "content": r3["reply"]}]
    decisions["type"] = "入耳式"

    # ── 第4轮：回答场景 ──
    r4 = agent_service.chat("通勤", history, "ollama", user_decisions=decisions)

    assert r4["stage"] in ["意图澄清", "未知"], (
        f"第4轮 stage 应为'意图澄清'，实际: {r4['stage']!r}"
    )
    assert r4["thinking_steps"] == [], "第4轮不应调用工具（还差降噪和品牌）"
    # 应问降噪或品牌，而非提前搜索
    assert _contains_any(r4["text"], ["降噪", "噪音", "品牌", "牌子", "偏好", "主动"]), (
        f"第4轮应询问降噪需求或品牌，实际: {r4['text'][:200]}"
    )

    history += [{"role": "user", "content": "通勤"},
                {"role": "assistant", "content": r4["reply"]}]
    decisions["scenario"] = "通勤"

    # ── 第5轮：回答降噪 ──
    r5 = agent_service.chat("需要降噪", history, "ollama", user_decisions=decisions)

    assert r5["stage"] in ["意图澄清", "未知"], (
        f"第5轮 stage 应为'意图澄清'，实际: {r5['stage']!r}"
    )
    assert r5["thinking_steps"] == [], "第5轮不应调用工具（还差品牌）"
    # 应问最后一个维度：品牌
    assert _contains_any(r5["text"], ["品牌", "牌子", "偏好", "品牌偏好", "哪个品牌", "厂商"]), (
        f"第5轮应询问品牌偏好，实际: {r5['text'][:200]}"
    )

    history += [{"role": "user", "content": "需要降噪"},
                {"role": "assistant", "content": r5["reply"]}]
    decisions["noise_cancellation"] = "需要降噪"

    # ── 第6轮：回答品牌 → 应触发搜索 ──
    r6 = agent_service.chat("没有偏好", history, "ollama", user_decisions=decisions)

    # V7: 5个维度全部回答，必须进入搜索/推荐阶段
    assert r6["stage"] != "意图澄清", (
        f"V7: 第6轮（5维度已全答）不应仍在'意图澄清'，实际: {r6['stage']!r}"
    )
    # 进入搜索准备状态（分析中/搜索中/推荐方案，或有 task_plan/thinking_steps）
    is_search_ready = (
        r6["stage"] in ["分析中", "搜索中", "推荐方案"]
        or r6.get("task_plan") is not None
        or len(r6["thinking_steps"]) > 0
        or _contains_any(r6["reply"], ["分析", "搜索", "推荐", "找到", "task_plan"])
    )
    assert is_search_ready, (
        f"V7: 第6轮应触发搜索，实际: stage={r6['stage']!r}, reply={r6['reply'][:200]}"
    )


# ─── 场景 G：不合理输入的容错 ────────────────────────────────────────────────

def test_scenario_g_fault_tolerance():
    """场景G: 不合理输入（无关话题/乱码）不崩溃，能引导回购物流程。"""

    # 无关话题
    r1 = agent_service.chat("今天天气怎么样", [], "ollama")
    assert r1["stage"] in ["意图澄清", "未知"], (
        f"天气话题 stage 应为意图澄清，实际: {r1['stage']!r}"
    )
    assert r1["thinking_steps"] == [], "无关输入不应调用工具"
    assert len(r1["text"]) > 0, "应有回复（引导回购物话题）"

    # 乱码/符号输入
    r2 = agent_service.chat("???", [], "ollama")
    assert r2["stage"] in ["意图澄清", "未知"], (
        f"符号输入 stage 应为意图澄清，实际: {r2['stage']!r}"
    )
    assert len(r2["text"]) > 0, "符号输入应有回复"

    # 空有效内容
    r3 = agent_service.chat("啊", [], "ollama")
    assert r3["stage"] in ["意图澄清", "未知"], (
        f"单字输入 stage 应为意图澄清，实际: {r3['stage']!r}"
    )
    assert len(r3["text"]) > 0, "单字输入应有回复"


# ─── 场景 B：用户一次性给出多个信息 ─────────────────────────────────────────

def test_scenario_b_multi_info_in_one_message():
    """场景B: 用户第一句包含多个信息，AI 应跳过已知维度，只问品牌。

    覆盖: V12(不重复提问已回答信息)
    """
    r = agent_service.chat(
        "帮我找一款500以内的入耳式降噪耳机，通勤用", [], "ollama"
    )

    # V12: 预算/类型/场景/降噪都给了，不应以问句形式再次询问这些
    text = r["text"]
    # 检测是否以问句形式重复询问预算
    assert "预算大概是多少" not in text and "价格大概是多少" not in text, (
        f"V12: 预算已给出，不应再以问句形式询问，实际: {text[:200]}"
    )
    # 不应重复问类型
    assert "什么类型" not in text and "入耳还是" not in text, (
        f"V12: 类型已给出，不应再问，实际: {text[:200]}"
    )
    # 不应重复问场景
    assert "通勤还是" not in text and "使用场景是什么" not in text, (
        f"V12: 场景已给出，不应再问，实际: {text[:200]}"
    )
    # 允许两种情况：① 问品牌（只缺品牌）② 直接进入分析/搜索（4维度已足够）
    is_ok = (
        _contains_any(text, ["品牌", "牌子", "偏好", "哪个品牌", "厂商", "国产", "进口"])
        or r["stage"] in ["分析中", "搜索中", "推荐方案"]
        or len(r["thinking_steps"]) > 0
        or r.get("task_plan") is not None
    )
    assert is_ok, (
        f"场景B: 应询问品牌或直接进入搜索，实际: stage={r['stage']!r}, text={text[:200]}"
    )


# ─── 场景 C：多选回答的合理处理 ──────────────────────────────────────────────

def test_scenario_c_multi_select_answer():
    """场景C: 用户回答"头戴式+入耳式"多选，AI 不应重复问类型，应继续下一维度。

    覆盖: V12(不重复提问)
    """
    history = [
        {"role": "user", "content": "帮我找一款耳机"},
        {"role": "assistant", "content": "[意图澄清] 您的预算大概是多少？"},
        {"role": "user", "content": "500-1000"},
        {"role": "assistant", "content": "[意图澄清] 您想要什么类型的耳机？"},
    ]

    r = agent_service.chat(
        "头戴式 + 入耳式都可以",
        history,
        "ollama",
        user_decisions={"budget": "¥500-1000"},
    )

    assert r["stage"] in ["意图澄清", "未知"], (
        f"场景C: 还缺其他维度，stage 应为意图澄清，实际: {r['stage']!r}"
    )
    # V12: 不应重复问类型
    text = r["text"]
    assert "入耳还是头戴" not in text, (
        f"V12: 不应重复问类型（入耳还是头戴），实际: {text[:200]}"
    )
    assert "什么类型" not in text, (
        f"V12: 不应重复问类型（什么类型），实际: {text[:200]}"
    )
    # 应继续问下一个维度
    assert _contains_any(text, ["场景", "用途", "降噪", "品牌", "通勤", "运动", "使用"]), (
        f"场景C: 应继续问下一维度，实际: {text[:200]}"
    )


# ─── 场景 D：推荐结果的合理性验证 ────────────────────────────────────────────

# 模块级推荐结果缓存（供场景 E/F/H 复用）
_scenario_d_result: dict | None = None
_scenario_d_history: list | None = None
_scenario_d_decisions: dict | None = None


def test_scenario_d_recommendation_quality():
    """场景D: 触发推荐后验证 structured_data 字段完整性和合理性。

    覆盖: V1(预算过滤), V8(恰好3款), V13(字段完整)
    """
    global _scenario_d_result, _scenario_d_history, _scenario_d_decisions

    history = [
        {"role": "user", "content": "帮我找500以内入耳式降噪耳机通勤用"},
        {"role": "assistant", "content": "[意图澄清] 品牌有偏好吗？"},
        {"role": "user", "content": "国产优先"},
        {"role": "assistant", "content": "[意图澄清] 需要降噪功能吗？"},
        {"role": "user", "content": "需要"},
    ]
    decisions = {
        "budget": "≤¥500",
        "type": "入耳式",
        "scenario": "通勤",
        "brand_preference": "国产优先",
        "noise_cancellation": "需要降噪",
    }

    r = agent_service.chat("开始搜索吧", history, "ollama", user_decisions=decisions)

    # 保存供后续场景使用
    _scenario_d_result = r
    _scenario_d_history = history
    _scenario_d_decisions = decisions

    # 应进入搜索/推荐阶段
    assert r["stage"] != "意图澄清", (
        f"场景D: 5维度完整，不应仍在意图澄清，stage={r['stage']!r}"
    )

    sd = r.get("structured_data")
    if sd and sd.get("type") == "recommendation":
        # V8: 恰好 3 款
        products = sd.get("products", [])
        assert len(products) == 3, (
            f"V8: 推荐应恰好 3 款，实际 {len(products)} 款"
        )

        for p in products:
            # V1: 不超预算
            assert p["price"] <= 500, (
                f"V1: 商品「{p.get('name')}」价格 {p['price']} 超过预算 500"
            )
            assert p["price"] > 0, f"价格应为正数，实际: {p['price']}"
            assert isinstance(p["price"], int), (
                f"价格应为整数，实际类型: {type(p['price']).__name__}"
            )

            # V13: 字段完整性
            assert p.get("name"), f"V13: name 字段不能为空"
            assert p.get("brand"), f"V13: brand 字段不能为空"
            assert p.get("platform") in ["京东", "天猫", "拼多多"], (
                f"V13: platform 值非法: {p.get('platform')}"
            )
            rating = p.get("rating", 0)
            assert 1.0 <= rating <= 5.0, f"V13: rating 应在 1-5 之间: {rating}"
            assert len(p.get("pros", [])) >= 1, "V13: pros 不能为空"
            assert len(p.get("cons", [])) >= 1, "V13: cons 不能为空"
            assert p.get("reason"), "V13: reason 不能为空"

        # rank 连续 [1, 2, 3]
        ranks = [p["rank"] for p in products]
        assert ranks == [1, 2, 3], f"rank 应为 [1,2,3]，实际: {ranks}"

        # decision_process
        dp = sd.get("decision_process", {})
        assert dp.get("total_products", 0) > 0, "decision_process.total_products 应大于 0"
        assert dp.get("retrieved", 0) > 0, "decision_process.retrieved 应大于 0"
        assert dp.get("final_candidates") == 3, (
            f"decision_process.final_candidates 应为 3，实际: {dp.get('final_candidates')}"
        )
        assert dp.get("primary_criterion"), "decision_process.primary_criterion 不能为空"

        # user_profile 回显
        up = sd.get("user_profile", {})
        assert "500" in str(up.get("budget", "")), (
            f"user_profile.budget 应含 '500'，实际: {up.get('budget')}"
        )
        assert "入耳" in str(up.get("type", "")), (
            f"user_profile.type 应含 '入耳'，实际: {up.get('type')}"
        )

        # verdict
        verdict = sd.get("verdict", "")
        assert verdict, "verdict 不能为空"
        assert len(verdict) >= 10, f"verdict 不能太短（<10字），实际: {verdict!r}"

        # comparisons
        comparisons = sd.get("comparisons", {})
        if comparisons:
            for key, values in comparisons.items():
                assert len(values) == 3, (
                    f"comparisons[{key!r}] 应有 3 个值，实际 {len(values)} 个"
                )
    else:
        # 如果没有推荐结果（LLM 只输出了分析阶段），跳过字段验证
        # 但必须记录 thinking_steps（说明确实调用了工具）
        assert len(r["thinking_steps"]) > 0 or r.get("task_plan") is not None, (
            f"场景D: 应调用工具或生成 task_plan，实际: stage={r['stage']!r}"
        )


# ─── 场景 E：订单确认的合理性验证 ────────────────────────────────────────────

def test_scenario_e_order_confirm_quality():
    """场景E: 用户选择商品后进入订单确认阶段，验证字段一致性。

    覆盖: V9(price_comparison整数), V14(不调用place_order)
    """
    global _scenario_d_result, _scenario_d_history, _scenario_d_decisions

    # 如果场景D没有运行或没有推荐结果，重新触发
    if (
        _scenario_d_result is None
        or _scenario_d_result.get("structured_data", {}) is None
        or _scenario_d_result["structured_data"].get("type") != "recommendation"
    ):
        pytest.skip("场景E依赖场景D的推荐结果，场景D未产生推荐，跳过")

    r_rec = _scenario_d_result
    sd = r_rec["structured_data"]
    chosen = sd["products"][0]
    decisions = _scenario_d_decisions

    history_full = _scenario_d_history + [
        {"role": "user", "content": "开始搜索吧"},
        {"role": "assistant", "content": r_rec["reply"]},
    ]

    r_order = agent_service.chat(
        f"我选择 {chosen['name']}，帮我下单{chosen['platform']}的",
        history_full,
        "ollama",
        user_decisions=decisions,
    )

    # 阶段验证
    assert r_order["stage"] == "订单确认", (
        f"场景E: stage 应为'订单确认'，实际: {r_order['stage']!r}"
    )
    oc_sd = r_order.get("structured_data")
    assert oc_sd is not None, "场景E: structured_data 不能为空"
    assert oc_sd.get("type") == "order_confirm", (
        f"场景E: structured_data.type 应为'order_confirm'，实际: {oc_sd.get('type')}"
    )

    oc = oc_sd

    # 订单信息一致性（V6: 缓存覆盖保证价格一致）
    assert oc.get("product") == chosen["name"], (
        f"订单商品名应与推荐一致，期望: {chosen['name']!r}，实际: {oc.get('product')!r}"
    )
    assert oc.get("price") == chosen["price"], (
        f"订单价格应与推荐一致，期望: {chosen['price']}，实际: {oc.get('price')}"
    )
    assert oc.get("platform") == chosen["platform"], (
        f"订单平台应与推荐一致，期望: {chosen['platform']!r}，实际: {oc.get('platform')!r}"
    )

    # V9: price_comparison 格式
    pc = oc.get("price_comparison", {})
    if pc:
        assert len(pc) >= 2, f"price_comparison 应至少有 2 个平台，实际: {len(pc)}"
        for platform, price in pc.items():
            assert isinstance(price, int), (
                f"V9: price_comparison[{platform!r}] 应为整数，实际: {price!r} ({type(price).__name__})"
            )
            assert price > 0, f"price_comparison 价格应大于 0，实际: {price}"
            assert platform in ["京东", "天猫", "拼多多"], (
                f"price_comparison 平台值非法: {platform!r}"
            )

    # delivery 字段
    assert oc.get("delivery"), "delivery 字段不能为空"

    # V14: 订单确认阶段不应调用 place_order
    tool_names = _tool_names(r_order)
    assert "place_order" not in tool_names, (
        f"V14: 订单确认阶段不应调用 place_order，实际 tools: {tool_names}"
    )

    # 保存供场景F使用
    global _scenario_e_result, _scenario_e_history, _scenario_e_chosen
    _scenario_e_result = r_order
    _scenario_e_history = history_full
    _scenario_e_chosen = chosen


# ─── 场景 F：下单完成的合理性验证 ────────────────────────────────────────────

_scenario_e_result: dict | None = None
_scenario_e_history: list | None = None
_scenario_e_chosen: dict | None = None


def test_scenario_f_order_complete():
    """场景F: 用户确认下单后，stage 应为'下单完成'，必须调用 place_order。

    覆盖: V14(确认后调用place_order)
    """
    global _scenario_e_result, _scenario_e_history, _scenario_e_chosen, _scenario_d_decisions

    if _scenario_e_result is None or _scenario_e_chosen is None:
        pytest.skip("场景F依赖场景E的订单确认结果，场景E未完成，跳过")

    chosen = _scenario_e_chosen
    history_order = _scenario_e_history + [
        {"role": "user", "content": f"我选择 {chosen['name']}"},
        {"role": "assistant", "content": _scenario_e_result["reply"]},
    ]

    r_done = agent_service.chat(
        "确认下单",
        history_order,
        "ollama",
        user_decisions=_scenario_d_decisions,
    )

    # 阶段验证
    assert r_done["stage"] == "下单完成", (
        f"场景F: stage 应为'下单完成'，实际: {r_done['stage']!r}"
    )

    # V14: 确认下单后必须调用 place_order
    tool_names = _tool_names(r_done)
    assert "place_order" in tool_names, (
        f"V14: 确认下单后必须调用 place_order，实际 tools: {tool_names}"
    )

    # 回复应包含订单号
    assert "订单号" in r_done["text"], (
        f"场景F: 回复应包含'订单号'，实际: {r_done['text'][:200]}"
    )

    # 提及商品名或"成功"
    assert (chosen["name"][:4] in r_done["text"] or "成功" in r_done["text"]), (
        f"场景F: 回复应提及商品名或成功，实际: {r_done['text'][:200]}"
    )


# ─── 场景 H：中途改需求后推荐内容更新 ───────────────────────────────────────

def test_scenario_h_change_requirement_mid_flow():
    """场景H: 推荐后用户放宽预算，AI 应重新搜索，新推荐在新预算内。

    覆盖: V15(改需求后重新搜索且结果在新预算内)
    """
    global _scenario_d_result, _scenario_d_history, _scenario_d_decisions

    if (
        _scenario_d_result is None
        or _scenario_d_result.get("structured_data", {}) is None
        or _scenario_d_result["structured_data"].get("type") != "recommendation"
    ):
        pytest.skip("场景H依赖场景D的推荐结果（500以内），场景D未产生推荐，跳过")

    r6 = _scenario_d_result
    sd = r6["structured_data"]
    old_products = sd["products"]

    # 验证原推荐在 500 以内
    old_max_price = max(p["price"] for p in old_products)
    assert old_max_price <= 500, f"场景H前提：原推荐最高价应 ≤500，实际: {old_max_price}"

    # 构造改需求的历史
    history_change = _scenario_d_history + [
        {"role": "user", "content": "开始搜索吧"},
        {"role": "assistant", "content": r6["reply"]},
    ]
    new_decisions = dict(_scenario_d_decisions)
    new_decisions["budget"] = "≤¥1000"

    r_change = agent_service.chat(
        "预算放宽到1000",
        history_change,
        "ollama",
        user_decisions=new_decisions,
    )

    # V15: 应重新搜索
    is_re_searched = (
        len(r_change["thinking_steps"]) > 0
        or r_change.get("task_plan") is not None
        or _contains_any(r_change["reply"], ["搜索", "重新", "扩大", "找到", "分析"])
    )
    assert is_re_searched, (
        f"V15: 改需求后应重新搜索，实际: stage={r_change['stage']!r}, reply={r_change['reply'][:200]}"
    )

    # 回复应提及预算变化
    assert _contains_any(r_change["text"], ["1000", "预算", "调整", "放宽", "扩大"]), (
        f"V15: 回复应提及新预算，实际: {r_change['text'][:200]}"
    )

    # 如果返回了新推荐，验证在新预算范围内
    new_sd = r_change.get("structured_data")
    if new_sd and new_sd.get("type") == "recommendation":
        new_products = new_sd["products"]
        new_max_price = max(p["price"] for p in new_products)
        assert new_max_price <= 1000, (
            f"V15: 新推荐最高价 {new_max_price} 应 ≤1000（新预算）"
        )
