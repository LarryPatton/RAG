import json
import re
import threading
from collections import OrderedDict
from typing import Optional

from langchain_core.messages import HumanMessage, AIMessage


def extract_stage(text: str, structured_data: dict | None = None) -> str:
    """Extract the most advanced [阶段] tag from agent response text.

    Uses the last valid stage tag found in the text, and also infers
    from structured_data type (recommendation → 推荐方案, order_confirm → 订单确认).
    """
    valid = ["意图澄清", "分析中", "搜索中", "推荐方案", "订单确认", "下单完成"]
    stage_order = {s: i for i, s in enumerate(valid)}

    # Find all stage tags in the text, keep the last (most advanced) one
    best_stage = "未知"
    best_order = -1
    for match in re.finditer(r"\[(意图澄清|分析中|搜索中|推荐方案|订单确认|下单完成)\]", text):
        tag = match.group(1)
        if tag in stage_order and stage_order[tag] > best_order:
            best_stage = tag
            best_order = stage_order[tag]

    # Infer from structured_data type if it gives a more advanced stage
    if structured_data:
        sd_type = structured_data.get("type")
        if sd_type == "recommendation" and stage_order.get("推荐方案", -1) > best_order:
            best_stage = "推荐方案"
        elif sd_type == "order_confirm" and stage_order.get("订单确认", -1) > best_order:
            best_stage = "订单确认"

    return best_stage


def parse_structured_output(text: str) -> dict:
    """Parse agent response into text + optional structured JSON.

    Finds all ```json ... ``` code blocks. Prefers recommendation/order_confirm
    over task_plan when multiple blocks are present.
    Returns {"text": <text without json blocks>, "structured_data": <parsed json or None>,
             "quick_replies": <list of options or None>}
    """
    pattern = r"```json\s*\n(.*?)\n```"
    matches = list(re.finditer(pattern, text, re.DOTALL))

    if not matches:
        return {"text": text, "structured_data": None, "quick_replies": None}

    parsed_blocks = []
    for m in matches:
        try:
            parsed_blocks.append((m, json.loads(m.group(1).strip())))
        except json.JSONDecodeError:
            pass

    if not parsed_blocks:
        return {"text": text, "structured_data": None, "quick_replies": None}

    # Extract quick_replies separately
    quick_replies = None
    remaining_blocks = []
    for m, data in parsed_blocks:
        if data.get("type") == "quick_replies" and isinstance(data.get("options"), list):
            quick_replies = data["options"]
        else:
            remaining_blocks.append((m, data))

    # Prefer recommendation/order_confirm over task_plan
    chosen_data = None
    if remaining_blocks:
        priority_types = {"recommendation", "order_confirm"}
        chosen_data = remaining_blocks[0][1]
        for m, data in remaining_blocks:
            if data.get("type") in priority_types:
                chosen_data = data
                break

    # Remove all JSON blocks from text
    clean_text = text
    for m, _ in reversed(parsed_blocks):
        clean_text = clean_text[:m.start()].rstrip() + "\n" + clean_text[m.end():].lstrip()
    clean_text = clean_text.strip()

    return {"text": clean_text, "structured_data": chosen_data, "quick_replies": quick_replies}


