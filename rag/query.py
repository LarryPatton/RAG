import re

from langchain_core.tools import tool
from llama_index.core import VectorStoreIndex


def create_product_search_tool(index: VectorStoreIndex):
    """Create a LangChain-compatible product search tool from a LlamaIndex index."""
    # Retrieve more candidates to allow for post-filtering
    retriever = index.as_retriever(similarity_top_k=30)

    @tool
    def product_search(query: str) -> str:
        """搜索商品数据库，根据用户需求找到匹配商品。
        输入用户的商品需求描述，如"500以内入耳式降噪耳机通勤用"，
        返回匹配商品的详细信息列表。"""
        nodes = retriever.retrieve(query)
        if not nodes:
            return "未找到匹配商品。"

        # Post-retrieval filtering: type, then budget
        earphone_type = _extract_type(query)
        max_price = _extract_budget(query)

        # Filter by type first (strict — this is a hard user requirement)
        if earphone_type:
            type_filtered = [n for n in nodes if n.metadata.get("type") == earphone_type]
            if len(type_filtered) >= 3:
                nodes = type_filtered

        # Filter by budget
        if max_price:
            budget_filtered = [n for n in nodes if n.metadata.get("price", 0) <= max_price]
            if len(budget_filtered) >= 3:
                nodes = budget_filtered

        # Sort by relevance score (already sorted) then return top 8
        results = []
        for i, node in enumerate(nodes[:8], 1):
            meta = node.metadata
            results.append(
                f"商品{i}: {meta.get('name', '未知')}\n"
                f"  品牌: {meta.get('brand', '未知')}\n"
                f"  价格: ¥{meta.get('price', '未知')}\n"
                f"  类型: {meta.get('type', '未知')}\n"
                f"  平台: {meta.get('platform', '未知')}\n"
                f"  评分: {meta.get('rating', '未知')}\n"
                f"  详情: {node.text}"
            )
        return "\n\n".join(results)

    return product_search


def _extract_type(query: str) -> str | None:
    """Extract earphone type from search query."""
    if re.search(r"头戴", query):
        return "头戴式"
    if re.search(r"入耳", query):
        return "入耳式"
    if re.search(r"颈挂", query):
        return "颈挂式"
    return None


def _extract_budget(query: str) -> int | None:
    """Extract max budget from a search query string. Returns None if no cap (e.g. '以上')."""
    # "1000以上" — no upper limit, don't filter
    if re.search(r"\d{2,5}\s*(元|块)?\s*(以上|起)", query):
        return None

    # "1000元以内", "1000以内", "预算1000"
    m = re.search(r"(\d{2,5})\s*(元|块)?\s*(以内|以下|左右|内)", query)
    if m:
        price = int(m.group(1))
        if "左右" in m.group(0):
            return int(price * 1.2)  # 1000左右 → max 1200
        return price

    # "预算500", "500元预算"
    m = re.search(r"预算\s*(\d{2,5})|(\d{2,5})\s*元?\s*预算", query)
    if m:
        return int(m.group(1) or m.group(2))

    # "200-500", "200到500"
    m = re.search(r"(\d{2,5})\s*[-–~到]\s*(\d{2,5})", query)
    if m:
        return int(m.group(2))

    # Bare number at start or alone: "1000头戴式"
    m = re.search(r"(\d{3,5})", query)
    if m:
        return int(m.group(1))

    return None
