# Frontend Agent Guide

## Stack

- React 19, TypeScript, Vite, Tailwind CSS v4, and Shadcn UI.
- Routes live in `src/main.tsx`; pages live in `src/pages`; reusable UI lives in `src/components`.

## Commands

- `npm run dev` starts the Vite development server.
- `npm run lint` checks linting.
- `npm run test` runs the frontend tests.
- `npm run build` type-checks and builds the production bundle.

## Conventions

- Prefer the existing Shadcn primitives in `src/components/ui`.
- Keep pages mobile responsive and use the existing theme tokens in `src/index.css`.
- Use `useAuth` from `@/hooks/use-auth` for authentication state; do not change the Convex auth files.
- Backend calls use `VITE_API_URL`, and WebSocket calls use `VITE_WS_URL`.

## Graphify

- This directory reserves `graphify-out/` for its local knowledge graph.
- When `graphify-out/graph.json` exists, query it before broad source exploration.
