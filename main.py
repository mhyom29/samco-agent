"""
SAMCO Superstore — FastAPI Backend Service.

    uvicorn main:app --host 0.0.0.0 --port 8000
"""

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Form, BackgroundTasks, Header, HTTPException
from fastapi.responses import PlainTextResponse, Response, JSONResponse

import config
import db
import agent
import whatsapp
import telegram
import telegram_bot
import paystack

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("samco-main")

# Maps an order's channel to the function that can message that customer back.
SENDERS = {
    "whatsapp": whatsapp.send_message,
    "telegram": telegram.send_message,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    logger.info("Database ready.")

    # Polling thread disabled in favor of high-speed /webhook endpoint
    # if config.TELEGRAM_BOT_TOKEN:
    #     thread = threading.Thread(target=telegram_bot.run_polling, daemon=True)
    #     thread.start()
    #     logger.info("Telegram bot polling thread started.")
    # else:
    #     logger.info("TELEGRAM_BOT_TOKEN not set — Telegram bot skipped.")

    yield


app = FastAPI(title="SAMCO Superstore", lifespan=lifespan)


@app.get("/api/health")
def health():
    return JSONResponse({"status": "ok", "service": "samco-superstore"})


# ---------------------------------------------------------------------------
# Telegram Webhook (Background Processing for instant 200 OK)
# ---------------------------------------------------------------------------

def _handle_incoming_telegram(chat_id: int, text: str):
    try:
        reply = agent.run_agent_turn(str(chat_id), text, channel="telegram")
    except Exception:
        logger.exception("Agent failed for Telegram chat %s", chat_id)
        reply = (
            "Sorry, something went wrong on our end. A staff member will "
            "follow up with you shortly."
        )
    try:
        telegram.send_message(chat_id, reply)
    except Exception:
        logger.exception("Failed to send Telegram reply to %s", chat_id)


@app.post("/webhook/telegram")
@app.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "Invalid JSON"}, status_code=400)

    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if chat_id and text:
        logger.info("Incoming Telegram message from %s: %s", chat_id, text)
        background_tasks.add_task(_handle_incoming_telegram, chat_id, text)

    return JSONResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# WhatsApp webhook (Twilio)
# ---------------------------------------------------------------------------

def _clean_phone(twilio_from: str) -> str:
    return twilio_from.replace("whatsapp:", "").lstrip("+")


def _handle_incoming_whatsapp(customer_id: str, body: str):
    try:
        reply = agent.run_agent_turn(customer_id, body, channel="whatsapp")
    except Exception:
        logger.exception("Agent failed for %s", customer_id)
        reply = (
            "Sorry, something went wrong on our end. A staff member will "
            "follow up with you shortly."
        )
    try:
        whatsapp.send_message(customer_id, reply)
    except Exception:
        logger.exception("Failed to send WhatsApp reply to %s", customer_id)


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(...),
):
    customer_id = _clean_phone(From)
    logger.info("Incoming WhatsApp message from %s: %s", customer_id, Body)
    background_tasks.add_task(_handle_incoming_whatsapp, customer_id, Body)
    return Response(content="<Response></Response>", media_type="application/xml")


# ---------------------------------------------------------------------------
# Paystack webhook — marks orders paid, replies on whichever channel ordered
# ---------------------------------------------------------------------------

@app.post("/webhook/paystack")
async def paystack_webhook(request: Request, x_paystack_signature: str = Header(None)):
    raw_body = await request.body()

    if not paystack.verify_webhook_signature(raw_body, x_paystack_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    event = payload.get("event")

    if event == "charge.success":
        data = payload.get("data", {})
        reference = data.get("reference")
        order = db.get_order_by_reference(reference)

        if order:
            db.update_order_status(reference, "paid")
            send = SENDERS.get(order["channel"])
            if send:
                try:
                    send(
                        order["customer_id"],
                        f"Payment received — thank you, {order['customer_name'] or ''}! "
                        f"Your order (₦{order['total_amount']:,}) is confirmed and being "
                        f"prepared for delivery to {order['delivery_address']}.",
                    )
                except Exception:
                    logger.exception("Failed to send payment confirmation for %s", reference)
            else:
                logger.warning("Unknown channel '%s' for order %s", order["channel"], reference)
        else:
            logger.warning("Paystack webhook for unknown reference: %s", reference)

    return PlainTextResponse("ok")
