"""
Storage layer — DynamoDB for AWS deployment.

This is a drop-in replacement for storage.py: it exposes the exact same
function signatures, so swapping backends is a matter of importing this
module instead (see storage_factory.py).

Tables are NOT created here — they are provisioned in the AWS console (or
IaC) before deployment. init_db() only seeds data when the tables are empty.

Table names and region are read from environment variables so the same
code runs against dev/prod tables without changes.
"""

import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

from src.models import Slot, Booking, Court, CourtCreate

# ─── Configuration (env-driven) ───────────────────────────────────
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SLOTS_TABLE = os.getenv("SLOTS_TABLE", "courtenis_slots")
BOOKINGS_TABLE = os.getenv("BOOKINGS_TABLE", "courtenis_bookings")
COURTS_TABLE = os.getenv("COURTS_TABLE", "courtenis_courts")

# Module-level resource — reused across Lambda invocations (warm containers).
_dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

slots_table = _dynamodb.Table(SLOTS_TABLE)
bookings_table = _dynamodb.Table(BOOKINGS_TABLE)
courts_table = _dynamodb.Table(COURTS_TABLE)


# ─── Internal helpers ─────────────────────────────────────────────

def _scan_all(table, **kwargs) -> list[dict]:
    """
    Scan a table fully, following pagination.
    Fine for workshop scale; a GSI + query is the production path.
    """
    items: list[dict] = []
    response = table.scan(**kwargs)
    items.extend(response.get("Items", []))
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"], **kwargs)
        items.extend(response.get("Items", []))
    return items


def _is_empty(table) -> bool:
    """Return True if the table has no items (cheap Limit=1 probe)."""
    return table.scan(Limit=1).get("Count", 0) == 0


def _slot_from_item(item: dict) -> Slot:
    """Build a Slot from a raw DynamoDB item (coerces DynamoDB types)."""
    return Slot(
        slot_id=item["slot_id"],
        court=item["court"],
        date=item["date"],
        time=item["time"],
        is_available=bool(item["is_available"]),
    )


def _court_from_item(item: dict) -> Court:
    """Build a Court from a raw DynamoDB item (Decimal price → int)."""
    return Court(
        court_id=item["court_id"],
        name=item["name"],
        type=item["type"],
        location=item["location"],
        price=int(item["price"]),
    )


def _booking_from_item(item: dict) -> Booking:
    """Build a Booking from a raw DynamoDB item."""
    return Booking(
        booking_id=item["booking_id"],
        slot_id=item["slot_id"],
        customer_name=item.get("customer_name", ""),
        court=item["court"],
        date=item["date"],
        time=item["time"],
        created_at=item["created_at"],
    )


# ─── Initialization / Seeding ─────────────────────────────────────

def init_db():
    """
    Seed courts and slots IF the tables are empty. Does NOT create tables
    (those are provisioned in AWS before deployment).
    """
    # Seed courts if empty
    if _is_empty(courts_table):
        seed_courts = [
            ("Baseline Grounds", "Clay", "Central Park", 85000),
            ("Net & Rally Club", "Hard", "Sudirman", 95000),
            ("Ace Courts", "Grass", "Kebayoran", 110000),
        ]
        with courts_table.batch_writer() as batch:
            for name, court_type, location, price in seed_courts:
                batch.put_item(Item={
                    "court_id": str(uuid.uuid4())[:8].upper(),
                    "name": name,
                    "type": court_type,
                    "location": location,
                    "price": price,
                })
        print("DynamoDB: seeded 3 courts.")
    else:
        print("DynamoDB: courts table not empty — courts NOT re-seeded.")

    # Seed slots (180 days ahead) if empty
    if _is_empty(slots_table):
        # Use the real court names (same as the seeded courts) so slots map to
        # actual courts — the agent can resolve names and look up prices.
        courts = ["Baseline Grounds", "Net & Rally Club", "Ace Courts"]
        times = ["08:00", "10:00", "13:00", "15:00", "17:00", "19:00"]

        with slots_table.batch_writer() as batch:
            for day_offset in range(180):
                date = (datetime.now() + timedelta(days=day_offset)).strftime("%Y-%m-%d")
                for court in courts:
                    for time in times:
                        slot_id = f"{date}_{court.replace(' ', '')}_{time.replace(':', '')}"
                        batch.put_item(Item={
                            "slot_id": slot_id,
                            "court": court,
                            "date": date,
                            "time": time,
                            "is_available": True,
                        })
        print("DynamoDB: seeded slots for the next 180 days.")
    else:
        print("DynamoDB: slots table not empty — slots NOT re-seeded.")


