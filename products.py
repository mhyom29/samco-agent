"""
SAMCO Superstore product catalog.

This is the AI agent's source of truth for what's in stock, units, and prices.
It mirrors the PRODUCTS array in site/js/catalog.js — same 21 products, same
names, same prices. Every product on the site now has a real photo (either
an actual SAMCO store photo or a stock photo) rather than an icon, so this
list is intentionally shorter than earlier versions — trimmed to only what
could be shown properly.

>>> KEEP THIS IN SYNC WITH THE WEBSITE <<<
When you update prices/products on the site (site/js/catalog.js), update
them here too.
"""

PRODUCTS = [
    # Furniture
    {"name": "Plastic Chairs (set of 4)", "unit": "set of 4", "price": 18000, "category": "furniture"},
    {"name": "Executive Office Chair", "unit": "1 unit, leather", "price": 45000, "category": "furniture"},
    {"name": "Dining Set – Tan Leather", "unit": "table + 4 chairs", "price": 280000, "category": "furniture"},
    {"name": "Dining Set – Teal & Amber (Square Table)", "unit": "table + 4 chairs", "price": 260000, "category": "furniture"},
    {"name": "Dining Set – Teal & Amber (Rectangular Table)", "unit": "table + 4 chairs", "price": 295000, "category": "furniture"},
    {"name": "Dining Set – Cream & Black", "unit": "table + 4 chairs", "price": 310000, "category": "furniture"},
    {"name": "Lounge Chair Duo – Orange & Houndstooth", "unit": "2 chairs + side table", "price": 145000, "category": "furniture"},
    {"name": "Round Sofa Set", "unit": "3-piece lounge set", "price": 320000, "category": "furniture"},

    # Electronics
    {"name": "LED Smart TV", "unit": "32-inch", "price": 95000, "category": "electronics"},
    {"name": "BARDEFU Commercial Blender", "unit": "1 unit, heavy duty", "price": 42000, "category": "electronics"},
    {"name": "SUPER Rechargeable Fan", "unit": "1 unit, foldable", "price": 15500, "category": "electronics"},
    {"name": "Electric Scooter", "unit": "1 unit, rechargeable", "price": 420000, "category": "electronics"},

    # Groceries
    {"name": "Wala Rice Pro", "unit": "50kg bag", "price": 78000, "category": "groceries"},
    {"name": "Stallion Rice", "unit": "25kg bag", "price": 42000, "category": "groceries"},
    {"name": "Optimum Rice", "unit": "10kg bag", "price": 18500, "category": "groceries"},
    {"name": "Vegetable Oil", "unit": "5 litres", "price": 12500, "category": "groceries"},
    {"name": "Spaghetti (carton)", "unit": "20 packs", "price": 15800, "category": "groceries"},

    # Beauty & Personal Care
    {"name": "Body Lotion", "unit": "400ml", "price": 4200, "category": "beauty"},
    {"name": "Roll-on Deodorant", "unit": "50ml", "price": 2200, "category": "beauty"},
    {"name": "Toothpaste", "unit": "1 tube", "price": 2100, "category": "beauty"},
    {"name": "Bathing Soap", "unit": "1 bar", "price": 1500, "category": "beauty"},

    # Baby & Household
    {"name": "Huggies Diapers", "unit": "size 4, jumbo pack", "price": 9800, "category": "baby"},
    {"name": "Baby Wipes", "unit": "pack of 3", "price": 3400, "category": "baby"},
    {"name": "Toilet Tissue", "unit": "pack of 12 rolls", "price": 4300, "category": "baby"},
    {"name": "Vacuum Flask (Thermal Jug)", "unit": "1 litre", "price": 8500, "category": "baby"},
]

CATEGORY_LABELS = {
    "furniture": "Furniture",
    "electronics": "Electronics",
    "groceries": "Groceries",
    "beauty": "Beauty & Personal Care",
    "baby": "Baby & Household",
}


def search_products(query: str, limit: int = 8):
    """Case-insensitive substring search over product name and category label."""
    q = (query or "").strip().lower()
    if not q:
        return []
    results = []
    for p in PRODUCTS:
        label = CATEGORY_LABELS.get(p["category"], p["category"])
        if q in p["name"].lower() or q in label.lower() or q in p["category"]:
            results.append(p)
    return results[:limit]


def find_product_exact(name: str):
    """Best-effort match: exact (case-insensitive) first, then substring, then None."""
    if not name:
        return None
    n = name.strip().lower()
    for p in PRODUCTS:
        if p["name"].lower() == n:
            return p
    matches = [p for p in PRODUCTS if n in p["name"].lower()]
    if len(matches) == 1:
        return matches[0]
    return None
