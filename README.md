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

### Docker Compose (recommended)

#### Prerequisites

- Docker Engine or Docker Desktop
- Docker Compose v2 (`docker compose version`)

The stack includes PostgreSQL, a one-time database schema setup service, the
FastAPI backend, and the compiled Vite frontend.

#### 1) Configure the environment

```bash
cp .env.example .env
```

Edit `.env` before using the stack:

- Set `LLM_GATEWAY_API_KEY` to enable real agent responses.
- Replace `POSTGRES_PASSWORD` and `JWT_SECRET` for any shared or long-lived
  environment.
- Keep `VITE_API_URL=http://localhost:5000` and
  `VITE_WS_URL=ws://localhost:5000` when opening the frontend on the same
  machine.

#### 2) Build and start the stack

```bash
docker compose up --build -d
docker compose ps
```

Expected services:

- `db`: running and healthy
- `db-setup`: exited successfully with status `0`
- `backend`: running and healthy
- `frontend`: running

If startup fails, inspect the setup and application logs:

```bash
docker compose logs db-setup
docker compose logs backend
docker compose logs frontend
```

#### 3) Create the sample application user

Database initialization creates the schema but does not create an application
login. Create the sample user defined in `scripts/create_user.py`:

```bash
docker compose exec backend python scripts/create_user.py
```

Sign in with:

- Username: `jdoe`
- Password: `User@123`

These are application credentials, not the PostgreSQL credentials from `.env`.
Edit `scripts/create_user.py` before running the command if you want different
initial credentials. The script creates a single user and will report a unique
constraint error if that username or email already exists.

#### 4) Open and verify the application

- Frontend: `http://localhost:5173`
- Backend liveness: `http://localhost:5000/v1/live`
- PostgreSQL: host port `5432` by default

The liveness endpoint should return:

```json
{"ok": true}
```

#### Common operations

```bash
docker compose ps
docker compose logs -f frontend
docker compose logs -f backend
docker compose restart backend frontend
docker compose down
```

After changing dependencies, Dockerfiles, or frontend build-time environment
variables, rebuild the affected service:

```bash
docker compose build --no-cache backend frontend
docker compose up -d --force-recreate backend frontend
```

The frontend URLs are embedded during its image build. Rebuild `frontend` after
changing `VITE_API_URL` or `VITE_WS_URL`.

Named volumes preserve PostgreSQL data, backend data, and logs across ordinary
`docker compose down` operations. To completely reset local data:

```bash
docker compose down -v
docker compose up --build -d
docker compose exec backend python scripts/create_user.py
```

Warning: `docker compose down -v` permanently deletes local database and
backend runtime data.

The first build is relatively large because the backend includes local ML and
Chroma dependencies. Later starts reuse built images and named volumes. Set
`POSTGRES_PORT`, `BACKEND_PORT`, or `FRONTEND_PORT` in `.env` if a default host
port is occupied. If `BACKEND_PORT` changes, update `VITE_API_URL` and
`VITE_WS_URL`, then rebuild the frontend image.

### Manual setup

#### 1) Backend setup

From `backend/`:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt -r api/requirements.txt
```

#### 2) Frontend setup

From `frontend/`:

```bash
npm install
```

#### 3) Run both apps

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
