from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# --- API Models ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    history: list[dict] = []


class ChatResponse(BaseModel):
    response: str
    session_id: str


# --- Domain Models ---
class Slot(BaseModel):
    slot_id: str
    court: str
    date: str
    time: str
    is_available: bool = True


class Booking(BaseModel):
    booking_id: str
    slot_id: str
    customer_name: str
    court: str
    date: str
    time: str
    created_at: str = datetime.now().isoformat()


class Court(BaseModel):
    court_id: str
    name: str
    type: str        # "Clay", "Hard", "Grass"
    location: str
    price: int       # price per hour in IDR


class CourtCreate(BaseModel):
    name: str
    type: str
    location: str
    price: int
