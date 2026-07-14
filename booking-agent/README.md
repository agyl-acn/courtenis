# Courtenis — Booking Agent Backend

AI-powered booking agent using **OpenAI Agents SDK + FastAPI + Gemini**.
Runs locally with SQLite — designed to migrate to AWS Lambda + DynamoDB.

---

## Project Structure

```
backend/
├── src/
│   ├── __init__.py
│   ├── models.py          # Pydantic models (request/response/domain)
│   ├── storage.py         # SQLite now → DynamoDB later
│   ├── agent.py           # AI agent + tools
│   ├── api.py             # FastAPI endpoints
│   └── lambda_handler.py  # Mangum adapter (AWS only)
├── .env.example
├── requirements.txt
└── README.md
```

---

## Local Setup

### 1. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and fill in GEMINI_API_KEY
```

### 3. Run the server

```bash
uvicorn src.api:app --reload
```

Server: http://localhost:8000
API docs: http://localhost:8000/docs

---

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Chat with the agent
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Any courts available tomorrow at 3pm?"}'

# View all bookings
curl http://localhost:8000/bookings
```

---

## Migrating to AWS

Only two things change when deploying to Lambda:

| Component | Local                   | AWS                         |
|-----------|-------------------------|-----------------------------|
| Storage   | `storage.py` (SQLite)   | Swap implementation to DynamoDB |
| Handler   | `uvicorn src.api:app`   | `src.lambda_handler.handler`|
| Config    | `.env` file             | Lambda Environment Variables|

`agent.py`, `api.py`, and `models.py` require **zero changes**.
