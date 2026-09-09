import os
from dotenv import load_dotenv

load_dotenv()

# --- Gemini ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")

# --- Telegram (active channel for now) ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# --- Twilio WhatsApp (for later — kept configured but not run by default) ---
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "")  # e.g. whatsapp:+14155238886

# --- Paystack ---
PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY", "")
PAYSTACK_CALLBACK_URL = os.environ.get("PAYSTACK_CALLBACK_URL", "")

# --- Store ---
STORE_NAME = os.environ.get("STORE_NAME", "SAMCO Superstore")
DEFAULT_CUSTOMER_EMAIL_DOMAIN = os.environ.get("DEFAULT_CUSTOMER_EMAIL_DOMAIN", "samcosuperstore.ng")

# --- Database ---
DB_PATH = os.environ.get("DB_PATH", "samco_agent.db")

# --- Misc ---
MAX_TOOL_ROUNDS = int(os.environ.get("MAX_TOOL_ROUNDS", "6"))
