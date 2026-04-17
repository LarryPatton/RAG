import json
import re
from typing import Optional

from langchain_core.messages import HumanMessage, AIMessage


def extract_stage(text: str) -> str:
    """Extract [阶段] tag from agent response text."""
    match = re.search(r"\[(.+?)\]", text)
    if match:
        stage = match.group(1)
        valid = ["意图澄清", "搜索中", "推荐方案", "订单确认", "下单完成"]
        if stage in valid:
            return stage
    return "未知"


def parse_structured_output(text: str) -> dict:
    """Parse agent response into text + optional structured JSON.

    Looks for ```json ... ``` code blocks in the response.
    Returns {"text": <text without json block>, "structured_data": <parsed json or None>}
    """
    pattern = r"```json\s*\n(.*?)\n```"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        json_str = match.group(1).strip()
        try:
            structured_data = json.loads(json_str)
        except json.JSONDecodeError:
            structured_data = None

        # Remove the JSON block from text, keep surrounding text
        clean_text = text[:match.start()].strip() + "\n" + text[match.end():].strip()
        clean_text = clean_text.strip()

        return {"text": clean_text, "structured_data": structured_data}

    return {"text": text, "structured_data": None}


class AgentService:
    """Singleton service wrapping the LangGraph agent."""

    def __init__(self):
        self._agent = None
        self._llm_mode = None

    def _ensure_agent(self, llm_mode: str):
        """Initialize or reinitialize agent if LLM mode changed."""
        if self._agent is not None and self._llm_mode == llm_mode:
            return

        import json as json_mod
        from config import get_llm
        from rag.indexer import build_index
        from rag.query import create_product_search_tool
        from tools.order import place_order
        from agent.graph import create_shopping_agent

        llm = get_llm(llm_mode)

        with open("data/products.json", "r", encoding="utf-8") as f:
            products = json_mod.load(f)
        index = build_index(products)
        search_tool = create_product_search_tool(index)

        self._agent = create_shopping_agent(llm, [search_tool, place_order])
        self._llm_mode = llm_mode

    def chat(self, message: str, history: list[dict], llm_mode: str = "ollama") -> dict:
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

        messages = []
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=message))

        result = self._agent.invoke({"messages": messages})
        ai_message = result["messages"][-1]
        reply = ai_message.content

        parsed = parse_structured_output(reply)
        stage = extract_stage(reply)

        return {
            "reply": reply,
            "text": parsed["text"],
            "structured_data": parsed["structured_data"],
            "stage": stage,
        }


# Global singleton
agent_service = AgentService()
