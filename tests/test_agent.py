from agent.graph import create_shopping_agent, ShoppingState
from agent.prompts import SYSTEM_PROMPT


def test_shopping_state_has_messages():
    annotations = ShoppingState.__annotations__
    assert "messages" in annotations


def test_system_prompt_contains_key_instructions():
    assert "product_search" in SYSTEM_PROMPT
    assert "place_order" in SYSTEM_PROMPT
    assert "[阶段]" in SYSTEM_PROMPT
    assert "Markdown 表格" in SYSTEM_PROMPT


def test_create_shopping_agent_compiles():
    from langchain_core.tools import tool
    from langchain_core.language_models.fake_chat_models import FakeChatModel

    @tool
    def dummy_tool(x: str) -> str:
        """Dummy tool."""
        return "ok"

    fake_llm = FakeChatModel(responses=["hello"])
    agent = create_shopping_agent(fake_llm, [dummy_tool])
    assert agent is not None
