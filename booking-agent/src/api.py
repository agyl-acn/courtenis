"""
FastAPI wrapper for the agent.
This is the HTTP interface — identical between local and Lambda.
The only difference on AWS is lambda_handler.py adding the Mangum adapter.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agents import Runner
from src.models import ChatRequest, ChatResponse, Court, CourtCreate
from src.agent import booking_agent
from src.storage_factory import storage

app = FastAPI(
    title="Courtenis Booking Agent",
    description="AI-powered tennis court booking via natural language",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize the database on server start."""
    storage.init_db()


@app.get("/health")
async def health():
    """Health check endpoint — useful for AWS monitoring."""
    return {
        "status": "healthy",
        "service": "courtenis-booking-agent"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the booking agent and receive a response.
    The agent will automatically check availability and/or book based on context.
    """
    try:
        # Build the input list for Runner.run().
        # Use {"role", "content"} only — no "type" key.
        # The SDK's chatcmpl_converter routes items with exactly these two keys
        # through EasyInputMessageParam, which accepts plain string content.
        # Adding "type": "message" triggers the ResponseOutputMessage path instead,
        # which expects content to be a list of blocks and crashes on plain strings.
        sdk_input = [
            {"role": item["role"], "content": item["content"]}
            for item in request.history
        ]
        sdk_input.append({"role": "user", "content": request.message})

        result = await Runner.run(booking_agent, sdk_input)
        return ChatResponse(
            response=result.final_output,
            session_id=request.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bookings")
async def get_bookings():
    """Return all bookings — useful for the admin view and demos."""
    bookings = storage.get_all_bookings()
    return {
        "total": len(bookings),
        "bookings": [b.model_dump() for b in bookings]
    }


@app.get("/courts")
async def get_courts():
    """Return all courts — used by the admin panel and the booking UI."""
    courts = storage.get_all_courts()
    return {
        "total": len(courts),
        "courts": [c.model_dump() for c in courts]
    }


@app.post("/courts", response_model=Court)
async def add_court(court: CourtCreate):
    """Add a new court (admin)."""
    return storage.create_court(court)


@app.put("/courts/{court_id}", response_model=Court)
async def edit_court(court_id: str, court: CourtCreate):
    """Update an existing court (admin)."""
    updated = storage.update_court(court_id, court)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Court '{court_id}' not found.")
    return updated


@app.delete("/courts/{court_id}")
async def remove_court(court_id: str):
    """Delete a court (admin)."""
    deleted = storage.delete_court(court_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Court '{court_id}' not found.")
    return {"deleted": court_id}
