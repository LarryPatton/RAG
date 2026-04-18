"""One-time script to enrich products.json with stock and cross-platform prices."""
import json
import random

PLATFORMS = ["京东", "天猫", "拼多多"]

def enrich(products: list[dict]) -> list[dict]:
    rng = random.Random(42)  # fixed seed for reproducibility
    enriched = []
    for p in products:
        p = dict(p)
        # Stock: 0-100, weighted toward 20-80 range
        p["stock"] = rng.randint(0, 100)

        # Cross-platform prices: other 2 platforms at ±5%~15% of base price
        base = p["price"]
        other_platforms = [pl for pl in PLATFORMS if pl != p["platform"]]
        other_prices = {}
        for pl in other_platforms:
            # Each platform gets a random multiplier between 0.85 and 1.15
            multiplier = rng.uniform(0.85, 1.15)
            other_prices[pl] = round(base * multiplier)
        p["other_platform_prices"] = other_prices

        enriched.append(p)
    return enriched


if __name__ == "__main__":
    input_path = "data/products.json"
    with open(input_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"Loaded {len(products)} products")
    enriched = enrich(products)

    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"Enriched {len(enriched)} products")
    print("Sample:")
    sample = enriched[0]
    print(f"  stock: {sample['stock']}")
    print(f"  other_platform_prices: {sample['other_platform_prices']}")
    print("Done.")
