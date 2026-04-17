from langchain_core.tools import tool
from llama_index.core import VectorStoreIndex


def create_product_search_tool(index: VectorStoreIndex):
    """Create a LangChain-compatible product search tool from a LlamaIndex index.

    Args:
        index: A built VectorStoreIndex containing product data.

    Returns:
        A LangChain @tool function that searches products.
    """
    retriever = index.as_retriever(similarity_top_k=8)

    @tool
    def product_search(query: str) -> str:
        """搜索商品数据库，根据用户需求找到匹配商品。
        输入用户的商品需求描述，如"500以内入耳式降噪耳机通勤用"，
        返回匹配商品的详细信息列表。"""
        nodes = retriever.retrieve(query)
        if not nodes:
            return "未找到匹配商品。"
        results = []
        for i, node in enumerate(nodes, 1):
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
