"""
SAMCO Superstore — everything in one process.

    uvicorn main:app --host 0.0.0.0 --port 8000

This single command now gets you:
  - The website (site/) served at http://localhost:8000/
  - The Telegram sales bot running in the background (long-polling —
    started automatically on startup if TELEGRAM_BOT_TOKEN is set)
  - /webhook/paystack — payment confirmation (needs a public URL to be
    reachable by Paystack; the site + Telegram bot work fine without it)
  - /webhook/whatsapp — ready for when you switch channels later (needs
    Twilio configured in .env; does nothing until then)

Nothing about the website changed — it's the exact same static files you'd
get opening site/index.html directly. FastAPI is just serving them now
instead of Python's http.server.
"""

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Form, BackgroundTasks, Header, HTTPException
from fastapi.responses import PlainTextResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles

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

    if config.TELEGRAM_BOT_TOKEN:
        thread = threading.Thread(target=telegram_bot.run_polling, daemon=True)
        thread.start()
        logger.info("Telegram bot started in the background.")
    else:
        logger.info("TELEGRAM_BOT_TOKEN not set — Telegram bot skipped. "
                     "Website and Paystack webhook still work fine.")

    yield
    # daemon thread stops automatically when the process exits — nothing to clean up


app = FastAPI(title="SAMCO Superstore", lifespan=lifespan)


@app.get("/api/health")
def health():
    return JSONResponse({"status": "ok", "service": "samco-superstore"})


# ---------------------------------------------------------------------------
# WhatsApp webhook (Twilio) — for later, inert until Twilio vars are set
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


# ---------------------------------------------------------------------------
# Utility: reset a stuck conversation
# ---------------------------------------------------------------------------

@app.post("/admin/reset/{customer_id}")
def reset_conversation(customer_id: str):
    db.reset_conversation(customer_id)
    return {"reset": customer_id}


# ---------------------------------------------------------------------------
# The website — mounted last so it doesn't shadow the routes above.
# site/index.html, site/furniture.html etc. become / , /furniture.html, ...
# ---------------------------------------------------------------------------

#app.mount("/", StaticFiles(directory="site", html=True), name="site")
