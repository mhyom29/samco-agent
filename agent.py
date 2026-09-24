import json
import logging

from groq import Groq

import config
import db
import products
import paystack

logger = logging.getLogger("samco-agent")

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client


SYSTEM_INSTRUCTION = f"""
You are the AI sales assistant for {config.STORE_NAME}, a supermarket in Abuja, Nigeria. You assist customers directly via web chat and messaging 
channels to make shopping fast, easy, and available 24/7. Be warm, natural, 
and genuinely helpful, the way a great sales assistant in-store would be.

How to work:
1. Searching the Catalog: ALWAYS use the search_products tool before giving prices 
   or availability. 
   - When a customer pastes an order list with quantities or prices (e.g. 
     'storm spray (100 units) x1 – ₦3,500'), extract ONLY the core item name 
     (e.g. 'storm spray') to search. Strip out units, prices, multipliers, and brackets.
   - If a search returns 0 results, try ONE broader search term (e.g. 'storm'). 
     If that also fails, stop searching immediately, state that it's not in stock, 
     and offer to have staff check the shelves. Never guess or invent stock.
2. Building & Handling Orders: When a customer expresses intent to order or buy items:
   - Search the catalog for each requested item.
   - If an item matches, read back the exact catalog product name, unit size, and price, 
     then ask the customer to confirm before calling add_to_cart.
   - Use view_cart or remove_from_cart whenever the user asks to modify their order.
3. Closing the Sale: Once the customer confirms they are ready to checkout:
   - Ask for their full name and delivery address (email is optional).
   - Call the checkout tool to generate the Paystack payment link.
   - Send the Paystack link clearly and confirm that delivery will be scheduled 
     once payment is received.
4. Tone: Short, warm, chat-length replies — a few lines max. Friendly Nigerian tone. 
   Understand and respond naturally to Pidgin English or casual phrasing 
   (e.g., "I wan buy", "abeg", "how much be this"). All prices are in Naira (₦).
5. Know Your Limits: If the customer is upset, wants a refund, requests bulk/wholesale 
   pricing, or asks for a human — warmly state that you are flagging the chat for 
   the SAMCO team to follow up, and pause closing the sale.
6. Never invent delivery timelines, stock levels, or discounts that tools didn't provide.
"""

# Groq/OpenAI tool-calling format: {"type": "function", "function": {name, description, parameters}}
# (Gemini's format was flatter — {"type": "function", "name": ..., ...} — this is the one
# structural thing that had to change when the tool definitions moved providers.)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Search the SAMCO Superstore catalog by keyword or category "
                "(e.g. 'rice', 'lotion', 'diapers', 'chair', 'TV'). Returns "
                "matching products with their exact name, unit, and price in "
                "Naira. Always use this before telling a customer a price or "
                "whether something is available."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Keyword to search for."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "view_cart",
            "description": "Get the customer's current cart contents and running total in Naira.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": (
                "Add a product to the customer's cart. product_name must exactly "
                "match a name returned by search_products. If the product is "
                "already in the cart, this increases the quantity."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "quantity": {
                        "type": "integer",
                        "description": "Number of units to add. Defaults to 1.",
                    },
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_from_cart",
            "description": "Remove a product entirely from the customer's cart.",
            "parameters": {
                "type": "object",
                "properties": {"product_name": {"type": "string"}},
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "checkout",
            "description": (
                "Finalize the order once the customer has confirmed their cart "
                "and given their name and delivery address. Creates the order "
                "and a Paystack payment link. Only call this after explicit "
                "confirmation from the customer — never checkout on their behalf "
                "without them agreeing to the final cart and total first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string"},
                    "delivery_address": {"type": "string"},
                    "email": {
                        "type": "string",
                        "description": "Customer email for the payment receipt. Optional — omit if they don't have one.",
                    },
                },
                "required": ["customer_name", "delivery_address"],
            },
        },
    },
]


