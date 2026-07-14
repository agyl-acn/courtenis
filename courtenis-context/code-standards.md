# Code Standards

## General

- One file, one responsibility — do not mix unrelated concerns
- Fix root causes, do not layer workarounds
- All configuration and secrets via environment variables —
  no hardcoded values anywhere

## TypeScript (Frontend)

- Strict mode enabled throughout
- Avoid `any` — use explicit interfaces or narrowly scoped types
- All component props must have a defined interface or type
- All backend fetches go through functions in `src/api/` —
  never call fetch directly inside a component

## React

- Functional components only, use hooks
- One component per file
- Components in `components/` must be reusable and route-agnostic
- Page components in `pages/` may handle routing and data fetching
- Custom hooks in `hooks/` for logic shared across more than one place

## CSS

- Use CSS custom properties from `ui-context.md` — no hardcoded hex values
- One CSS file per component, imported directly into the component file
- Follow the border radius scale defined in `ui-context.md`
- All transitions `150ms ease` unless there is a specific reason otherwise

## Python (Backend)

- Type hints on all functions
- Docstrings on all functions in `storage.py` and `agent.py`
- Use Pydantic models for all request and response shapes
- No logic in `lambda_handler.py` — Mangum wrapper only

## API Routes

- Validate and parse request input before any logic runs
  (Pydantic handles this automatically)
- Return consistent, predictable response shapes
- Error responses always include a descriptive `detail` field
- No direct database calls in route handlers — always go through `storage.py`

## Data and Storage

- All DB operations live in `storage.py` — no exceptions
- Storage functions include a comment `# → DynamoDB: ...` to aid migration
- No state stored inside the Lambda / FastAPI process

## File Organization

- `frontend/src/components/` — reusable UI components
- `frontend/src/pages/` — HomePage, AdminPage
- `frontend/src/api/` — all fetch wrappers to the backend
- `frontend/src/hooks/` — custom React hooks
- `frontend/src/styles/` — global CSS, custom properties
- `backend/src/` — all backend Python modules
