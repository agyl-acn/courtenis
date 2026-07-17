# Architecture Context

This branch (`aws-deployment`) describes Courtenis as it is **deployed on
AWS**. The same application code runs locally; only the storage backend and
the entry point change. See "Local vs AWS Mapping" below for how each local
piece maps to a cloud service.

## Stack

| Layer     | Technology                          | Role                                        |
| --------- | ----------------------------------- | ------------------------------------------- |
| Frontend  | React + Vite + TypeScript           | User & admin UI, built to static files      |
| Styling   | Plain CSS with CSS custom properties| Courtenis design system (see ui-context.md) |
| Backend   | FastAPI + Python 3.12               | REST API, routing, business logic           |
| AI Agent  | OpenAI Agents SDK + LiteLLM + Gemini| Natural language → tool calls               |
| Storage   | SQLite (local) → DynamoDB (AWS)     | All persistent data                         |
| Adapter   | Mangum                              | Bridge from FastAPI (ASGI) to AWS Lambda    |

## AWS Stack (deployed)

The deployed application uses the following AWS services, all in
**us-east-1**:

| Service           | What it hosts / does                                              |
| ----------------- | ---------------------------------------------------------------- |
| **S3**            | Static website hosting for the built React frontend (`dist/`)    |
| **API Gateway**   | HTTP API — the public entry point; proxies all routes to Lambda  |
| **Lambda**        | Runs FastAPI + the AI agent via the Mangum adapter (Python 3.12) |
| **DynamoDB**      | 3 tables: `courtenis_slots`, `courtenis_bookings`, `courtenis_courts` |
| **IAM**           | Lambda execution role with `AmazonDynamoDBFullAccess` attached   |
| **Gemini API**    | External LLM (Google AI Studio) — called by the agent for reasoning |

Notes:
- **S3 only** (static website hosting) — CloudFront is not part of the
  deployed workshop stack.
- **API Gateway** is an HTTP API with a catch-all route (`ANY /{proxy+}`)
  whose integration target is the `courtenis-backend` Lambda.
- **Lambda** is packaged as a zip (`dist/lambda.zip`) with `src/` and the
  Python dependencies at the archive root; handler is
  `src.lambda_handler.handler`. `boto3`/`botocore` are stripped because the
  Lambda runtime already provides them.
- **DynamoDB** tables are `PAY_PER_REQUEST` with a single string partition
  key each (`slot_id`, `booking_id`, `court_id`). Tables are provisioned
  before deployment; the app never creates them.
- **Gemini** is reached over HTTPS using `GEMINI_API_KEY`; the model is set
  via `GEMINI_MODEL` (workshop default `gemini/gemini-2.5-flash-lite`).

## Local vs AWS Mapping

| Component      | Local                   | AWS                                        |
| -------------- | ----------------------- | ------------------------------------------ |
| Frontend serve | `vite dev` (port 5173)  | S3 static website hosting                  |
| Static assets  | Vite dev server         | S3 bucket (`npm run build` → `aws s3 sync`)|
| Backend serve  | `uvicorn` (port 8000)   | API Gateway (HTTP API) + Lambda            |
| Entry point    | `src.api:app`           | `src.lambda_handler.handler` (Mangum)      |
| Storage        | `courtenis.db` (SQLite) | DynamoDB (3 tables)                         |
| Storage module | `src/storage.py`        | `src/storage_dynamodb.py`                  |
| DB seeding     | FastAPI startup event   | `POST /admin/seed` (invoked once)          |
| LLM            | Gemini via LiteLLM      | Gemini via LiteLLM (unchanged)             |
| Secrets/config | `.env`                  | Lambda environment variables               |

The business logic (`api.py`, `agent.py`, `models.py`) is **identical**
between local and AWS. Only two things swap: the storage implementation
(via `storage_factory.py`) and the entry point (`lambda_handler.py`).

## Storage Abstraction

Storage is chosen at import time by `src/storage_factory.py`, driven by the
`STORAGE_BACKEND` environment variable:

```
STORAGE_BACKEND unset / "sqlite"  → src/storage.py           (local, SQLite)
STORAGE_BACKEND == "dynamodb"     → src/storage_dynamodb.py  (AWS, DynamoDB)
```

Both modules expose **identical function signatures**, so the rest of the
app (`api.py`, `agent.py`) imports `storage` from `storage_factory` and never
knows which backend is active. On Lambda, `STORAGE_BACKEND=dynamodb` selects
the DynamoDB implementation; on a laptop with the variable unset it falls
back to SQLite. This is why no business-logic code changes between local and
cloud.

`storage_dynamodb.py` specifics:
- Table names and region come from env vars (`SLOTS_TABLE`, `BOOKINGS_TABLE`,
  `COURTS_TABLE`, `AWS_REGION`).
- It does **not** create tables — only `init_db()` seeds them (courts + 180
  days of slots) and only when empty.
- Uses `Attr(...)` filter expressions to avoid DynamoDB reserved-word
  clashes on attributes like `date`, `time`, `name`, `type`, `location`.
- `update_court` is guarded by `attribute_exists(court_id)` so a missing
  court is not silently upserted.

