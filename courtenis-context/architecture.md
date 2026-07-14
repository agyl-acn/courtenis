# Architecture Context

## Stack

| Layer     | Technology                          | Role                                        |
| --------- | ----------------------------------- | ------------------------------------------- |
| Frontend  | React + Vite + TypeScript           | User & admin UI, served from browser        |
| Styling   | Plain CSS with CSS custom properties| Courtenis design system (see ui-context.md) |
| Backend   | FastAPI + Python                    | REST API, routing, business logic           |
| AI Agent  | OpenAI Agents SDK + LiteLLM + Gemini| Natural language → tool calls               |
| Storage   | SQLite (local) → DynamoDB (AWS)     | All persistent data                         |
| Adapter   | Mangum                              | Bridge from FastAPI to AWS Lambda           |

## Local vs AWS Mapping

| Component      | Local                  | AWS                        |
| -------------- | ---------------------- | -------------------------- |
| Frontend serve | `vite dev`             | S3 + CloudFront            |
| Backend serve  | `uvicorn`              | API Gateway + Lambda       |
| Storage        | `courtenis.db` (SQLite)| DynamoDB                   |
| Static assets  | Vite dev server        | S3                         |

## Project Structure

```
courtenis/
├── frontend/                  # React + Vite app
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # HomePage, AdminPage
│   │   ├── hooks/             # Custom React hooks
│   │   ├── api/               # Fetch wrappers to backend
│   │   └── styles/            # CSS custom properties + globals
│   ├── index.html
│   └── vite.config.ts
│
└── backend/                   # FastAPI app
    ├── src/
    │   ├── agent.py           # AI agent + tools
    │   ├── api.py             # FastAPI routes
    │   ├── storage.py         # SQLite ops (interface ready for DynamoDB)
    │   ├── models.py          # Pydantic models
    │   └── lambda_handler.py  # Mangum adapter (AWS only)
    ├── .env
    └── requirements.txt
```

## System Boundaries

- `frontend/src/api/` — the only place allowed to fetch from the backend;
  components must not call fetch directly
- `backend/src/storage.py` — the only place allowed to touch the database;
  routes must not query the DB directly
- `backend/src/agent.py` — all AI logic and tool definitions live here;
  routes only call `Runner.run()`
- `backend/src/api.py` — routing and request validation only;
  no business logic here

## API Endpoints

| Method | Endpoint           | Description                        |
| ------ | ------------------ | ---------------------------------- |
| GET    | /health            | Health check                       |
| POST   | /chat              | Send a message to the AI agent     |
| GET    | /courts            | List all courts                    |
| POST   | /courts            | Add a new court (admin)            |
| PUT    | /courts/{id}       | Update a court (admin)             |
| DELETE | /courts/{id}       | Delete a court (admin)             |
| GET    | /bookings          | List all bookings (admin)          |
| GET    | /slots             | Check available slots (query: date)|

## Storage Model

- **SQLite / DynamoDB**: all data — courts, slots, bookings
- **No blob storage**: the app does not store files or images
  (court photos use external URLs or Unsplash for demo purposes)

## Auth and Access Model

- No authentication within the workshop scope
- Role is determined by route: `/` = user view, `/admin` = admin view
- No ownership checks — all data is globally accessible

## Invariants

1. `storage.py` is the only file allowed to interact with the database —
   no raw SQL or DB calls outside this file
2. Agent tools may only call functions from `storage.py`,
   never manipulate the DB directly
3. The frontend may only communicate with the backend via
   functions in `frontend/src/api/` — no fetch calls inside components
4. `lambda_handler.py` must contain no business logic — Mangum wrapper only
5. Environment variables (API keys, config) are read only via `os.getenv()` —
   no hardcoded secrets anywhere
