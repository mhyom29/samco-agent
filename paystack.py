import uuid
import requests

from config import PAYSTACK_SECRET_KEY, PAYSTACK_CALLBACK_URL

PAYSTACK_BASE = "https://api.paystack.co"


def generate_reference(customer_id: str) -> str:
    clean_id = "".join(ch for ch in customer_id if ch.isalnum())
    return f"samco_{clean_id}_{uuid.uuid4().hex[:8]}"


def create_payment_link(email: str, amount_naira: int, reference: str, metadata: dict | None = None):
    """
    Calls Paystack's Initialize Transaction endpoint and returns the checkout URL.
    Raises RuntimeError with a readable message on failure — the agent will relay
    a graceful fallback to the customer rather than crash the conversation.
    """
    if not PAYSTACK_SECRET_KEY:
        raise RuntimeError("PAYSTACK_SECRET_KEY is not configured on the server.")

    payload = {
        "email": email,
        "amount": int(amount_naira) * 100,  # Paystack expects kobo
        "currency": "NGN",
        "reference": reference,
        "metadata": metadata or {},
    }
    if PAYSTACK_CALLBACK_URL:
        payload["callback_url"] = PAYSTACK_CALLBACK_URL

    resp = requests.post(
        f"{PAYSTACK_BASE}/transaction/initialize",
        json=payload,
        headers={
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        },
        timeout=15,
    )
    data = resp.json()
    if not resp.ok or not data.get("status"):
        raise RuntimeError(f"Paystack error: {data.get('message', 'unknown error')}")

    return {
        "authorization_url": data["data"]["authorization_url"],
        "access_code": data["data"]["access_code"],
        "reference": data["data"]["reference"],
    }


def verify_webhook_signature(raw_body: bytes, signature_header: str) -> bool:
    import hashlib
    import hmac

    computed = hmac.new(
        PAYSTACK_SECRET_KEY.encode("utf-8"), raw_body, hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(computed, signature_header or "")
