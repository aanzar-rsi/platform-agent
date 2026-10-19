# Project Agent Guide

## Layout

- `frontend/` is the React/Vite web application.
- `backend/` is the Python API and agent runtime.
- `tests/` contains cross-application contract and correctness tests.

## Development

- Run `./run_dev` from this directory to start both applications.
- The frontend uses `npm run dev`.
- The backend must run with `backend/.venv/bin/python main.py` from `backend/`.

## Graphify

- This repository reserves `graphify-out/` for a project-wide knowledge graph.
- Prefer graph queries over broad source searches when `graphify-out/graph.json` exists.
- `backend/` maintains its own graph at `backend/graphify-out/`.
