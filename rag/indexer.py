from qdrant_client import QdrantClient
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.llms import MockLLM


def get_embed_model():
    """Return the BGE-small-zh embedding model (downloads ~100MB on first use)."""
    return HuggingFaceEmbedding(model_name="BAAI/bge-small-zh-v1.5")


def build_index(products: list[dict]) -> VectorStoreIndex:
    """Build a vector index from product data.

    Args:
        products: List of product dicts with keys: id, name, brand, price,
                  type, features, scenario, description.

    Returns:
        A LlamaIndex VectorStoreIndex backed by in-memory Qdrant.
    """
    embed_model = get_embed_model()
    Settings.embed_model = embed_model
    # Use MockLLM so the query engine works without a real LLM configured
    Settings.llm = MockLLM()

    client = QdrantClient(":memory:")
    vector_store = QdrantVectorStore(client=client, collection_name="products", path=None)

    documents = []
    for p in products:
        text = (
            f"{p['name']}，{p['brand']}品牌，¥{p['price']}，{p['type']}，"
            f"特点：{'、'.join(p['features'])}，"
            f"适合：{'、'.join(p['scenario'])}，"
            f"{p['description']}"
        )
        doc = Document(
            text=text,
            metadata={
                "id": p["id"],
                "name": p["name"],
                "price": p["price"],
                "brand": p["brand"],
                "type": p["type"],
                "platform": p["platform"],
                "rating": p["rating"],
            },
        )
        documents.append(doc)

    index = VectorStoreIndex.from_documents(
        documents,
        vector_store=vector_store,
    )
    return index
