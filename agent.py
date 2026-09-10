import json
import logging

from google import genai
from google.genai import errors, types

import config
import db
import products
import paystack

logger = logging.getLogger("samco-agent")

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(
            api_key=config.GEMINI_API_KEY,
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(
                    initial_delay=2.0,
                    attempts=8,
                    max_delay=65.0,
                    http_status_codes=[429, 500, 502, 503, 504],
                )
            ),
        )
    return _client


SYSTEM_INSTRUCTION = f"""
You are the AI sales assistant for {config.STORE_NAME}, a supermarket in Jos,
Plateau State, Nigeria. You're chatting with a customer who was previously
talking to a staff member — you've taken over so replies are fast and
available any time. The customer doesn't need to be told this explicitly;
just be warm, natural, and genuinely helpful, the way a good sales assistant
in-store would be.

How to work:
1. Product questions: ALWAYS use the search_products tool to check the real
   catalog before answering. Never guess a product, price, or unit size from
   memory — if it's not returned by the tool, it's not something SAMCO stocks
   right now. If nothing matches, say so honestly and offer to have a staff
   member confirm, rather than inventing an answer.
2. Building an order: use add_to_cart / remove_from_cart / view_cart. Always
   read back the product name, quantity, unit, and price to the customer so
   they can confirm before you add it — don't assume quantities.
3. Closing the sale: once the customer confirms they're done adding items,
   ask for their full name and delivery address (email is optional — if they
   don't have one, proceed without it). Then call the checkout tool. It will
   create the order and return a secure Paystack payment link — send that
   link to the customer clearly and let them know their order will be
   prepared as soon as payment reflects.
4. Tone: short, warm, chat-length replies — a few lines, not paragraphs.
   Nigerian and friendly. You can understand and respond naturally to Pidgin
   English or casual phrasing (e.g. "I wan buy", "abeg", "how much be this").
   All prices are in Naira (₦).
5. Know your limits: if the customer is upset, wants a refund, has a
   complaint, wants bulk/wholesale pricing outside the listed prices, or
   directly asks for a human — tell them warmly that you're flagging this
   for the SAMCO team to personally follow up, and stop trying to close the
   sale yourself in that message.
6. Never invent delivery timelines, stock levels, or discounts that the
   tools didn't give you.
"""

TOOLS = [
    {
        "type": "function",
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
    {
        "type": "function",
        "name": "view_cart",
        "description": "Get the customer's current cart contents and running total in Naira.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "type": "function",
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
    {
        "type": "function",
        "name": "remove_from_cart",
        "description": "Remove a product entirely from the customer's cart.",
        "parameters": {
            "type": "object",
            "properties": {"product_name": {"type": "string"}},
            "required": ["product_name"],
        },
    },
    {
        "type": "function",
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
]


def _dispatch_tool(name: str, args: dict, customer_id: str, channel: str) -> dict:
    """Executes a tool call and returns a JSON-serializable result."""
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


def run_agent_turn(customer_id: str, user_message: str, channel: str = "telegram") -> str:
    """
    Runs one full turn of the conversation with Gemini retry backoff and
    rate-limit error handling.
    """
    client = _get_client()
    previous_id = db.get_last_interaction_id(customer_id)

    try:
        interaction = client.interactions.create(
            model=config.GEMINI_MODEL,
            system_instruction=SYSTEM_INSTRUCTION,
            input=user_message,
            tools=TOOLS,
            previous_interaction_id=previous_id,
        )

        rounds = 0
        while rounds < config.MAX_TOOL_ROUNDS:
            function_calls = [s for s in interaction.steps if s.type == "function_call"]
            if not function_calls:
                break

            results_input = []
            for call in function_calls:
                result = _dispatch_tool(call.name, call.arguments or {}, customer_id, channel)
                results_input.append(
                    {
                        "type": "function_result",
                        "name": call.name,
                        "call_id": call.id,
                        "result": [{"type": "text", "text": json.dumps(result)}],
                    }
                )

            interaction = client.interactions.create(
                model=config.GEMINI_MODEL,
                system_instruction=SYSTEM_INSTRUCTION,
                tools=TOOLS,
                previous_interaction_id=interaction.id,
                input=results_input,
            )
            rounds += 1

        db.set_last_interaction_id(customer_id, interaction.id, channel=channel)

        reply = (interaction.output_text or "").strip()
        if not reply:
            reply = "Sorry, I didn't quite catch that — could you say that again?"
        return reply

    except errors.ClientError as e:
        if e.code == 429 or "429" in str(e) or "quota" in str(e).lower():
            logger.warning("Gemini 429 Rate Limit hit for customer %s", customer_id)
            return (
                "We're receiving high order traffic right now! "
                "Please wait 30 seconds and try your message again."
            )
        logger.exception("Gemini ClientError for customer %s", customer_id)
        return "Sorry, something went wrong on our end. A staff member will follow up shortly."

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower():
            logger.warning("Gemini quota exception hit for customer %s: %s", customer_id, e)
            return (
                "We're receiving high order traffic right now! "
                "Please wait 30 seconds and try your message again."
            )
        logger.exception("Unexpected error in agent turn for %s", customer_id)
        return "Sorry, something went wrong on our end. A staff member will follow up shortly."