# ─── Slot Operations ──────────────────────────────────────────────

def get_available_slots(date: str, time: Optional[str] = None) -> list[Slot]:
    """
    Return available slots for a given date and optional time.
    DynamoDB: scan with a FilterExpression (Attr avoids reserved-word clashes
    on 'date' and 'time').
    """
    filter_expr = Attr("date").eq(date) & Attr("is_available").eq(True)
    if time:
        filter_expr = filter_expr & Attr("time").eq(time)

    items = _scan_all(slots_table, FilterExpression=filter_expr)
    return [_slot_from_item(item) for item in items]


def get_slot_by_id(slot_id: str) -> Optional[Slot]:
    """
    Return a single slot by ID.
    DynamoDB: get_item by PK slot_id.
    """
    item = slots_table.get_item(Key={"slot_id": slot_id}).get("Item")
    return _slot_from_item(item) if item else None


def mark_slot_unavailable(slot_id: str):
    """
    Mark a slot as unavailable after it has been booked.
    DynamoDB: update_item set is_available = False.
    """
    slots_table.update_item(
        Key={"slot_id": slot_id},
        UpdateExpression="SET is_available = :f",
        ExpressionAttributeValues={":f": False},
    )


# ─── Booking Operations ───────────────────────────────────────────

def create_booking(slot: Slot, customer_name: str) -> Booking:
    """
    Create a new booking and persist it.
    DynamoDB: put_item into the bookings table.
    """
    booking = Booking(
        booking_id=str(uuid.uuid4())[:8].upper(),
        slot_id=slot.slot_id,
        customer_name=customer_name,
        court=slot.court,
        date=slot.date,
        time=slot.time,
        created_at=datetime.now().isoformat(),
    )

    bookings_table.put_item(Item={
        "booking_id": booking.booking_id,
        "slot_id": booking.slot_id,
        "customer_name": booking.customer_name,
        "court": booking.court,
        "date": booking.date,
        "time": booking.time,
        "created_at": booking.created_at,
    })

    return booking


def get_all_bookings() -> list[Booking]:
    """
    Return all bookings, most recent first.
    DynamoDB: scan bookings table, sort by created_at desc in-process.
    """
    items = _scan_all(bookings_table)
    bookings = [_booking_from_item(item) for item in items]
    bookings.sort(key=lambda b: b.created_at, reverse=True)
    return bookings


# ─── Court Operations ─────────────────────────────────────────────

def get_all_courts() -> list[Court]:
    """
    Return all courts, sorted by name.
    DynamoDB: scan courts table.
    """
    items = _scan_all(courts_table)
    courts = [_court_from_item(item) for item in items]
    courts.sort(key=lambda c: c.name)
    return courts


def get_court_by_id(court_id: str) -> Optional[Court]:
    """
    Return a single court by ID.
    DynamoDB: get_item by PK court_id.
    """
    item = courts_table.get_item(Key={"court_id": court_id}).get("Item")
    return _court_from_item(item) if item else None


def create_court(court: CourtCreate) -> Court:
    """
    Create a new court and persist it.
    DynamoDB: put_item into the courts table.
    """
    new_court = Court(
        court_id=str(uuid.uuid4())[:8].upper(),
        name=court.name,
        type=court.type,
        location=court.location,
        price=court.price,
    )

    courts_table.put_item(Item={
        "court_id": new_court.court_id,
        "name": new_court.name,
        "type": new_court.type,
        "location": new_court.location,
        "price": new_court.price,
    })

    return new_court


def update_court(court_id: str, court: CourtCreate) -> Optional[Court]:
    """
    Update an existing court. Returns the updated court, or None if not found.
    DynamoDB: put_item guarded by attribute_exists(court_id) so a missing
    court is not silently created (upsert).
    """
    try:
        courts_table.put_item(
            Item={
                "court_id": court_id,
                "name": court.name,
                "type": court.type,
                "location": court.location,
                "price": court.price,
            },
            ConditionExpression="attribute_exists(court_id)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return None
        raise

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
    DynamoDB: delete_item with ReturnValues=ALL_OLD to detect existence.
    """
    response = courts_table.delete_item(
        Key={"court_id": court_id},
        ReturnValues="ALL_OLD",
    )
    return "Attributes" in response
