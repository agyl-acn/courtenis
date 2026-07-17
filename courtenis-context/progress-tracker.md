# Progress Tracker

Update this file after every meaningful implementation change.

## Current Phase

In Progress

## Current Goal

Project structure setup — frontend (React + Vite) and backend (FastAPI)
running locally and connected to each other.

## Completed

- Courtenis design system — finalized
- Backend boilerplate: FastAPI + SQLite + AI agent (Gemini) — done
  - `models.py`, `storage.py`, `agent.py`, `api.py`, `lambda_handler.py`
  - Agent tools: `check_availability`, `book_slot`
- All 6 context files created and filled in
- **Frontend scaffold** — done
  - Vite + React + TypeScript in `frontend/`
  - Folder structure: `src/components/`, `src/pages/`, `src/hooks/`, `src/api/`, `src/styles/`
  - `src/styles/globals.css` with all CSS custom properties (colors, typography, shadows, radius)
  - Google Fonts: Playfair Display + Inter loaded in `index.html`
  - `.env` with `VITE_API_BASE_URL=http://localhost:8000`
  - Vite proxy: `/api/*` → `http://localhost:8000/*`
  - `npm run dev` confirmed starting on http://localhost:5173

- **Homepage** — done
  - `src/pages/HomePage.tsx` — hero section with full-bleed Unsplash photo, overlay, left copy column, right booking card
  - `src/components/Navbar.tsx` — pill-shaped sticky navbar, logo, nav links with active dot, membership CTA
  - `src/components/BookingCard.tsx` — navy header, 6-field form (location, type, date, time, duration, players), yellow CTA, submits to `POST /chat` via agent
  - `src/components/FeaturedCourts.tsx` — 3-card grid (clay/hard/grass) with colored headers and Available badge
  - `src/api/bookings.ts` — `sendBookingMessage()` wrapping `POST /chat`; all icons from lucide-react
  - `tsc --noEmit` passes clean; `npm run dev` starts without errors

- **Chatbot widget** — done
  - `src/components/Chatbot.tsx` — fixed bottom-right, toggle button (yellow circle), slide-up panel (360×480)
  - `src/components/Chatbot.css` — translateY animation (150ms ease), typing indicator (3-dot bounce), user/agent bubbles
  - `src/api/chat.ts` — `sendChatMessage(message, sessionId)` → `POST /chat`, returns `response` field
  - Welcome message shown on open; conversation kept in React state (resets on refresh)
  - Auto-scroll to latest message; input focused when panel opens; Enter key submits
  - `tsc --noEmit` clean; `npm run dev` starts without errors

- **Chatbot conversation history** — done
  - `booking-agent/src/models.py` — added `history: list[dict] = []` to `ChatRequest`
  - `booking-agent/src/api.py` — builds SDK input list from history + new message; plain `{"role", "content"}` dicts only (no `"type"` key) to route through EasyInputMessageParam
  - `frontend/src/api/chat.ts` — `sendChatMessage()` now accepts `history: HistoryMessage[]`
  - `frontend/src/components/Chatbot.tsx` — snapshots `messages` before each send, maps `'agent'` → `'assistant'` for SDK role names

