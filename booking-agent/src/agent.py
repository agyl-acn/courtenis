"""
Agent definition and tools.
This is the AI core — the agent decides when to check availability,
when to book, and understands natural language from the user.
"""

import os
from datetime import datetime
from typing import Optional
from agents import Agent, function_tool
from agents.extensions.models.litellm_model import LitellmModel
from src.storage_factory import storage

# Gemini model to use — can be changed via env var:
# - gemini/gemini-2.0-flash   → fastest, free, good for demos
# - gemini/gemini-1.5-pro     → smarter, more limited free tier
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini/gemini-2.0-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


# ─── Tools ────────────────────────────────────────────────────────
# Docstrings here are critical — they are what the AI reads
# to understand when and how to call each tool.

@function_tool
def check_availability(date: str, time: Optional[str] = None) -> str:
    """
    Check available tennis court slots for a given date.

    Args:
        date: Date in YYYY-MM-DD format (e.g. "2024-12-15")
        time: Optional specific time in HH:MM format (e.g. "14:00")

    Returns:
        List of available slots with their slot_ids, or a message if none found.
    """
    slots = storage.get_available_slots(date, time)

    if not slots:
        msg = f"No available slots for {date}"
        if time:
            msg += f" at {time}"
        return msg

    # Each line carries the slot_id for the agent to use internally when booking.
    # The agent is instructed to present Court + Time to the user as a markdown
    # table and to NOT surface the slot_id.
    result = f"Available slots for {date}:\n"
    for slot in slots:
        result += f"  - Court: {slot.court} | Time: {slot.time} | slot_id (internal): \"{slot.slot_id}\"\n"

    return result


@function_tool
def get_courts() -> str:
    """
    Get all tennis courts with their real details (name, type, location, price).
    Use when the user asks about courts, refers to a court by name, or wants a
    recommendation (e.g. "the cheapest court", "a clay court").

    Returns:
        A markdown table of all courts with type, location, and price per hour.
    """
    courts = storage.get_all_courts()

    if not courts:
        return "No courts are currently available."

    result = "| Court | Type | Location | Price/hour |\n"
    result += "| --- | --- | --- | --- |\n"
    for court in courts:
        result += f"| {court.name} | {court.type} | {court.location} | Rp{court.price:,} |\n"

    return result


@function_tool
def book_slot(slot_id: str, customer_name: str) -> str:
    """
    Book a tennis court slot by slot_id for a named customer.

    Args:
        slot_id: The slot ID from check_availability results
        customer_name: The customer's name. Ask the user for this before
            booking if you don't already have it — do not guess or leave blank.

    Returns:
        A markdown "receipt" table confirming the booking, or an error message.
    """
    slot = storage.get_slot_by_id(slot_id)

    if not slot:
        return f"Slot '{slot_id}' not found."

    if not slot.is_available:
        return f"Slot '{slot_id}' is no longer available. Please choose another slot."

    try:
        storage.mark_slot_unavailable(slot_id)
        booking = storage.create_booking(slot, customer_name)

        # Look up the court's price (slots are seeded with real court names,
        # so slot.court matches a court record).
        courts = storage.get_all_courts()
        price = next((c.price for c in courts if c.name == booking.court), None)
        price_str = f"Rp{price:,}" if price is not None else "—"

        # Return a tidy markdown receipt — the chatbot renders this as a table.
        return (
            "Booking confirmed! Here is your receipt:\n\n"
            "| Field | Detail |\n"
            "| --- | --- |\n"
            f"| Booking ID | {booking.booking_id} |\n"
            f"| Name | {booking.customer_name} |\n"
            f"| Court | {booking.court} |\n"
            f"| Date | {booking.date} |\n"
            f"| Time | {booking.time} |\n"
            f"| Price | {price_str} |\n"
            "| Payment | PAID (mock) |\n"
        )
    except Exception as e:
        return f"Booking failed: {str(e)}"


# ─── Agent Instructions ───────────────────────────────────────────

def get_instructions(context, agent) -> str:
    """Dynamic instructions — always includes the current date and time."""
    now = datetime.now()
    current_datetime = now.strftime("%Y-%m-%d %H:%M (%A)")

    return f"""You are a helpful tennis court booking assistant for Courtenis.

CURRENT DATE AND TIME: {current_datetime}

LANGUAGE:
- Always reply in the SAME language the user writes in. If they write in
  Indonesian, respond in Indonesian; if English, respond in English. Match
  their language for every message, including table headers where natural.

WORKFLOW:
1. When a user wants to book, ALWAYS check availability first (check_availability)
2. Present the available options clearly
3. Before confirming a booking, make sure you have the customer's NAME.
   If you don't already know it, ask for it first — do not book without a name.
4. Once you have both the chosen slot AND the customer's name, call book_slot
   with the exact slot_id and the customer_name.
5. Show the booking receipt returned by book_slot back to the user

COURTS:
- Use get_courts to learn the real courts (name, type, location, price).
- When the user refers to a court by name (e.g. "book Baseline Grounds") or by
  a quality (e.g. "the cheapest court", "a clay court"), call get_courts, pick
  the matching court, then check availability for that court's name and book it.
- Never invent court names, prices, or locations — always use get_courts data.

FORMATTING (responses render as markdown in the chat):
- Present availability as a markdown table with columns **Court** and **Time**.
  Do NOT show the internal slot_id to the user — use it only to call book_slot.
- Use **bold** for key values and bullet lists where helpful.
- When book_slot returns a receipt table, pass it through to the user as-is.

GUIDELINES:
- Convert relative dates ("tomorrow", "next Monday") to YYYY-MM-DD format
- If no time is specified, show all available slots for that day
- When booking, always use the exact slot_id string from check_availability results. Never construct or guess the slot_id.
- Ignore duration or player count — just use slot_id to book.
- Be friendly and concise
- If an error occurs, explain it clearly and offer alternatives

IMPORTANT: You control the conversation flow.
Decide autonomously when to check availability versus when to proceed with booking."""


# ─── Agent Instance ───────────────────────────────────────────────
# LitellmModel is the bridge between OpenAI Agents SDK and Gemini.
# To switch back to OpenAI, remove the `model` parameter —
# the SDK will automatically pick up OPENAI_API_KEY from the environment.

booking_agent = Agent(
    name="Courtenis Booking Agent",
    instructions=get_instructions,
    tools=[get_courts, check_availability, book_slot],
    model=LitellmModel(
        model=GEMINI_MODEL,
        api_key=GEMINI_API_KEY,
    ),
)
