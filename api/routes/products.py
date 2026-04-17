import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query

router = APIRouter()

_products = None


def _load_products() -> list[dict]:
    global _products
    if _products is None:
        path = Path(__file__).parent.parent.parent / "data" / "products.json"
        with open(path, "r", encoding="utf-8") as f:
            _products = json.load(f)
    return _products


@router.get("/api/products")
def list_products(
    brand: Optional[str] = Query(None),
    min_price: Optional[int] = Query(None),
    max_price: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    scenario: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    products = _load_products()
    filtered = products

    if brand:
        filtered = [p for p in filtered if p["brand"] == brand]
    if min_price is not None:
        filtered = [p for p in filtered if p["price"] >= min_price]
    if max_price is not None:
        filtered = [p for p in filtered if p["price"] <= max_price]
    if type:
        filtered = [p for p in filtered if p["type"] == type]
    if scenario:
        filtered = [p for p in filtered if scenario in p["scenario"]]

    total = len(filtered)
    start = (page - 1) * limit
    end = start + limit

    return {"products": filtered[start:end], "total": total}


@router.get("/api/products/stats")
def product_stats():
    products = _load_products()
    brands = sorted(set(p["brand"] for p in products))
    types = sorted(set(p["type"] for p in products))
    scenarios = sorted(set(s for p in products for s in p["scenario"]))
    prices = [p["price"] for p in products]

    return {
        "total": len(products),
        "brands": brands,
        "types": types,
        "scenarios": scenarios,
        "price_range": {"min": min(prices), "max": max(prices)},
    }
