# Repository Structure (v2)

## Top-level map

```text
v2/
├─ backend/          # Python API + agent runtime
├─ frontend/         # React/Vite web app
├─ tests/            # cross-app contract/correctness tests
├─ documentation/    # developer-facing codebase docs
├─ requirements/     # requirements, plans, and migration notes
├─ graphify-out/     # generated project graph artifacts
├─ run_dev           # starts backend + frontend together
├─ .gitignore
└─ README.md
```

## Backend (`backend/`)

- `main.py`: backend entrypoint (`API` default, `--cli` for terminal mode)
- `api/`: FastAPI routes, services, DB integration
- `src/`: agent graph, nodes, tools, prompts, model clients
- `scripts/`: standalone operational scripts (e.g., KB import)
- `tests/`: backend-focused tests

## Frontend (`frontend/`)

- `src/`: app code (pages, components, hooks)
- `public/`: static assets
- `package.json`: frontend scripts and dependencies

## Tests (`tests/`)

- `test_backend_correctness.py`: backend behavior checks
- `test_frontend_backend_contract.py`: frontend/backend contract checks

## Developer workflow

### Start locally

```bash
./run_dev
```

### Common commands

- Backend tests: `cd backend && .venv/bin/python -m pytest`
- Frontend tests: `cd frontend && npm run test`
- Frontend lint: `cd frontend && npm run lint`
- Frontend build: `cd frontend && npm run build`

## Documentation policy

- Code architecture and usage docs live in `/documentation`.
- Requirements, implementation plans, and migration notes live in `/requirements`.