## Request Flow (end to end on AWS)

```
Browser (S3-hosted React app)
   │  fetch() to the API Gateway URL
   ▼
API Gateway (HTTP API, ANY /{proxy+})
   │  proxies the request
   ▼
Lambda (courtenis-backend)
   │  Mangum adapts the event → ASGI → FastAPI (api.py)
   │  /chat routes into the AI agent (agent.py)
   ├─────────────► Gemini API (LiteLLM)   ── reasoning: which tool to call
   │  ◄──────────  tool decision
   ▼
DynamoDB (via storage_dynamodb.py)
   │  check_availability / get_courts / book_slot read & write items
   ▼
Response bubbles back: DynamoDB → Lambda → API Gateway → Browser
```

In plain terms: the browser loads the static site from S3, then calls the
API Gateway URL for data. API Gateway forwards every request to the Lambda
function, where Mangum hands it to FastAPI. For a chat message, the agent
asks Gemini what to do; Gemini decides which tool to call
(`check_availability`, `get_courts`, `book_slot`); the tool reads or writes
DynamoDB; and the result is returned back up the same chain to the browser.

## Project Structure

```
courtenis/
├── frontend/                  # React + Vite app (built → S3)
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/             # HomePage, AdminPage
│   │   ├── hooks/             # Custom React hooks
│   │   ├── api/               # Fetch wrappers to backend
│   │   └── styles/            # CSS custom properties + globals
│   ├── index.html
│   └── vite.config.ts
│
└── booking-agent/             # FastAPI app + AI agent
    ├── src/
    │   ├── agent.py            # AI agent + tools
    │   ├── api.py              # FastAPI routes
    │   ├── storage.py          # SQLite ops (local)
    │   ├── storage_dynamodb.py # DynamoDB ops (AWS)
    │   ├── storage_factory.py  # Backend selector (STORAGE_BACKEND)
    │   ├── models.py           # Pydantic models
    │   └── lambda_handler.py   # Mangum adapter (AWS only)
    ├── build_lambda_linux.sh   # Builds dist/lambda.zip on CloudShell/Linux
    ├── requirements.txt        # Local (includes uvicorn, boto3)
    └── requirements-lambda.txt # Lambda runtime-only (no uvicorn/boto3)
```

## System Boundaries

- `frontend/src/api/` — the only place allowed to fetch from the backend;
  components must not call fetch directly
- `booking-agent/src/storage_factory.py` — the single import point for
  storage; the rest of the app imports `storage` from here
- `booking-agent/src/storage.py` / `storage_dynamodb.py` — the only places
  allowed to touch the database; routes must not query the DB directly
- `booking-agent/src/agent.py` — all AI logic and tool definitions live
  here; routes only call `Runner.run()`
- `booking-agent/src/api.py` — routing and request validation only;
  no business logic here
- `booking-agent/src/lambda_handler.py` — Mangum wrapper only, no logic

## API Endpoints

| Method | Endpoint           | Description                            |
| ------ | ------------------ | -------------------------------------- |
| GET    | /health            | Health check                           |
| POST   | /chat              | Send a message to the AI agent         |
| POST   | /admin/seed        | Seed DynamoDB (once, after deploy)     |
| GET    | /courts            | List all courts                        |
| POST   | /courts            | Add a new court (admin)                |
| PUT    | /courts/{id}       | Update a court (admin)                 |
| DELETE | /courts/{id}       | Delete a court (admin)                 |
| GET    | /bookings          | List all bookings (admin)              |

`/admin/seed` exists specifically for AWS: Mangum runs with `lifespan="off"`,
so the FastAPI startup event (which seeds locally) never fires on Lambda. The
endpoint is idempotent — `init_db()` only seeds when a table is empty.

## Storage Model

- **SQLite / DynamoDB**: all data — courts, slots, bookings
- **DynamoDB tables** (AWS): `courtenis_courts` (PK `court_id`),
  `courtenis_slots` (PK `slot_id`), `courtenis_bookings` (PK `booking_id`)
- **No blob storage**: the app does not store files or images
  (court photos use external URLs or Unsplash for demo purposes)

## Auth and Access Model

- No authentication within the workshop scope
- Role is determined by route: `/` = user view, `/admin` = admin view
- No ownership checks — all data is globally accessible
- Lambda's access to DynamoDB is granted by its IAM execution role
  (`AmazonDynamoDBFullAccess`)

## Invariants

1. `storage.py` / `storage_dynamodb.py` are the only files allowed to
   interact with the database — no raw SQL or DB calls outside them
2. All storage access goes through `storage_factory.py`; nothing imports a
   concrete backend module directly
3. Agent tools may only call functions from the storage layer,
   never manipulate the DB directly
4. The frontend may only communicate with the backend via
   functions in `frontend/src/api/` — no fetch calls inside components
5. `lambda_handler.py` must contain no business logic — Mangum wrapper only
6. Environment variables (API keys, table names, backend selection) are read
   only via `os.getenv()` — no hardcoded secrets or config anywhere
7. Lambda holds no state between invocations — all state lives in DynamoDB
