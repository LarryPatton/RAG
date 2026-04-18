"""Shared product data loader. Single source of truth for products.json."""

import json
import os

_PRODUCTS: list[dict] | None = None
_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "products.json")


def load_products() -> list[dict]:
    """Load and cache all products from products.json."""
    global _PRODUCTS
    if _PRODUCTS is None:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            _PRODUCTS = json.load(f)
    return _PRODUCTS


def find_product(name: str) -> dict | None:
    """Find a product by name. Exact match first, then fuzzy match with overlap threshold."""
    products = load_products()
    # Exact match
    for p in products:
        if p["name"] == name:
            return p
    # Fuzzy match: require at least 4 character overlap to prevent false positives
    for p in products:
        if len(name) >= 4 and name in p["name"]:
            return p
        if len(p["name"]) >= 4 and p["name"] in name:
            return p
    return None
