# Courtenis

A tennis court booking platform with an AI assistant — built as a cloud workshop demo.

## What is Courtenis?

Courtenis is a full-stack web app that lets users book tennis courts in natural language.
Type "Book a hard court downtown for tomorrow at 3pm" and the AI agent handles the rest.

Built to demonstrate:
- React + Vite frontend with an admin panel
- FastAPI backend with an AI agent (Gemini via OpenAI Agents SDK)
- SQLite locally — designed to migrate to AWS Lambda + DynamoDB

## Project Structure

```
courtenis/
├── booking-agent/          # FastAPI backend + AI agent
│   ├── src/
│   │   ├── agent.py            # AI agent definition and tools
│   │   ├── api.py              # REST API endpoints (FastAPI)
│   │   ├── storage.py          # SQLite ops (DynamoDB-ready interface)
│   │   ├── models.py           # Pydantic request/response models
│   │   └── lambda_handler.py   # AWS Lambda adapter (Mangum)
│   ├── .env.example
│   └── requirements.txt
│
└── frontend/               # React + Vite + TypeScript UI
    ├── src/
    │   ├── pages/              # HomePage, AdminPage
    │   ├── components/         # Navbar, Chatbot, BookingCard, FeaturedCourts
    │   ├── components/admin/   # AdminSidebar, DashboardTab, CourtsTab, BookingsTab
    │   ├── api/                # Fetch wrappers — all backend calls go here
    │   └── styles/             # CSS custom properties (design system)
    ├── .env.example
    └── package.json
```

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **A free Gemini API key** — [get one at Google AI Studio](https://aistudio.google.com/apikey) (no credit card)

## Getting a Gemini API Key

1. Go to [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with a Google account
3. Click **Create API key**
4. Copy the key — you'll paste it into `booking-agent/.env` below

## Backend Setup

```bash
cd booking-agent

# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Gemini API key
cp .env.example .env
# Open .env and set GEMINI_API_KEY=your-key-here

# 4. Start the server
uvicorn src.api:app --reload
```

Backend: http://localhost:8000  
API docs: http://localhost:8000/docs

## Frontend Setup

Open a second terminal:

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Copy env file (defaults are already correct for local dev)
cp .env.example .env

# 3. Start the dev server
npm run dev
```

Frontend: http://localhost:5173

## What You Can Do

**User view** (`/`)
- Browse featured courts
- Fill in the booking form — the AI agent checks availability and confirms
- Use the floating chatbot (bottom-right) to ask in natural language:
  - "Any clay courts available tomorrow?"
  - "Book Court A at 10am on July 20"

**Admin view** (`/admin`)
- Dashboard: total bookings, active courts, today's bookings
- Courts: add, edit, delete courts
- Bookings: view all confirmed bookings

## Workshop Note

This is a demo project. It is intentionally simplified:

- **No authentication** — `/` is the user view, `/admin` is the admin view (no login)
- **SQLite locally** — `storage.py` has a DynamoDB-ready interface for AWS migration
- **No payments** — booking is confirmed by the AI agent, no payment step

AWS migration path (zero code changes to business logic):
| Component | Local | AWS |
|-----------|-------|-----|
| Frontend | `npm run dev` | S3 + CloudFront |
| Backend | `uvicorn` | API Gateway + Lambda (via Mangum) |
| Storage | `courtenis.db` | DynamoDB |
