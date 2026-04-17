from langchain_core.tools import tool
from llama_index.core import VectorStoreIndex


def create_product_search_tool(index: VectorStoreIndex):
    """Create a LangChain-compatible product search tool from a LlamaIndex index.

    Args:
        index: A built VectorStoreIndex containing product data.

    Returns:
        A LangChain @tool function that searches products.
    """
    query_engine = index.as_query_engine(similarity_top_k=5)

    @tool
    def product_search(query: str) -> str:
        """搜索商品数据库，根据用户需求找到匹配商品。
        输入用户的商品需求描述，如"500以内入耳式降噪耳机通勤用"，
        返回匹配商品的详细信息列表。"""
        response = query_engine.query(query)
        return str(response)

    return product_search