def _dispatch_tool(name: str, args: dict, customer_id: str, channel: str) -> dict:
    """Executes a tool call and returns a JSON-serializable result. Provider-agnostic — unchanged from the Gemini version."""
    try:
        if name == "search_products":
            results = products.search_products(args.get("query", ""))
            return {"results": results, "count": len(results)}

        if name == "view_cart":
            cart = db.get_cart(customer_id)
            return {"cart": cart, "total_naira": db.cart_total(customer_id)}

        if name == "add_to_cart":
            product_name = args.get("product_name", "")
            quantity = int(args.get("quantity") or 1)
            product = products.find_product_exact(product_name)
            if not product:
                return {"error": f"'{product_name}' isn't an exact catalog match. Use search_products first."}
            db.add_to_cart(customer_id, product["name"], product["unit"], product["price"], quantity)
            return {
                "added": product["name"],
                "quantity": quantity,
                "cart": db.get_cart(customer_id),
                "total_naira": db.cart_total(customer_id),
            }

        if name == "remove_from_cart":
            removed = db.remove_from_cart(customer_id, args.get("product_name", ""))
            return {
                "removed": removed,
                "cart": db.get_cart(customer_id),
                "total_naira": db.cart_total(customer_id),
            }

        if name == "checkout":
            cart = db.get_cart(customer_id)
            if not cart:
                return {"error": "Cart is empty — add items with add_to_cart before checking out."}

            total = db.cart_total(customer_id)
            safe_id = "".join(c for c in customer_id if c.isalnum())
            email = args.get("email") or f"{safe_id}@{config.DEFAULT_CUSTOMER_EMAIL_DOMAIN}"
            reference = paystack.generate_reference(customer_id)

            try:
                link = paystack.create_payment_link(
                    email=email,
                    amount_naira=total,
                    reference=reference,
                    metadata={
                        "customer_id": customer_id,
                        "channel": channel,
                        "customer_name": args.get("customer_name"),
                        "items": cart,
                    },
                )
            except RuntimeError as e:
                logger.error("Paystack error: %s", e)
                return {"error": f"Could not create payment link right now: {e}. Apologize and say a staff member will follow up to complete payment."}

            db.create_order(
                customer_id=customer_id,
                channel=channel,
                customer_name=args.get("customer_name"),
                delivery_address=args.get("delivery_address"),
                email=email,
                items=cart,
                total_amount=total,
                reference=reference,
                payment_link=link["authorization_url"],
            )
            db.clear_cart(customer_id)

            return {
                "order_created": True,
                "total_naira": total,
                "payment_link": link["authorization_url"],
                "reference": reference,
            }

        return {"error": f"Unknown tool '{name}'"}

    except Exception as e:
        logger.exception("Tool dispatch failed for %s", name)
        return {"error": f"Internal error running {name}: {e}"}


def _is_rate_limit_error(e: Exception) -> bool:
    err_str = str(e).lower()
    status_code = getattr(e, "status_code", None)
    return status_code == 429 or "429" in err_str or "rate_limit" in err_str or "rate limit" in err_str


def run_agent_turn(customer_id: str, user_message: str, channel: str = "telegram") -> str:
    """
    Runs one full turn of the conversation against Groq. Unlike Gemini's
    Interactions API, Groq/OpenAI-style chat completions are stateless per
    call — we load and persist the full message history ourselves via db.py,
    trimmed to MAX_HISTORY_MESSAGES to stay under the free-tier TPM budget.
    """
    client = _get_client()
    history = db.get_conversation_history(customer_id)

    messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}] + history
    messages.append({"role": "user", "content": user_message})

    try:
        rounds = 0
        while rounds < config.MAX_TOOL_ROUNDS:
            completion = client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
            message = completion.choices[0].message
            tool_calls = message.tool_calls

            if not tool_calls:
                messages.append({"role": "assistant", "content": message.content or ""})
                break

            # Groq's assistant message with tool_calls must be preserved in the
            # history exactly as returned before the tool results are appended,
            # or the next call will reject the conversation as malformed.
            messages.append({
                "role": "assistant",
                "content": message.content or None,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {"name": call.function.name, "arguments": call.function.arguments},
                    }
                    for call in tool_calls
                ],
            })

            for call in tool_calls:
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = _dispatch_tool(call.function.name, args, customer_id, channel)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result),
                })

            rounds += 1
        else:
            # Hit MAX_TOOL_ROUNDS without a final text reply.
            messages.append({
                "role": "assistant",
                "content": "Sorry, that's taking longer than expected — could you try again?",
            })

        # Persist everything except the system prompt (re-added fresh each turn).
        db.save_conversation_history(customer_id, messages[1:], channel=channel)

        reply = (messages[-1].get("content") or "").strip()
        if not reply:
            reply = "Sorry, I didn't quite catch that — could you say that again?"
        return reply

    except Exception as e:
        if _is_rate_limit_error(e):
            logger.warning("Groq rate limit hit for customer %s", customer_id)
            return (
                "We're receiving high order traffic right now! "
                "Please wait 30 seconds and try your message again."
            )
        logger.exception("Unexpected error in agent turn for %s", customer_id)
        return "Sorry, something went wrong on our end. A staff member will follow up shortly."
