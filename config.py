import os
from dotenv import load_dotenv

load_dotenv()

# --- Groq ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
# llama-3.3-70b-versatile was decommissioned by Groq on 2026-08-16.
# openai/gpt-oss-120b is Groq's current recommended replacement for
# tool-calling workloads. qwen/qwen3.6-27b is the lighter/cheaper alternative
# if you need more headroom under the free-tier TPM limit.
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

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
# How many past messages (excluding the system prompt) to keep per customer.
# Groq's free tier is tight on tokens-per-minute, and Gemini's stateful
# interaction IDs don't exist here — we manage history ourselves, so it
# needs an explicit cap or long conversations eventually blow the TPM budget.
MAX_HISTORY_MESSAGES = int(os.environ.get("MAX_HISTORY_MESSAGES", "20"))
