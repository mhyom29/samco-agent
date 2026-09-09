import sqlite3
import json
import time
from contextlib import contextmanager

from config import DB_PATH


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                customer_id TEXT PRIMARY KEY,
                channel TEXT,
                last_interaction_id TEXT,
                updated_at REAL
            );

            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                unit TEXT,
                unit_price INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                UNIQUE(customer_id, product_name)
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT NOT NULL,
                channel TEXT NOT NULL DEFAULT 'telegram',
                customer_name TEXT,
                delivery_address TEXT,
                email TEXT,
                items_json TEXT,
                total_amount INTEGER,
                paystack_reference TEXT UNIQUE,
                paystack_link TEXT,
                status TEXT DEFAULT 'awaiting_payment',
                created_at REAL,
                updated_at REAL
            );
            """
        )


# ---------- conversation state ----------

def get_last_interaction_id(customer_id: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT last_interaction_id FROM conversations WHERE customer_id = ?",
            (customer_id,),
        ).fetchone()
        return row["last_interaction_id"] if row else None


def set_last_interaction_id(customer_id: str, interaction_id: str, channel: str = "telegram"):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO conversations (customer_id, channel, last_interaction_id, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(customer_id) DO UPDATE SET
                channel = excluded.channel,
                last_interaction_id = excluded.last_interaction_id,
                updated_at = excluded.updated_at
            """,
            (customer_id, channel, interaction_id, time.time()),
        )


def reset_conversation(customer_id: str):
    """Used if a conversation gets stuck — clears server-side thread + local cart."""
    with get_conn() as conn:
        conn.execute("DELETE FROM conversations WHERE customer_id = ?", (customer_id,))
        conn.execute("DELETE FROM cart_items WHERE customer_id = ?", (customer_id,))


# ---------- cart ----------

def add_to_cart(customer_id: str, product_name: str, unit: str, unit_price: int, quantity: int):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO cart_items (customer_id, product_name, unit, unit_price, quantity)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(customer_id, product_name) DO UPDATE SET
                quantity = quantity + excluded.quantity
            """,
            (customer_id, product_name, unit, unit_price, quantity),
        )


def remove_from_cart(customer_id: str, product_name: str):
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM cart_items WHERE customer_id = ? AND product_name = ?",
            (customer_id, product_name),
        )
        return cur.rowcount > 0


def get_cart(customer_id: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT product_name, unit, unit_price, quantity FROM cart_items WHERE customer_id = ?",
            (customer_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def clear_cart(customer_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM cart_items WHERE customer_id = ?", (customer_id,))


def cart_total(customer_id: str) -> int:
    return sum(item["unit_price"] * item["quantity"] for item in get_cart(customer_id))


# ---------- orders ----------

def create_order(customer_id, channel, customer_name, delivery_address, email, items, total_amount, reference, payment_link):
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO orders
                (customer_id, channel, customer_name, delivery_address, email, items_json,
                 total_amount, paystack_reference, paystack_link, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'awaiting_payment', ?, ?)
            """,
            (
                customer_id, channel, customer_name, delivery_address, email, json.dumps(items),
                total_amount, reference, payment_link, time.time(), time.time(),
            ),
        )
        return cur.lastrowid


def get_order_by_reference(reference: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM orders WHERE paystack_reference = ?", (reference,)
        ).fetchone()
        return dict(row) if row else None


def update_order_status(reference: str, status: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE orders SET status = ?, updated_at = ? WHERE paystack_reference = ?",
            (status, time.time(), reference),
        )
