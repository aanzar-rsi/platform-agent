# Meta-Agent v2

Meta-Agent v2 is a two-app workspace:

- `backend/`: Python agent runtime + FastAPI API
- `frontend/`: React/Vite web application
- `tests/`: cross-app contract/correctness tests

## Repository Layout

```text
v2/
├─ backend/
├─ frontend/
├─ tests/
├─ documentation/
├─ requirements/
├─ run_dev
└─ README.md
```

## Quick Start

### 1) Install dependencies

Backend (from `backend/`):

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Frontend (from `frontend/`):

```bash
npm install
```

### 2) Run first-time setup (database + test user)

From repo root:

```bash
backend/.venv/bin/python scripts/firsttime_setup.py
```

This will:

- print setup/install checklist reminders,
- create/verify PostgreSQL database and schema,
- prompt for test login credentials and create/update the user,
- print final bring-up checklist.

### 3) Run both apps

From repo root:

```bash
./run_dev
```

This starts:

- backend: `.venv/bin/python main.py`
- frontend: `npm run dev`

## Run apps independently

- Backend API: `cd backend && .venv/bin/python main.py`
- Backend CLI: `cd backend && .venv/bin/python main.py --cli`
- Frontend dev: `cd frontend && npm run dev`

## Testing

- Backend tests: `cd backend && .venv/bin/python -m pytest`
- Frontend tests: `cd frontend && npm run test`
- Root cross-app tests: `pytest tests/`

## Documentation

All developer-facing code docs live under [`documentation/`](documentation/README.md):

- Backend codebase guide
- Backend API reference
- Frontend app guide
- draw.io schematic blueprint

Planning and requirement artifacts live under [`requirements/`](requirements/README.md).

## Notes

- `graphify-out/` is reserved for generated knowledge-graph artifacts.
- Do not commit secrets from `.env` files.