- **Admin page** — done
  - React Router added (`react-router-dom`): `/` → HomePage, `/admin` → AdminPage
  - `frontend/src/pages/AdminPage.tsx` — sidebar + tab switcher layout
  - `frontend/src/pages/AdminPage.css` — layout + shared admin utilities (`admin-table`, `admin-page-title`, `admin-state-msg`)
  - `frontend/src/components/admin/AdminSidebar.tsx/.css` — 240px navy sidebar, yellow active state, logo circle
  - `frontend/src/components/admin/StatsCard.tsx/.css` — stat card (value + label)
  - `frontend/src/components/admin/DashboardTab.tsx/.css` — 3-card stats grid (Total Bookings, Active Courts, Today's Bookings)
  - `frontend/src/components/admin/CourtsTab.tsx/.css` — table + Add/Edit/Delete + modal form, type badges
  - `frontend/src/components/admin/BookingsTab.tsx/.css` — read-only bookings table, most recent first
  - `frontend/src/api/courts.ts` — getCourts, createCourt, updateCourt, deleteCourt; 404 → empty array
  - `frontend/src/api/bookings.ts` — added Booking type + getBookings(); fixed reply→response mismatch
  - `frontend/src/styles/globals.css` — added --color-white, --overlay-bg, badge color variables
  - `tsc --noEmit` clean

- **Backend: Courts CRUD** — done
  - `booking-agent/src/models.py` — added `Court` (court_id, name, type, location, price:int IDR) + `CourtCreate`
  - `booking-agent/src/storage.py` — `courts` table in `init_db()`, seeds 3 courts (Baseline Grounds/Clay/Central Park/85000, Net & Rally Club/Hard/Sudirman/95000, Ace Courts/Grass/Kebayoran/110000); added `get_all_courts`, `get_court_by_id`, `create_court`, `update_court`, `delete_court` (all with `# → DynamoDB:` comments)
  - `booking-agent/src/api.py` — `GET/POST /courts`, `PUT/DELETE /courts/{court_id}`; 404 on missing court
  - `booking-agent/src/agent.py` — added `get_courts` tool, registered in agent tools list
  - `frontend/src/api/courts.ts` + `CourtsTab.tsx` — aligned field to `price` (IDR), display `Rp{price}/hr`
  - Verified: `GET /courts` returns 3 seeded courts; full POST→PUT→DELETE cycle works; missing ID → 404

- **Slot seeding extended** — done
  - `booking-agent/src/storage.py` — seed loop `range(7)` → `range(180)` (~6 months ahead)
  - `init_db()` now prints a reminder when existing data is found: delete `courtenis.db` + restart uvicorn to re-seed
  - Re-seed required: old `courtenis.db` only had 7 days of slots

- **DynamoDB storage prep (AWS)** — done (branch `aws-deployment`, not committed)
  - `booking-agent/src/storage_dynamodb.py` — boto3 drop-in mirroring `storage.py` signatures; 3 tables (courtenis_slots/bookings/courts), names + region from env; `init_db()` does NOT create tables, only seeds (180-day slots + 3 courts) when empty; uses `Attr` to avoid DynamoDB reserved-word clashes (date/time/name/type/location); `update_court` guarded by `attribute_exists` to avoid upsert
  - `booking-agent/src/storage_factory.py` — selects backend via `STORAGE_BACKEND` env (`sqlite` default / `dynamodb`)
  - `booking-agent/src/api.py` + `agent.py` — import `storage` from `storage_factory` (was `from src import storage`)
  - `booking-agent/requirements.txt` — added `boto3>=1.34.0`
  - Verified local (no `STORAGE_BACKEND`): factory → `src.storage`; server serves `/courts` (3) + agent `get_courts` works; DynamoDB local path never imports boto3; both new modules `py_compile` clean

- **Lambda build packaging (AWS)** — done (branch `aws-deployment`)
  - `booking-agent/build_lambda.py` — builds `dist/lambda.zip` with cross-platform pip flags (`--platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all:`); zip root holds `src/` + deps directly; robust `_force_rmtree` retry (Windows/OneDrive lock workaround); prints size + confirms `src/lambda_handler.py` inside
  - Handler: `src.lambda_handler.handler`
  - **Slim deps**: `booking-agent/requirements-lambda.txt` (runtime-only, excludes uvicorn); build now installs from it instead of `requirements.txt`
  - **Manual seed**: `booking-agent/src/api.py` — added `POST /admin/seed` (calls `storage.init_db()`); needed because Mangum runs with `lifespan="off"` so FastAPI startup never fires on Lambda; idempotent via init_db's "only seed if empty" guard
  - Verified: zip built (64.16 MB, `src/lambda_handler.py` present); local SQLite unchanged — `/courts`=3, `/admin/seed` returns `{"status":"seeded"}` and is idempotent
  - **Size note**: still 64 MB — dropping uvicorn doesn't help (mcp pulls it transitively; bulk is boto3/botocore). Over Lambda's 50 MB direct-upload cap → deploy via S3
  - **Deploy caveat**: binary-only resolution forces `openai-agents==0.2.0` (local venv uses a newer one) — verify agent code runs on Lambda before relying on it

- **Lambda build moved to Linux/CloudShell** — done (branch `aws-deployment`)
  - Root cause of the version problem: `mcp` declares `pywin32; sys_platform == "win32"`; pip's `--platform` flag does NOT override marker evaluation, so a Windows host demands pywin32 (no Linux wheel) and either fails or backtracks `openai-agents` to ancient 0.2.0. Local WSL/Docker unavailable → build on AWS CloudShell instead
  - `booking-agent/requirements-lambda.txt` — pinned to local venv set (openai-agents==0.17.4, fastapi==0.136.3, litellm==1.83.0, mangum==0.21.0, pydantic==2.13.4, pydantic-settings==2.14.1, python-dotenv==1.2.2); NO boto3/botocore (Lambda runtime provides them), NO uvicorn
  - `booking-agent/build_lambda_linux.sh` — plain `pip install --target build/` on Linux (no --platform hacks), strips boto3/botocore/s3transfer/jmespath, copies src/, zips to dist/lambda.zip (src/ at root), prints size
  - `.gitattributes` — forces `*.sh` to LF so the script runs on Linux
  - Build to be run in CloudShell; expected under 50 MB once boto3/botocore excluded

- **Chatbot UX improvements** — done (branch `aws-deployment`, local-tested)
  - **Language matching**: `agent.py` `get_instructions` — reply in the user's language (ID↔EN). Verified EN→EN, ID→ID (headers translated too)
  - **Markdown rendering**: `frontend` — added `react-markdown` + `remark-gfm`; `Chatbot.tsx` renders agent bubbles via `<ReactMarkdown remarkPlugins={[remarkGfm]}>`, user bubbles stay plain text; `Chatbot.css` `.chatbot-markdown` styles (bold=navy, bullet lists, GFM tables with navy header) matching the design system; agent bubble max-width bumped to 92% for tables
  - **Agent markdown output**: `get_courts` returns a markdown table; `check_availability` instructed to render as a **Court/Time** table (slot_id kept internal); no more raw `**` in chat
  - **Court awareness**: instructions tell the agent to use `get_courts` to resolve court names / "cheapest" / type, then book the matching court. Verified: "cheapest court" → Baseline Grounds
  - **Mock payment receipt**: `book_slot` returns a markdown receipt table (Booking ID, Court, Date, Time, Price, Payment: PAID (mock)). Price looked up from courts by name
  - **Data alignment**: slot seed court names changed `Court A/B/C` → real names (`Baseline Grounds`/`Net & Rally Club`/`Ace Courts`) in BOTH `storage.py` and `storage_dynamodb.py`, so slots map to real courts and `book_slot` can look up price. **Requires re-seed**: delete `courtenis.db` + restart uvicorn (seed only runs when empty)
  - Verified with isolated temp-DB agent run (real Gemini): all 4 improvements pass; `tsc --noEmit` clean; backend `py_compile` clean

- **Customer name on bookings** — done (branch `aws-deployment`, local-tested)
  - `models.py` — added `customer_name: str` to `Booking`
  - `storage.py` — `bookings` table gains `customer_name` column (fresh CREATE TABLE, re-seed required); `create_booking(slot, customer_name)` persists it; `get_all_bookings` returns it via `Booking(**row)`
  - `storage_dynamodb.py` — `create_booking(slot, customer_name)` writes the attribute; `_booking_from_item` reads it (`.get` default "")
  - `agent.py` — `book_slot(slot_id, customer_name)`; instructions require asking for the name before booking; receipt table gains a **Name** row
  - `frontend/src/api/bookings.ts` — `Booking` interface gains `customer_name`
  - `frontend/src/components/admin/BookingsTab.tsx` — added **Name** column (order: Booking ID, Name, Court, Date, Time, Created At)
  - Verified (temp-DB real agent): agent asks for name when missing → books on name given → receipt shows Name → `get_all_bookings` returns it; `tsc --noEmit` + backend `py_compile` clean
  - **Requires re-seed**: bookings schema changed → delete `courtenis.db` + restart uvicorn

- **AWS deployment docs** — done (branch `aws-deployment`)
  - `courtenis-context/architecture.md` — rewritten to describe the DEPLOYED AWS state: added an AWS Stack table (S3 static hosting, API Gateway HTTP API, Lambda, DynamoDB 3 tables, IAM role + AmazonDynamoDBFullAccess, external Gemini), refined the local↔AWS mapping (SQLite→DynamoDB, uvicorn→Lambda/Mangum, vite dev→S3, startup event→`/admin/seed`), documented the `storage_factory.py` backend switch (`STORAGE_BACKEND`), added an end-to-end request-flow diagram (Browser→S3→API Gateway→Lambda→Gemini→DynamoDB), corrected S3+CloudFront → **S3 static website hosting only**, updated invariants for the dual storage backends
  - `README.md` — rewritten as a self-contained **AWS CloudShell deployment guide** (no local dev). Chose option (a) — self-contained quickstart — because the fuller `participant-guide.md` is gitignored and can't be referenced from the committed repo. Covers: prereqs (Udacity sandbox, us-east-1, Gemini key), plain-language "how services talk", why the Lambda zip is built the way it is (CloudShell Linux / cp312 / boto3+uvicorn stripped), full CloudShell steps end-to-end (build → DynamoDB → Lambda → env vars → IAM → API Gateway → seed → S3), and a troubleshooting table (cp312 vs cp313, openai 2.44 pin, CORS allow_origins, sourceIp on manual invoke, stale table data)
  - `slides.md` — NEW brief for the Day 2 slide-generating agent (**gitignored**, not committed). Part A: stack roles in-app + concepts to teach (agent vs LLM, tools, reasoning loop, Lambda-as-agent-handler, migration insight) + end-to-end narrative. Part B: 15-slide structure for ~30 min then demo. No MCP mentioned
  - `.gitignore` — added `slides.md` and `participant-guide.md` (workshop authoring files, not committed)
  - `participant-guide.md` — Day 2 handout kept locally as the source of truth for README steps; gitignored, not committed

- **CORS fix for AWS deployment** — done (branch `aws-deployment`)
  - `booking-agent/src/api.py` — `allow_origins` `["http://localhost:5173"]` → `["*"]` so a fresh deploy from the repo serves the S3 frontend without manual CloudShell edits; `allow_credentials` `True` → `False` (browsers reject wildcard origin + credentials together). `allow_methods`/`allow_headers` unchanged (`["*"]`)
  - Verified: `from src.api import app` imports cleanly via venv; CORSMiddleware present

## In Progress

- AWS deployment (branch `aws-deployment`): provision DynamoDB tables, Lambda + API Gateway (upload zip via S3), S3/CloudFront for frontend

## Next Up

1. ~~**Frontend scaffold**~~ — done
2. ~~**Homepage**~~ — done
3. ~~**Chatbot widget**~~ — done
4. ~~**Admin page**~~ — done
5. ~~**Backend: courts API**~~ — done (court CRUD + `get_courts` agent tool)
6. **Connect everything** — verify all flows work end-to-end

## Open Questions

- ~~Hero photo~~ → Unsplash URL directly (decided: demo-appropriate, no local asset needed)
- ~~Chatbot history~~ → frontend-only React state, resets on page refresh (decided: simplest, no backend changes needed)
- Admin: should there be a confirmation step before deleting a court
  or cancelling a booking?

## Architecture Decisions

- **SQLite for local**: Chosen for being lightweight, zero-config, and
  Docker-free. `storage.py` interface is designed for easy DynamoDB migration.
- **React + Vite**: Chosen over plain HTML because the build output is
  static files that can be uploaded directly to S3. Migration path to AWS
  is clear with no code changes required.
- **Gemini via LiteLLM**: Free tier is sufficient for workshop demo.
  Model can be swapped by changing an env var.
- **No auth**: Simplified for workshop scope. Role is determined by route
  (`/` vs `/admin`).

## Session Notes

- Backend lives in `backend/`, already has Gemini agent + SQLite storage
- Frontend does not exist yet — start from Vite scaffold
- Full design system is in `ui-context.md`
- All target endpoints are in `architecture.md` under API Endpoints
- Run backend: `cd backend && uvicorn src.api:app --reload`
- Run frontend (after scaffold): `cd frontend && npm run dev`
- Backend runs on port 8000, frontend dev server on port 5173
