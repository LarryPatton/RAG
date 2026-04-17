from typing import Annotated

from langchain.agents import create_agent
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from agent.prompts import SYSTEM_PROMPT


class ShoppingState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def create_shopping_agent(llm, tools: list):
    """Create a shopping assistant agent.

    Args:
        llm: A LangChain chat model (ChatOllama or ChatTongyi).
        tools: List of LangChain tools [product_search, place_order].

    Returns:
        A compiled LangGraph agent.
    """
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
    return agent