class AgentService:
    """Singleton service wrapping the LangGraph agent."""

    def __init__(self):
        self._agent = None
        self._llm_mode = None
        self._lock = threading.Lock()
        self._product_cache: OrderedDict[str, dict] = OrderedDict()  # name → product data, LRU eviction at 100

    def _cache_product(self, name: str, data: dict):
        """Cache product data with LRU eviction (max 100 entries)."""
        if name in self._product_cache:
            self._product_cache.move_to_end(name)
        self._product_cache[name] = data
        while len(self._product_cache) > 100:
            self._product_cache.popitem(last=False)

    def _ensure_agent(self, llm_mode: str):
        """Initialize or reinitialize agent if LLM mode changed."""
        with self._lock:
            if self._agent is not None and self._llm_mode == llm_mode:
                return

            import json as json_mod
            from config import get_llm
            from rag.indexer import build_index
            from rag.query import create_product_search_tool
            from tools.order import place_order
            from tools.price_comparison import compare_prices
            from tools.inventory import check_inventory
            from agent.graph import create_shopping_agent

            llm = get_llm(llm_mode)

            with open("data/products.json", "r", encoding="utf-8") as f:
                products = json_mod.load(f)
            index = build_index(products)
            search_tool = create_product_search_tool(index)

            self._agent = create_shopping_agent(llm, [search_tool, compare_prices, check_inventory, place_order])
            self._llm_mode = llm_mode

    def _extract_task_plan(self, messages: list) -> dict | None:
        """Extract task_plan JSON from intermediate agent messages."""
        pattern = r"```json\s*\n(.*?)\n```"
        # Walk all messages except the last (which is the final response)
        for msg in messages[:-1]:
            content = getattr(msg, "content", "")
            if not content:
                continue
            for m in re.finditer(pattern, content, re.DOTALL):
                try:
                    data = json.loads(m.group(1).strip())
                    if data.get("type") == "task_plan":
                        return data
                except json.JSONDecodeError:
                    pass
        # Also check final message (agent may output task_plan without tools in one turn)
        final_content = getattr(messages[-1], "content", "") if messages else ""
        for m in re.finditer(pattern, final_content, re.DOTALL):
            try:
                data = json.loads(m.group(1).strip())
                if data.get("type") == "task_plan":
                    return data
            except json.JSONDecodeError:
                pass
        return None

    def _extract_thinking_steps(self, messages: list) -> list[dict]:
        """Extract tool call sequence from LangGraph message chain."""
        tool_display = {
            "product_search": ("🔍", "搜索商品"),
            "compare_prices": ("💰", "比较价格"),
            "check_inventory": ("📦", "查询库存"),
            "place_order": ("✅", "完成下单"),
        }
        steps = []
        # Map tool call id → step index for result attachment
        call_id_to_step: dict[str, int] = {}

        for msg in messages:
            # AIMessage with tool_calls list
            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                for tc in tool_calls:
                    name = tc.get("name", "")
                    icon, label = tool_display.get(name, ("🔧", name))
                    args = tc.get("args", {})
                    # Build a short human-readable input summary
                    input_summary = ", ".join(f"{v}" for v in args.values() if v)[:80]
                    step = {"tool": name, "icon": icon, "label": label, "input": input_summary}
                    call_id_to_step[tc.get("id", "")] = len(steps)
                    steps.append(step)

            # ToolMessage — attach result to the matching step
            tool_call_id = getattr(msg, "tool_call_id", None)
            if tool_call_id and tool_call_id in call_id_to_step:
                idx = call_id_to_step[tool_call_id]
                content = str(getattr(msg, "content", ""))
                # Take first line or first 100 chars as summary
                first_line = content.split("\n")[0][:100]
                steps[idx]["result"] = first_line

        return steps

    def _build_decision_prefix(self, decisions: dict[str, str]) -> str:
        """Build a prefix string from confirmed user decisions to inject into the prompt."""
        if not decisions:
            return ""
        lines = ["[已确认的用户决策，请勿再次询问以下信息：]"]
        label_map = {
            "type": "耳机类型",
            "budget": "预算",
            "scenario": "使用场景",
            "brand_preference": "品牌偏好",
            "noise_cancellation": "降噪需求",
        }
        for key, value in decisions.items():
            label = label_map.get(key, key)
            lines.append(f"- {label}: {value}")
        return "\n".join(lines) + "\n\n"

    def _auto_extract_decisions(self, texts: list[str]) -> dict[str, str]:
        """Auto-extract user decisions from a list of user message texts.

        Used when user_decisions is not explicitly provided (e.g. first turn
        where user includes budget/type/scenario in one message).
        """
        import re as _re
        decisions: dict[str, str] = {}
        combined = " ".join(texts)

        # Budget: "500以内", "500元以内", "1000以下", "200-500", "500左右"
        budget_m = _re.search(r"(\d{2,5})\s*(元|块钱?)?\s*(以内|以下|左右)", combined)
        if not budget_m:
            budget_m = _re.search(r"(\d{3,5})\s*[-～~]\s*(\d{3,5})", combined)
            if budget_m:
                decisions["budget"] = f"¥{budget_m.group(1)}-{budget_m.group(2)}"
        else:
            decisions["budget"] = f"≤¥{budget_m.group(1)}"

        # Type: earphone form factor
        if _re.search(r"入耳", combined):
            decisions["type"] = "入耳式"
        elif _re.search(r"头戴", combined):
            decisions["type"] = "头戴式"
        elif _re.search(r"骨传导", combined):
            decisions["type"] = "骨传导"
        elif _re.search(r"耳挂", combined):
            decisions["type"] = "耳挂式"

        # Scenario
        for scenario in ["通勤", "运动", "跑步", "办公", "游戏", "学习"]:
            if scenario in combined:
                decisions["scenario"] = scenario
                break

        # Noise cancellation
        if _re.search(r"降噪|消噪|主动降", combined):
            decisions["noise_cancellation"] = "需要降噪"

        # Brand preference
        for brand_kw in ["国产优先", "进口", "索尼", "Sony", "苹果", "AirPods", "华为", "小米"]:
            if brand_kw in combined:
                decisions["brand_preference"] = brand_kw
                break

        return decisions

    def _extract_decisions(self, structured_data: dict | None) -> dict[str, str] | None:
        """Extract user decisions from recommendation structured data."""
        if not structured_data or structured_data.get("type") != "recommendation":
            return None
        profile = structured_data.get("user_profile")
        if not profile:
            return None
        decisions = {}
        if profile.get("type"):
            decisions["type"] = profile["type"]
        if profile.get("budget"):
            budget = str(profile["budget"])
            # Clean up and preserve direction (以上 vs 以内)
            clean = budget.replace("≤¥", "").replace("¥", "").strip()
            if "以上" in clean or "起" in clean:
                num = clean.replace("以上", "").replace("起", "").strip()
                decisions["budget"] = f"¥{num}以上"
            else:
                num = clean.replace("以内", "").replace("以下", "").strip()
                decisions["budget"] = f"≤¥{num}"
        if profile.get("scenario"):
            decisions["scenario"] = profile["scenario"]
        if profile.get("brand_preference"):
            decisions["brand_preference"] = profile["brand_preference"]
        if profile.get("noise_cancellation"):
            decisions["noise_cancellation"] = "需要降噪"
        return decisions if decisions else None

    def chat(self, message: str, history: list[dict], llm_mode: str = "ollama", user_decisions: dict[str, str] | None = None) -> dict:
        """Send a message to the agent and get a parsed response.

        Args:
            message: User's message text.
            history: List of {"role": "user"|"assistant", "content": str}.
            llm_mode: "ollama" or "qwen-api".

        Returns:
            {
                "reply": str,               # full raw reply
                "text": str,                 # reply without JSON blocks
                "structured_data": dict|None,# parsed JSON if present
                "stage": str,               # current stage
            }
        """
        self._ensure_agent(llm_mode)

        # Auto-extract decisions from current message + history when not provided
        # This ensures that info embedded in the first user message (e.g. "500以内入耳式通勤")
        # is properly reflected as confirmed decisions in the prefix (V12 fix)
        if not user_decisions:
            all_texts = [msg.get("content", "") for msg in history if msg.get("role") == "user"]
            all_texts.append(message)
            auto_decisions = self._auto_extract_decisions(all_texts)
            if auto_decisions:
                user_decisions = auto_decisions

        # Build decision prefix for the current message
        decision_prefix = self._build_decision_prefix(user_decisions or {})

        messages = []
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=decision_prefix + message))

        result = self._agent.invoke({"messages": messages})
        ai_message = result["messages"][-1]
        reply = ai_message.content

        parsed = parse_structured_output(reply)
        stage = extract_stage(reply)
        thinking_steps = self._extract_thinking_steps(result["messages"])
        task_plan = self._extract_task_plan(result["messages"])

        # Cache real product data from recommendations
        if parsed["structured_data"] and parsed["structured_data"].get("type") == "recommendation":
            for p in parsed["structured_data"].get("products", []):
                if p.get("name"):
                    self._cache_product(p["name"], p)

        # Override order_confirm price/name with cached real data to prevent LLM hallucination
        if parsed["structured_data"] and parsed["structured_data"].get("type") == "order_confirm":
            sd = parsed["structured_data"]
            product_name = sd.get("product", "")
            cached = self._product_cache.get(product_name)
            if not cached:
                # Partial match: find cached product whose name contains or is contained by the order name
                for name, data in self._product_cache.items():
                    if product_name in name or name in product_name:
                        cached = data
                        break
            if cached:
                sd["product"] = cached["name"]
                sd["price"] = cached["price"]
                sd["platform"] = cached.get("platform", sd.get("platform", ""))
                # Populate price_comparison from cached other_platform_prices
                if "other_platform_prices" in cached and not sd.get("price_comparison"):
                    sd["price_comparison"] = {cached["platform"]: cached["price"], **cached["other_platform_prices"]}

        return {
            "reply": reply,
            "text": parsed["text"],
            "structured_data": parsed["structured_data"],
            "stage": stage,
            "thinking_steps": thinking_steps,
            "task_plan": task_plan,
        }

    async def stream_chat(self, message: str, history: list[dict], llm_mode: str = "ollama", user_decisions: dict[str, str] | None = None):
        """Async generator yielding SSE events for streaming chat.

        Event types:
          token          — {"type":"token","content":"..."}
          tool_start     — {"type":"tool_start","tool":"...","icon":"...","label":"...","input":"..."}
          tool_end       — {"type":"tool_end","tool":"...","result":"..."}
          task_plan      — {"type":"task_plan","tasks":[...]}
          structured_data— {"type":"structured_data","data":{...}}
          decision_update— {"type":"decision_update","decisions":{...}}
          stage          — {"type":"stage","stage":"..."}
          thinking_steps — {"type":"thinking_steps","steps":[...]}
          done           — {"type":"done"}
        """
        self._ensure_agent(llm_mode)

        # Auto-extract decisions from current message + history when not provided
        if not user_decisions:
            all_texts = [msg.get("content", "") for msg in history if msg.get("role") == "user"]
            all_texts.append(message)
            auto_decisions = self._auto_extract_decisions(all_texts)
            if auto_decisions:
                user_decisions = auto_decisions

        # Build decision prefix for the current message
        decision_prefix = self._build_decision_prefix(user_decisions or {})

        messages = []
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=decision_prefix + message))

        tool_display = {
            "product_search": ("🔍", "搜索商品"),
            "compare_prices": ("💰", "比较价格"),
            "check_inventory": ("📦", "查询库存"),
            "place_order": ("✅", "完成下单"),
        }

        accumulated_text = ""
        thinking_steps: list[dict] = []
        # tool_call_id → step index for result attachment
        call_id_to_step: dict[str, int] = {}

        async for event in self._agent.astream_events({"messages": messages}, version="v2"):
            kind = event["event"]
            name = event.get("name", "")

            # LLM token
            if kind == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    accumulated_text += chunk.content
                    yield {"type": "token", "content": chunk.content}

            # Tool call starting
            elif kind == "on_tool_start" and name in tool_display:
                icon, label = tool_display[name]
                args = event["data"].get("input", {})
                input_summary = ", ".join(str(v) for v in args.values() if v)[:80]
                run_id = event.get("run_id", "")
                step = {"tool": name, "icon": icon, "label": label, "input": input_summary}
                call_id_to_step[run_id] = len(thinking_steps)
                thinking_steps.append(step)
                yield {"type": "tool_start", **step}

            # Tool call finished
            elif kind == "on_tool_end" and name in tool_display:
                run_id = event.get("run_id", "")
                output = event["data"].get("output", "")
                # output may be a ToolMessage object or a string
                if hasattr(output, "content"):
                    output = output.content
                first_line = str(output).split("\n")[0][:120]
                idx = call_id_to_step.get(run_id)
                if idx is not None and idx < len(thinking_steps):
                    thinking_steps[idx]["result"] = first_line
                yield {"type": "tool_end", "tool": name, "result": first_line}

        # ── Post-stream processing ──────────────────────────────────────────
        parsed = parse_structured_output(accumulated_text)
        stage = extract_stage(accumulated_text, parsed["structured_data"])

        # Emit task_plan if found in text
        for task_plan_match in re.finditer(r"```json\s*\n(.*?)\n```", accumulated_text, re.DOTALL):
            try:
                maybe_plan = json.loads(task_plan_match.group(1).strip())
                if maybe_plan.get("type") == "task_plan":
                    yield {"type": "task_plan", "data": maybe_plan}
                    break
            except json.JSONDecodeError:
                pass

        # Update product cache + override hallucinated prices
        if parsed["structured_data"]:
            sd = parsed["structured_data"]
            if sd.get("type") == "recommendation":
                for p in sd.get("products", []):
                    if p.get("name"):
                        self._cache_product(p["name"], p)

            if sd.get("type") == "order_confirm":
                product_name = sd.get("product", "")
                cached = self._product_cache.get(product_name)
                if not cached:
                    for n, d in self._product_cache.items():
                        if product_name in n or n in product_name:
                            cached = d
                            break
                if cached:
                    sd["product"] = cached["name"]
                    sd["price"] = cached["price"]
                    sd["platform"] = cached.get("platform", sd.get("platform", ""))
                    if "other_platform_prices" in cached and not sd.get("price_comparison"):
                        sd["price_comparison"] = {cached["platform"]: cached["price"], **cached["other_platform_prices"]}

            yield {"type": "structured_data", "data": sd}

            # Emit decision_update for recommendation data
            decisions = self._extract_decisions(sd)
            if decisions:
                yield {"type": "decision_update", "decisions": decisions}

        if parsed["quick_replies"]:
            yield {"type": "quick_replies", "options": parsed["quick_replies"]}

        yield {"type": "stage", "stage": stage}
        yield {"type": "thinking_steps", "steps": thinking_steps}
        yield {"type": "done", "clean_text": parsed["text"]}


# Global singleton
agent_service = AgentService()
