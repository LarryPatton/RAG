import json
import os
import pickle
import time

import rag.compat  # noqa: F401 — patches QdrantVectorStore for Python 3.14

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import VectorStoreIndex, Settings, StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.llms import MockLLM

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index_cache")
CACHE_FILE = os.path.join(CACHE_DIR, "embeddings.pkl")
COLLECTION_NAME = "products"


def get_embed_model():
    """Return the BGE-small-zh embedding model (downloads ~100MB on first use)."""
    return HuggingFaceEmbedding(model_name="BAAI/bge-small-zh-v1.5")


def index_exists() -> bool:
    """Check if a cached index exists on disk."""
    return os.path.exists(CACHE_FILE)


def _products_to_texts(products: list[dict]) -> list[dict]:
    """Convert product dicts to text + metadata pairs."""
    items = []
    for p in products:
        text = (
            f"{p['name']}，{p['brand']}品牌，¥{p['price']}，{p['type']}，"
            f"特点：{'、'.join(p['features'])}，"
            f"适合：{'、'.join(p['scenario'])}，"
            f"{p['description']}"
        )
        items.append({
            "text": text,
            "metadata": {
                "id": p["id"],
                "name": p["name"],
                "price": p["price"],
                "brand": p["brand"],
                "type": p["type"],
                "platform": p["platform"],
                "rating": p["rating"],
            },
        })
    return items


def build_index(products: list[dict]) -> VectorStoreIndex:
    """Build a vector index from product data.

    Uses a disk cache for pre-computed embeddings:
    - First build: computes embeddings (~30s for 500 products), saves to ./index_cache/
    - Subsequent builds: loads cached embeddings (~2s)

    Always uses in-memory Qdrant (no persistence issues).
    """
    embed_model = get_embed_model()
    Settings.embed_model = embed_model
    Settings.llm = MockLLM()

    items = _products_to_texts(products)
    client = QdrantClient(":memory:")

    if _cache_exists():
        # Fast path: load pre-computed embeddings, insert directly via Qdrant client
        with open(CACHE_FILE, "rb") as f:
            cache = pickle.load(f)

        vectors = cache["vectors"]
        dim = len(vectors[0])

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

        points = []
        for i, (vec, item) in enumerate(zip(vectors, items)):
            payload = {**item["metadata"], "_node_content": json.dumps({"text": item["text"], "metadata": item["metadata"]}), "text": item["text"]}
            points.append(PointStruct(id=i, vector=vec, payload=payload))

        # Batch insert
        batch_size = 100
        for start in range(0, len(points), batch_size):
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=points[start:start + batch_size],
            )

        vector_store = QdrantVectorStore(
            client=client, collection_name=COLLECTION_NAME, path=None
        )
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        return index

    # Slow path: compute embeddings from scratch using LlamaIndex
    vector_store = QdrantVectorStore(
        client=client, collection_name=COLLECTION_NAME, path=None
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    from llama_index.core import Document
    documents = [
        Document(text=item["text"], metadata=item["metadata"])
        for item in items
    ]

    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
    )

    # Cache the embeddings for next time
    all_points = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=len(products) + 10,
        with_vectors=True,
    )[0]
    vectors = [p.vector for p in all_points]

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "wb") as f:
        pickle.dump({"vectors": vectors}, f)

    return index


def _cache_exists() -> bool:
    return os.path.exists(CACHE_FILE)


def rebuild_index(products: list[dict]) -> VectorStoreIndex:
    """Force rebuild: delete cache and create fresh index."""
    import shutil
    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
    return build_index(products)
