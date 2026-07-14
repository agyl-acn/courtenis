# AI Workflow Rules

## Approach

Build this project incrementally using a spec-driven workflow.
Context files define what to build, how to build it, and the current
state of progress. Always implement against these specs —
do not infer or invent behavior from scratch.

## Scoping Rules

- Work on one feature unit at a time
- Prefer small, verifiable increments over large speculative changes
- Do not combine unrelated system boundaries in a single implementation step

## When to Split Work

Split an implementation step if it combines:

- Frontend and backend changes simultaneously (unless trivial)
- More than one unrelated API route
- UI changes and agent/tool changes at the same time
- Behavior not clearly defined in the context files

If a change cannot be verified end-to-end quickly,
the scope is too broad — split it.

## Handling Missing Requirements

- Do not invent product behavior not defined in the context files
- If a requirement is ambiguous, resolve it in the relevant context file
  before implementing
- If a requirement is missing, add it as an open question in
  `progress-tracker.md` before continuing

## Protected Files

Do not modify the following unless explicitly instructed:

- `backend/src/lambda_handler.py` — Mangum wrapper only, no logic
- Anything inside `frontend/node_modules/`
- `.env` — do not overwrite; only append new variables if needed

## Keeping Docs in Sync

Update the relevant context file whenever implementation changes:

- System architecture or boundaries
- Storage model decisions
- Code conventions or standards
- Feature scope

`progress-tracker.md` in particular must be updated after every completed unit.

## Migration Mindfulness

Every implementation decision should account for the AWS migration path:

- Storage operations in `storage.py` always include a DynamoDB equivalent comment
- No hardcoded localhost URLs — use the `VITE_API_BASE_URL` environment
  variable in the frontend
- Backend must not store in-process state (Lambda is stateless)

## Before Moving to the Next Unit

1. The current unit works end-to-end within its defined scope
2. No invariant defined in `architecture.md` was violated
3. `progress-tracker.md` reflects the completed work
4. `npm run build` (frontend) and `uvicorn` (backend) pass without errors
