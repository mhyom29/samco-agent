# SAMCO Superstore — Bundled (website + AI sales agent, one process)

Everything in one project now: the customer-facing catalog website and the
Telegram AI sales agent run from a single command.

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

That one line gets you:
- The website, live at `http://localhost:8000/` (and `/furniture.html`,
  `/electronics.html`, etc.) — same site, just served by FastAPI instead of
  a plain file server.
- The Telegram sales bot, running in the background automatically.
- `/webhook/paystack` — ready for payment confirmations once you expose it.
- `/webhook/whatsapp` — ready for when you switch channels later, inert
  until Twilio is configured.

## Project layout

```
samco-agent/
  main.py            <- run this. Bundles everything together.
  agent.py            the AI sales brain (Gemini + tool calling)
  db.py                SQLite: carts, orders, conversation state
  products.py           41-item catalog (mirrors site/js/catalog.js)
  paystack.py           payment link generation
  telegram.py            Telegram Bot API wrapper
  telegram_bot.py          long-polling loop (used by main.py, or run alone)
  whatsapp.py               Twilio sender, parked for later
  site/                       the website — untouched, just now served by FastAPI
    index.html, furniture.html, electronics.html, groceries.html,
    beauty.html, baby.html, css/, js/, assets/
  requirements.txt
  .env.example
```

## 1. Install (Arch)

Arch's system Python is externally managed, so use a virtual environment
rather than installing packages system-wide — this is the standard Arch way,
not a workaround:

```bash
sudo pacman -S --needed python python-pip

cd samco-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

You'll need to run `source venv/bin/activate` again in any new terminal
session before running the app.

## 2. Get your three keys

**Telegram bot token** — message **@BotFather** on Telegram, send `/newbot`,
follow the prompts. You get a token immediately, no approval wait.

**Gemini API key** — free at
[aistudio.google.com/apikey](https://aistudio.google.com/apikey).

**Paystack test key** — create an account at
[paystack.com](https://paystack.com) → **Settings → API Keys & Webhooks** →
copy the key starting `sk_test_`.

## 3. Configure

```bash
cp .env.example .env
nano .env   # or your editor of choice
```

Fill in `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, `PAYSTACK_SECRET_KEY`. Leave
the Twilio lines blank for now.

## 4. Run it

```bash
source venv/bin/activate   # if not already active
uvicorn main:app --host 0.0.0.0 --port 8000
```

You should see log lines confirming the database is ready and the Telegram
bot logged in. Open `http://localhost:8000/` in a browser — that's the live
site. Message your bot on Telegram — that's the live agent, using the exact
same product data.

## 5. Optional: expose the Paystack webhook

Checkout already works without this step — the AI generates a real,
working Paystack link regardless. This just adds the automatic "payment
received!" message once a customer actually pays.

You need *something* public-facing pointed at port 8000. A few options,
roughly in order of how permanent you want this to be:

- **Quick test**: [ngrok](https://ngrok.com) or `cloudflared tunnel` — both
  installable via `pacman`/AUR, give you a public HTTPS URL in seconds.
- **Real deployment**: point a domain you own at this machine, put Nginx or
  Caddy in front of port 8000 for HTTPS, and use that domain directly.

Whichever you use, set the resulting URL + `/webhook/paystack` as the
Webhook URL in Paystack's dashboard (**Settings → API Keys & Webhooks**).

## Running it permanently (systemd)

For something you don't have to manually restart, a user-level systemd
service is the idiomatic Arch way to keep this alive across reboots —
solves the "phone dies, bot goes offline" problem from Termux entirely.

Create `~/.config/systemd/user/samco-agent.service`:

```ini
[Unit]
Description=SAMCO Superstore — website + AI sales agent
After=network-online.target

[Service]
WorkingDirectory=%h/samco-agent
ExecStart=%h/samco-agent/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=on-failure
EnvironmentFile=%h/samco-agent/.env

[Install]
WantedBy=default.target
```

Then:

```bash
systemctl --user daemon-reload
systemctl --user enable --now samco-agent.service

# check it's running / view logs
systemctl --user status samco-agent.service
journalctl --user -u samco-agent.service -f
```

`loginctl enable-linger $USER` keeps it running even when you're logged out
(useful if this is a home server rather than your daily laptop).

## Keeping the catalog in sync

`products.py` (the agent's brain) and `site/js/catalog.js` (the website)
list the same 41 products independently — update a price or add an item in
one, update the other to match. If this becomes annoying, the real fix is
having both read from one shared `products.json`; say the word and I'll
wire that up.

## Switching to WhatsApp later

1. Fill in `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and
   `TWILIO_WHATSAPP_FROM` in `.env`.
2. Point Twilio's webhook at `https://your-url/webhook/whatsapp`.
3. That's it — `agent.py`, `db.py`, and `products.py` never knew which
   channel they were talking to. You can run Telegram and WhatsApp at the
   same time if you want; orders are tagged by `channel` so Paystack
   confirmations route back correctly either way.

## Going to production

- **Prices are still placeholders** — go through `products.py` *and*
  `site/js/catalog.js` and correct every price before real customers see
  either one.
- **Paystack**: switch `PAYSTACK_SECRET_KEY` to your **live** key when ready.
- **WhatsApp**: for real customers you'll need an approved WhatsApp
  Business Sender through Twilio, or Meta's Cloud API directly.
- **Human fallback**: the AI already backs off and flags the SAMCO team for
  complaints, refunds, or bulk-pricing requests instead of trying to handle
  those itself. If you want it to also *ping you* directly (e.g. your own
  Telegram chat_id), that's a small addition.

## Cost notes

- Gemini Flash: per-token, cheap for short chat replies.
- Telegram: free.
- Twilio (when you switch): sandbox free, production billed per conversation.
- Paystack: percentage fee per successful transaction.
