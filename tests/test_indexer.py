import os
import shutil
import tempfile
from unittest import mock

from rag.indexer import build_index


def test_build_index_returns_queryable_index():
    products = [
        {
            "id": "test_001",
            "name": "测试降噪耳机A",
            "category": "耳机",
            "type": "入耳式",
            "brand": "TestBrand",
            "price": 299,
            "platform": "京东",
            "rating": 4.5,
            "features": ["主动降噪", "蓝牙5.0"],
            "scenario": ["通勤"],
            "noise_cancellation": "主动降噪",
            "description": "测试用降噪耳机"
        },
        {
            "id": "test_002",
            "name": "测试运动耳机B",
            "category": "耳机",
            "type": "入耳式",
            "brand": "TestBrand",
            "price": 199,
            "platform": "淘宝",
            "rating": 4.2,
            "features": ["防水", "运动耳挂"],
            "scenario": ["运动"],
            "noise_cancellation": "无",
            "description": "测试用运动耳机"
        }
    ]
    # Use a temp directory so tests don't pollute the real index cache
    tmp_dir = tempfile.mkdtemp()
    try:
        with mock.patch("rag.indexer.CACHE_DIR", tmp_dir), \
             mock.patch("rag.indexer.CACHE_FILE", os.path.join(tmp_dir, "embeddings.pkl")):
            index = build_index(products)
            assert index is not None
            retriever = index.as_retriever(similarity_top_k=2)
            results = retriever.retrieve("降噪耳机")
            assert len(results) > 0
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
