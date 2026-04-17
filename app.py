import json
import re
from datetime import datetime

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

from agent.graph import create_shopping_agent
from config import get_llm
from rag.indexer import build_index
from rag.query import create_product_search_tool
from tools.order import place_order

# --- Page config ---
st.set_page_config(page_title="RAG 购物助手", page_icon="🛒", layout="wide")

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ 设置")
    llm_mode = st.selectbox(
        "选择 LLM",
        ["ollama", "qwen-api"],
        format_func=lambda x: "Ollama (本地)" if x == "ollama" else "Qwen API (云端)",
    )

    if st.button("🔄 清空对话"):
        st.session_state.messages = []
        st.session_state.logs = []
        st.session_state.current_stage = "等待输入"
        st.rerun()

    st.divider()
    st.subheader("📊 Agent 推理日志")

    # Stage indicator
    stages = ["意图澄清", "搜索中", "推荐方案", "订单确认", "下单完成"]
    current = st.session_state.get("current_stage", "等待输入")
    for s in stages:
        if s == current:
            st.markdown(f"🔄 **{s}** ← 当前")
        elif stages.index(s) < stages.index(current) if current in stages else False:
            st.markdown(f"✅ {s}")
        else:
            st.markdown(f"⬜ {s}")

    st.divider()

    # Reasoning logs
    for log in st.session_state.get("logs", []):
        with st.expander(f"[{log['timestamp']}] {log['step']}"):
            st.text(f"输入: {log['input']}")
            st.text(f"输出: {log['output'][:200]}")


# --- Initialize session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "logs" not in st.session_state:
    st.session_state.logs = []
if "current_stage" not in st.session_state:
    st.session_state.current_stage = "等待输入"


@st.cache_resource
def init_index():
    """Load product data and build the vector index (cached)."""
    with open("data/products.json", "r", encoding="utf-8") as f:
        products = json.load(f)
    return build_index(products)


@st.cache_resource
def init_agent(_llm_mode: str):
    """Create the shopping agent (cached per LLM mode)."""
    llm = get_llm(_llm_mode)
    index = init_index()
    search_tool = create_product_search_tool(index)
    agent = create_shopping_agent(llm, [search_tool, place_order])
    return agent


def extract_stage(text: str) -> str:
    """Extract [阶段] tag from agent response."""
    match = re.search(r"\[(.+?)\]", text)
    if match:
        stage = match.group(1)
        valid = ["意图澄清", "搜索中", "推荐方案", "订单确认", "下单完成"]
        if stage in valid:
            return stage
    return st.session_state.get("current_stage", "等待输入")


def add_log(step: str, input_text: str, output_text: str):
    """Add an entry to the reasoning log."""
    st.session_state.logs.append({
        "step": step,
        "input": input_text,
        "output": output_text,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    })


# --- Main chat area ---
st.title("🛒 RAG 购物助手")
st.caption("基于 LangGraph + LlamaIndex + Qdrant 的智能购物助手 Demo")

# Display chat history
for msg in st.session_state.messages:
    role = msg["role"]
    with st.chat_message(role):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("帮你找什么？比如：帮我找一款500以内的降噪耳机"):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            add_log("用户输入", prompt, "")
            agent = init_agent(llm_mode)

            # Build message history for the agent
            agent_messages = []
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    agent_messages.append(HumanMessage(content=msg["content"]))
                else:
                    agent_messages.append(AIMessage(content=msg["content"]))

            result = agent.invoke({"messages": agent_messages})

            # Extract the last AI message
            ai_message = result["messages"][-1]
            response_text = ai_message.content

            # Update stage
            st.session_state.current_stage = extract_stage(response_text)
            add_log(
                st.session_state.current_stage,
                prompt,
                response_text[:200],
            )

            # Display response
            st.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.rerun()
