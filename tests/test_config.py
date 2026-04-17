import os
from config import get_llm


def test_get_llm_ollama_returns_chat_ollama():
    llm = get_llm("ollama")
    assert llm is not None
    assert "ollama" in type(llm).__name__.lower() or "ChatOllama" in type(llm).__name__


def test_get_llm_qwen_api_returns_tongyi():
    os.environ["DASHSCOPE_API_KEY"] = "test-key-placeholder"
    llm = get_llm("qwen-api")
    assert llm is not None
    del os.environ["DASHSCOPE_API_KEY"]


def test_get_llm_invalid_mode_raises():
    try:
        get_llm("invalid")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
