from twilio.rest import Client

from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return _client


def send_message(customer_id: str, body: str):
    """
    customer_id should be a bare phone number in international format,
    e.g. 2347058624928. This function adds the 'whatsapp:' prefix Twilio
    expects. Named send_message (not send_whatsapp_message) to match the
    same interface as telegram.send_message — so main.py can call either
    channel's sender interchangeably.
    """
    to_number = customer_id
    if not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:+{to_number.lstrip('+')}"

    client = _get_client()
    return client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        to=to_number,
        body=body,
    )
