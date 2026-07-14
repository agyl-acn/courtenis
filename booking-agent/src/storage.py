"""
Storage layer - SQLite for local development.
Interface is designed to mirror DynamoDB semantics,
so migrating to AWS is a matter of swapping this implementation only.
"""

import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Optional
from src.models import Slot, Booking, Court, CourtCreate

DB_PATH = "courtenis.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables and seed initial slot data."""
    conn = get_connection()
    cursor = conn.cursor()

    # Slots table — all available schedules
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            slot_id TEXT PRIMARY KEY,
            court TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            is_available INTEGER DEFAULT 1
        )
    """)

    # Bookings table — all confirmed bookings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id TEXT PRIMARY KEY,
            slot_id TEXT NOT NULL,
            court TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Courts table — all bookable courts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courts (
            court_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            location TEXT NOT NULL,
            price INTEGER NOT NULL
        )
    """)

    # Seed courts if the table is empty
    cursor.execute("SELECT COUNT(*) FROM courts")
    court_count = cursor.fetchone()[0]

    if court_count == 0:
        seed_courts = [
            ("Baseline Grounds", "Clay", "Central Park", 85000),
            ("Net & Rally Club", "Hard", "Sudirman", 95000),
            ("Ace Courts", "Grass", "Kebayoran", 110000),
        ]
        for name, court_type, location, price in seed_courts:
            cursor.execute(
                "INSERT INTO courts VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4())[:8].upper(), name, court_type, location, price)
            )

    # Seed slots for the next 7 days if the table is empty
    cursor.execute("SELECT COUNT(*) FROM slots")
    count = cursor.fetchone()[0]

    if count == 0:
        # Use the real court names (same as the seeded courts) so slots map to
        # actual courts — the agent can resolve names and look up prices.
        courts = ["Baseline Grounds", "Net & Rally Club", "Ace Courts"]
        times = ["08:00", "10:00", "13:00", "15:00", "17:00", "19:00"]

        # Seed ~6 months ahead so dates well into 2026 have availability.
        for day_offset in range(180):
            date = (datetime.now() + timedelta(days=day_offset)).strftime("%Y-%m-%d")
            for court in courts:
                for time in times:
                    slot_id = f"{date}_{court.replace(' ', '')}_{time.replace(':', '')}"
                    cursor.execute(
                        "INSERT OR IGNORE INTO slots VALUES (?, ?, ?, ?, 1)",
                        (slot_id, court, date, time)
                    )

    conn.commit()
    conn.close()

    if count == 0:
        print("Database initialized — seeded slots for the next 180 days.")
    else:
        print(
            "Database initialized (existing data found — slots NOT re-seeded).\n"
            "  NOTE: to apply the extended 180-day seed, stop uvicorn, delete "
            "courtenis.db, then restart uvicorn so the DB re-seeds fresh."
        )


# ─── Slot Operations ──────────────────────────────────────────────

def get_available_slots(date: str, time: Optional[str] = None) -> list[Slot]:
    """
    Return available slots for a given date and optional time.
    → DynamoDB: query GSI by date, filter is_available = True
    """
    conn = get_connection()
    cursor = conn.cursor()

    if time:
        cursor.execute(
            "SELECT * FROM slots WHERE date = ? AND time = ? AND is_available = 1",
            (date, time)
        )
    else:
        cursor.execute(
            "SELECT * FROM slots WHERE date = ? AND is_available = 1",
            (date,)
        )

    rows = cursor.fetchall()
    conn.close()

    return [Slot(**dict(row)) for row in rows]


def get_slot_by_id(slot_id: str) -> Optional[Slot]:
    """
    Return a single slot by ID.
    → DynamoDB: get_item by PK slot_id
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM slots WHERE slot_id = ?", (slot_id,))
    row = cursor.fetchone()
    conn.close()

    return Slot(**dict(row)) if row else None


def mark_slot_unavailable(slot_id: str):
    """
    Mark a slot as unavailable after it has been booked.
    → DynamoDB: update_item set is_available = False
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE slots SET is_available = 0 WHERE slot_id = ?",
        (slot_id,)
    )
    conn.commit()
    conn.close()


# ─── Booking Operations ───────────────────────────────────────────

def create_booking(slot: Slot) -> Booking:
    """
    Create a new booking and persist it to the database.
    → DynamoDB: put_item into bookings table
    """
    booking = Booking(
        booking_id=str(uuid.uuid4())[:8].upper(),
        slot_id=slot.slot_id,
        court=slot.court,
        date=slot.date,
        time=slot.time,
        created_at=datetime.now().isoformat()
    )

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?)",
        (booking.booking_id, booking.slot_id, booking.court,
         booking.date, booking.time, booking.created_at)
    )
    conn.commit()
    conn.close()

    return booking


def get_all_bookings() -> list[Booking]:
    """
    Return all bookings, most recent first.
    → DynamoDB: scan bookings table (or query by GSI)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    return [Booking(**dict(row)) for row in rows]


# ─── Court Operations ─────────────────────────────────────────────

def get_all_courts() -> list[Court]:
    """
    Return all courts.
    → DynamoDB: scan courts table
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courts ORDER BY name")
    rows = cursor.fetchall()
    conn.close()

    return [Court(**dict(row)) for row in rows]


def get_court_by_id(court_id: str) -> Optional[Court]:
    """
    Return a single court by ID.
    → DynamoDB: get_item by PK court_id
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courts WHERE court_id = ?", (court_id,))
    row = cursor.fetchone()
    conn.close()

    return Court(**dict(row)) if row else None


def create_court(court: CourtCreate) -> Court:
    """
    Create a new court and persist it to the database.
    → DynamoDB: put_item into courts table
    """
    new_court = Court(
        court_id=str(uuid.uuid4())[:8].upper(),
        name=court.name,
        type=court.type,
        location=court.location,
        price=court.price,
    )

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO courts VALUES (?, ?, ?, ?, ?)",
        (new_court.court_id, new_court.name, new_court.type,
         new_court.location, new_court.price)
    )
    conn.commit()
    conn.close()

    return new_court


def update_court(court_id: str, court: CourtCreate) -> Optional[Court]:
    """
    Update an existing court. Returns the updated court, or None if not found.
    → DynamoDB: update_item by PK court_id
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE courts SET name = ?, type = ?, location = ?, price = ? WHERE court_id = ?",
        (court.name, court.type, court.location, court.price, court_id)
    )
    conn.commit()
    updated = cursor.rowcount
    conn.close()

    if updated == 0:
        return None

    return Court(
        court_id=court_id,
        name=court.name,
        type=court.type,
        location=court.location,
        price=court.price,
    )


def delete_court(court_id: str) -> bool:
    """
    Delete a court by ID. Returns True if a court was deleted, False otherwise.
    → DynamoDB: delete_item by PK court_id
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM courts WHERE court_id = ?", (court_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    return deleted > 0
