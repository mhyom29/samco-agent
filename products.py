"""
SAMCO Superstore product catalog.
Kept in 1-to-1 sync with site/js/catalog.js.
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
    {"name": "samsung charger", "unit": "20 units", "price": 7000, "category": "electronics"},
    {"name": "xiaomi power bank", "unit": "20 units", "price": 42000, "category": "electronics"},
    {"name": "30000MAH powerbank", "unit": "20 units", "price": 30000, "category": "electronics"},
    {"name": "wifi router", "unit": "50 units", "price": 15000, "category": "electronics"},
    {"name": "newage powerbank", "unit": "30 units", "price": 30000, "category": "electronics"},
    {"name": "LED Smart TV", "unit": "32-inch", "price": 95000, "category": "electronics"},
    {"name": "BARDEFU Commercial Blender", "unit": "1 unit, heavy duty", "price": 42000, "category": "electronics"},
    {"name": "SUPER Rechargeable Fan", "unit": "1 unit, foldable", "price": 15500, "category": "electronics"},
    {"name": "Electric Scooter", "unit": "1 unit, rechargeable", "price": 420000, "category": "electronics"},

    # Groceries
    {"name": "Stallion Rice", "unit": "25kg bag", "price": 42000, "category": "groceries"},
    {"name": "Optimum Rice", "unit": "10kg bag", "price": 18500, "category": "groceries"},
    {"name": "Amaana Vegetable Oil", "unit": "5 litres", "price": 12500, "category": "groceries"},
    {"name": "Spaghetti (carton)", "unit": "20 packs", "price": 15800, "category": "groceries"},
    {"name": "Vegitables", "unit": "20 kg", "price": 1000, "category": "groceries"},
    {"name": "Dano milk", "unit": "20 units", "price": 1000, "category": "groceries"},
    {"name": "corn", "unit": "100 pieces", "price": 200, "category": "groceries"},
    {"name": "pea(x10)", "unit": "200 pieces", "price": 300, "category": "groceries"},

    # Beauty & Personal Care
    {"name": "nivea cream(men)", "unit": "100 units", "price": 7500, "category": "beauty"},
    {"name": "nivea spray(men)", "unit": "100 units", "price": 7500, "category": "beauty"},
    {"name": "Riggs", "unit": "100 units", "price": 4500, "category": "beauty"},
    {"name": "storm spray", "unit": "100 units", "price": 3500, "category": "beauty"},
    {"name": "Body Lotion", "unit": "400ml", "price": 4200, "category": "beauty"},
    {"name": "Roll-on Deodorant", "unit": "50ml", "price": 2200, "category": "beauty"},
    {"name": "Toothpaste", "unit": "1 tube", "price": 2100, "category": "beauty"},
    {"name": "Bathing Soap", "unit": "1 bar", "price": 1500, "category": "beauty"},

    # Baby & Household
    {"name": "Huggies Diapers", "unit": "size 4, jumbo pack", "price": 9800, "category": "baby"},
    {"name": "Baby Wipes", "unit": "pack of 3", "price": 3400, "category": "baby"},
    {"name": "Toilet Tissue", "unit": "pack of 12 rolls", "price": 4300, "category": "baby"},
    {"name": "Vacuum Flask (Thermal Jug)", "unit": "1 litre", "price": 8500, "category": "baby"},
    {"name": "groom kit", "unit": "50 unit", "price": 2500, "category": "baby"},
]

CATEGORY_LABELS = {
    "furniture": "Furniture",
    "electronics": "Electronics",
    "groceries": "Groceries",
    "beauty": "Beauty & Personal Care",
    "baby": "Baby & Household",
}


def search_products(query: str):
    words = [
        w for w in query.lower().replace("(", "").replace(")", "").split()
        if w not in ["units", "unit", "x1", "x2", "x3", "x4", "x5"]
    ]
    results = []

    for product in PRODUCTS:
        product_name = product["name"].lower()
        if all(word in product_name for word in words):
            results.append(product)

    return results


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
