import re
from typing import Annotated

from langchain_core.messages import AnyMessage, AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from agent.prompts import SYSTEM_PROMPT

# Required user-provided fields before tool calls are allowed
REQUIRED_FIELDS = {"budget", "type", "scenario"}

MISSING_LABELS = {"budget": "预算范围", "type": "耳机类型", "scenario": "使用场景"}

# Max times the gate can bounce back to model before giving up
MAX_GATE_RETRIES = 2


class ShoppingState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def extract_confirmed_info(messages: list) -> dict[str, bool]:
    """Extract confirmed user decisions from conversation history.

    Scans all HumanMessage instances for user-provided budget, type, and scenario.
    Also parses decision prefixes injected by the backend.
    """
    confirmed = {}

    for msg in messages:
        content = getattr(msg, "content", "")
        if not content:
            continue

        # Decision prefix injected by backend (e.g., "[已确认的用户决策...]")
        if "[已确认的用户决策" in content:
            if "耳机类型:" in content or "耳机类型：" in content:
                confirmed["type"] = True
            if "预算:" in content or "预算：" in content:
                confirmed["budget"] = True
            if "使用场景:" in content or "使用场景：" in content:
                confirmed["scenario"] = True
            # Fall through to also parse user text after prefix

        # Only parse user messages
        if not isinstance(msg, HumanMessage):
            continue

        text = content.strip()

        # Budget: numbers that look like prices (50-10000), with optional unit
        if re.search(r"\d{2,5}\s*(元|以内|块|预算|左右)?", text) or re.search(r"\d+-\d+", text):
            confirmed["budget"] = True

        # Type: earphone form factor
        if re.search(r"入耳|头戴|颈挂", text):
            confirmed["type"] = True

        # Scenario: usage context
        if re.search(r"通勤|运动|跑步|办公|游戏|音乐|睡眠|学习", text):
            confirmed["scenario"] = True

    return confirmed


def create_shopping_agent(llm, tools: list):
    """Create a shopping assistant agent with a pre-tool-call gate.

    Graph structure:
        __start__ → model → [has tool_calls?]
                                ├─ YES → gate → [info complete?]
                                │                  ├─ YES → tools → model
                                │                  └─ NO  → model (with feedback)
                                └─ NO  → __end__
    """
    model_with_tools = llm.bind_tools(tools)

    def model_node(state: ShoppingState):
        msgs = list(state["messages"])
        # Ensure system prompt is always first
        if not msgs or not isinstance(msgs[0], SystemMessage):
            msgs = [SystemMessage(content=SYSTEM_PROMPT)] + msgs
        response = model_with_tools.invoke(msgs)
        return {"messages": [response]}

    def gate_node(state: ShoppingState):
        confirmed = extract_confirmed_info(state["messages"])
        missing = REQUIRED_FIELDS - confirmed.keys()

        if not missing:
            # All required info present — allow tool calls through
            # Return empty update = no-op, state unchanged, last msg still has tool_calls
            return {"messages": []}

        # Count how many times we've already bounced back
        gate_count = sum(
            1 for m in state["messages"]
            if isinstance(m, SystemMessage) and "[系统拦截]" in getattr(m, "content", "")
        )
        if gate_count >= MAX_GATE_RETRIES:
            # Give up — let tools through to avoid infinite loop
            return {"messages": []}

        # Missing info — block tool calls, send LLM back to ask user
        missing_str = "、".join(MISSING_LABELS[f] for f in missing)
        feedback = SystemMessage(
            content=(
                f"[系统拦截] 用户尚未提供以下必要信息：{missing_str}。"
                f"你刚才试图调用工具，但信息不完整，已被系统拦截。"
                f"请向用户询问缺失的信息，每次只问一个问题，并提供 quick_replies 选项。"
                f"不要自己假设或填充这些信息。"
            )
        )

        # Replace last AI message (strip tool_calls) using same ID to avoid duplication
        last_msg = state["messages"][-1]
        clean_msg = AIMessage(
            content=last_msg.content if hasattr(last_msg, "content") else "",
            id=last_msg.id,  # Same ID → replaces original in add_messages reducer
        )

        return {"messages": [clean_msg, feedback]}

    def should_use_tools(state: ShoppingState):
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "gate"
        return END

    def gate_decision(state: ShoppingState):
        last = state["messages"][-1]
        if isinstance(last, SystemMessage) and "[系统拦截]" in last.content:
            # Gate injected feedback — go back to model
            return "model"
        # Gate passed through (empty update) — last msg still has tool_calls → tools
        return "tools"

    # Build the graph
    tool_node = ToolNode(tools)

    graph = StateGraph(ShoppingState)
    graph.add_node("model", model_node)
    graph.add_node("gate", gate_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", should_use_tools, {"gate": "gate", END: END})
    graph.add_conditional_edges("gate", gate_decision, {"model": "model", "tools": "tools"})
    graph.add_edge("tools", "model")

    return graph.compile()
