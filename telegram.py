import requests

from config import TELEGRAM_BOT_TOKEN

API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_message(chat_id, text: str):
    resp = requests.post(
        f"{API_BASE}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def get_updates(offset=None, timeout=30):
    params = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset

    resp = requests.get(
        f"{API_BASE}/getUpdates",
        params=params,
        timeout=timeout + 10,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram getUpdates error: {data}")
    return data["result"]


def get_me():
    resp = requests.get(f"{API_BASE}/getMe", timeout=10)
    resp.raise_for_status()
    return resp.json()


def set_webhook(url: str):
    """Registers your deployed URL with Telegram so it POSTs messages to /webhook."""
    resp = requests.post(f"{API_BASE}/setWebhook", json={"url": url}, timeout=15)
    resp.raise_for_status()
    return resp.json()


def delete_webhook():
    """Switches back to polling mode by removing the registered webhook."""
    resp = requests.post(f"{API_BASE}/deleteWebhook", timeout=15)
    resp.raise_for_status()
    return resp.json()
