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

    result = f"Available slots for {date}:\n"
    for slot in slots:
        result += f"  - {slot.court} at {slot.time} → slot_id to book: \"{slot.slot_id}\"\n"

    return result


@function_tool
def get_courts() -> str:
    """
    Get all available tennis courts with details.
    Use when the user asks about courts, types, locations, or pricing.

    Returns:
        A formatted list of all courts with type, location, and price per hour.
    """
    courts = storage.get_all_courts()

    if not courts:
        return "No courts are currently available."

    result = "Available courts:\n"
    for court in courts:
        result += (
            f"  - {court.name} ({court.type}) at {court.location} "
            f"— Rp{court.price:,}/hour\n"
        )

    return result


@function_tool
def book_slot(slot_id: str) -> str:
    """
    Book a tennis court slot by slot_id.

    Args:
        slot_id: The slot ID from check_availability results

    Returns:
        Booking confirmation with details, or an error message.
    """
    slot = storage.get_slot_by_id(slot_id)

    if not slot:
        return f"Slot '{slot_id}' not found."

    if not slot.is_available:
        return f"Slot '{slot_id}' is no longer available. Please choose another slot."

    try:
        storage.mark_slot_unavailable(slot_id)
        booking = storage.create_booking(slot)

        return (
            f"Booking confirmed!\n"
            f"  Booking ID : {booking.booking_id}\n"
            f"  Court      : {booking.court}\n"
            f"  Date       : {booking.date}\n"
            f"  Time       : {booking.time}"
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

WORKFLOW:
1. When a user wants to book, ALWAYS check availability first (check_availability)
2. Present the available options clearly
3. Once the user confirms a slot, book it using book_slot
4. Confirm the booking details back to the user

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
