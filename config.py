import os


def get_llm(mode: str):
    """Create LLM instance based on mode.

    Args:
        mode: "ollama" for local Ollama, "qwen-api" for Qwen cloud API.

    Returns:
        A LangChain chat model instance.
    """
    if mode == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model="qwen2.5:14b",
            base_url="http://localhost:11434",
        )
    elif mode == "qwen-api":
        from langchain_community.chat_models.tongyi import ChatTongyi
        return ChatTongyi(
            model="qwen-plus",
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
        )
    else:
        raise ValueError(f"Unknown LLM mode: {mode}. Use 'ollama' or 'qwen-api'.")
