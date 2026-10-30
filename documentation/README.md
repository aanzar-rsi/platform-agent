# Documentation Index

This folder contains developer-facing documentation for the v2 codebase.

## First-Time Setup

- Run `backend/.venv/bin/python scripts/firsttime_setup.py` from repo root to:
  - print/install checklist reminders,
  - create/verify Postgres database + schema,
  - prompt for and create/update a local test login user,
  - print final bring-up checklist (`./run_dev`, login URL, live health URL).

## Core Docs

- [`repo-structure.md`](repo-structure.md) — repository layout, responsibilities, and developer workflows.
- [`backend-codebase.md`](backend-codebase.md) — backend architecture and subsystem details.
- [`backend-api.md`](backend-api.md) — backend HTTP/WebSocket API reference.
- [`frontend-app.md`](frontend-app.md) — frontend architecture and conventions.
- [`layer-dependencies.md`](layer-dependencies.md) — permitted and prohibited cross-layer dependencies.
- [`component-dependency-diagram.md`](component-dependency-diagram.md) — component and dependency diagram.
- [`drawio-schematic-blueprint.md`](drawio-schematic-blueprint.md) — draw.io sheet blueprint for architecture schematics.

## Conventions

- Keep long-form codebase documentation in this folder.
- Keep planning, migration notes, and requirement artifacts in `/requirements`.
- Keep agent operating instructions in `AGENTS.md` / `agents.md` files where they are consumed.
