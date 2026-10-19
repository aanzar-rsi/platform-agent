# EVA Agent API — Reference & How to Use

This document describes the FastAPI application in `backend/api`.  
Run backend tests from `backend/tests` and cross-app tests from root `tests/`.

---

## Layout

```text
v2/
  backend/
    api/               # FastAPI app
    src/               # LangGraph agent runtime
    tests/             # backend-focused tests
  tests/               # cross-app tests
```

Start the server **from `backend/`** (single worker required):

```bash
# install once
.venv/bin/pip install -r requirements.txt -r api/requirements.txt

# run
.venv/bin/python main.py
```

Base URL: `http://localhost:5000`  
API prefix: `/v1`  
WebSocket: `ws://localhost:5000/v1/ws/chats/{chat_id}?token=...`

Auth: almost every route needs `Authorization: Bearer <access_token>`.  
Public only: `POST /v1/auth/login`, `GET /v1/live`.

---

## Authentication

### `POST /v1/auth/login` (public)

**Input**

```json
{
  "identifier": "ahad_anzar",
  "password": "password123"
}
```

`identifier` may be `user_name`, `email`, or `uid`.

**Output (200)**

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 43200,
  "session_id": "<opaque>",
  "user": {
    "uid": "...",
    "user_name": "ahad_anzar",
    "email": "...",
    "name": "...",
    "role": "admin",
    "created_at": "...",
    "last_login": "..."
  }
}
```

Use `access_token` on REST and as the WS `token` query param.  
`session_id` is embedded in the JWT (`sid`); logout invalidates it server-side.

**Errors:** `401` bad credentials, `422` validation.

### `POST /v1/auth/logout` (auth)

**Input:** empty body + Bearer token.

**Output:** `{ "success": true, "message": "logged out" }`

Revokes the current `session_id`. The JWT stops working even if not expired.

### `GET /v1/auth/me` (auth)

**Output:** user object (`uid`, `user_name`, `email`, `name`, `role`, …).

---

## Health

| Method | Path | Auth | Output |
|--------|------|------|--------|
| GET | `/v1/live` | no | `{ "ok": true }` |
| GET | `/v1/health` | yes | `{ "status", "agent_ready", "active_ws", "active_runs" }` |

---

## Chats

Chat id = LangGraph `thread_id`. Creating a chat **preloads** user profile, preferences, memory, and MCP registry into `preloaded_context` for the agent.

### `POST /v1/chats` (auth)

**Input**

```json
{ "title": "Optional title", "suite": "general" }
```

Both fields optional.

**Output (200)** — `ChatOut`:

```json
{
  "chat_id": "chat_xxxxxxxxxxxx",
  "uid": "...",
  "title": "New chat",
  "suite": "general",
  "created_at": "...",
  "updated_at": "...",
  "deleted": false,
  "rollback_checkpoint_id": null
}
```

### `GET /v1/chats` (auth)

**Output:** array of `ChatOut` for the current user (excludes soft-deleted).

### `GET /v1/chats/{chat_id}` (auth)

**Output** — `ChatDetailOut` = `ChatOut` plus:

```json
{
  "messages": [{ "role": "human|ai|...", "content": "..." }],
  "preloaded_context": {
    "user": {},
    "preferences": {},
    "memory": [],
    "mcp_servers": []
  }
}
```

`messages` are projected from the LangGraph checkpoint tip when present.

**Errors:** `404` missing/deleted, `403` other user’s chat.

### `PATCH /v1/chats/{chat_id}` (auth)

**Input:** `{ "title"?: string, "suite"?: string }`  
Empty body is a no-op success.

### `DELETE /v1/chats/{chat_id}` (auth)

Soft-delete. **Output:** `{ "success": true, "chat_id": "..." }`

---

## Checkpoints & rollback

### `GET /v1/chats/{chat_id}/checkpoints` (auth)

**Output:** list of

```json
{
  "checkpoint_id": "...",
  "timestamp": "...",
  "current_task": "...",
  "message_snippet": "...",
  "parent_checkpoint_id": "..."
}
```

### `POST /v1/chats/{chat_id}/rollback` (auth)

**Input:** `{ "checkpoint_id": "..." }`

**Output:**

```json
{
  "success": true,
  "chat_id": "...",
  "checkpoint_id": "...",
  "message": "Next run will resume from this checkpoint"
}
```

Stores a one-shot tip on the session. The **next** agent run uses that checkpoint, then clears the tip. Also fences the in-memory packet queue (new epoch) so catch-up does not replay pre-rollback tokens.

---

## Memory

Per-user entries in `data/users/memory.json`.

| Method | Path | Input | Notes |
|--------|------|-------|-------|
| GET | `/v1/memory` | — | list of `{ key, value, category, updated_at? }` |
| PUT | `/v1/memory` | `{ "entries": [ ... ] }` | replace entire set |
| POST | `/v1/memory/entries` | `{ "key", "value", "category"? }` | upsert by key |
| DELETE | `/v1/memory` | — | clear all for user |

---

## Preferences

| Method | Path | Input / Output |
|--------|------|----------------|
| GET | `/v1/preferences` | `{ theme, console_mode, agent }` |
| PUT | `/v1/preferences` | partial update; omitted fields kept |

Example PUT:

```json
{ "theme": "dark", "console_mode": "advanced", "agent": {} }
```

---

## MCP registry

Registry only (no live MCP tool execution in v1). Stored in `data/users/mcp_servers.json`.

| Method | Path | Input |
|--------|------|-------|
| GET | `/v1/mcp/servers` | — |
| POST | `/v1/mcp/servers` | `{ "name", "url", "metadata"? }` |
| PATCH | `/v1/mcp/servers/{id}` | `{ "name"?, "url"?, "connected"?, "metadata"? }` |
| DELETE | `/v1/mcp/servers/{id}` | — |

---

## Analytics

### `GET /v1/analytics/summary` (auth)

**Output:** `{ "total_events", "by_type": { ... }, "uid": ... }`

- `role=admin` → all events (`uid` is `null`)
- other roles → only that user’s events (`uid` set)

Events append to `data/analytics/events.jsonl` (`login`, `logout`, `chat_create`, `run_start`, `run_complete`, `rollback`, …).

---

## WebSocket chat session

### Connect

```
WS /v1/ws/chats/{chat_id}?token=<access_token>&after_seq=<optional int>
```

- Validates JWT + active session + chat ownership (not deleted).
- Attaches a flusher to that chat’s **packet queue**.
- If another socket was attached to the same chat, it is replaced (last wins).

**Important:** agent runs always **enqueue** packets to a per-`chat_id` queue.  
If the client disconnects (switches chats), the run continues and packets buffer.  
On reconnect, undelivered packets are flushed (catch-up), then live streaming resumes.

### Envelope (all messages)

```json
{
  "v": 1,
  "type": "<string>",
  "id": "<uuid or string>",
  "chat_id": "<chat_id>",
  "seq": 123,
  "ts": "<iso8601>",
  "payload": {},
  "epoch": 0
}
```

- `seq` is monotonic per chat (null on a few control messages like `session.ready` / `pong`).
- `epoch` bumps on rollback fence.

### Client → server

| type | payload | behavior |
|------|---------|----------|
| `run.start` | `{ "query": "...", "checkpoint_id"? }` | starts one agent turn; rejects if a run is already active |
| `run.stop` | `{}` | cooperative stop (best-effort; does not hard-kill tools) |
| `run.rollback` | `{ "checkpoint_id": "..." }` | same as REST rollback + queue fence |
| `ping` | `{}` | server replies `pong` |
| `ack` | `{ "seq": <int> }` | advances delivery cursor; trims delivered packets |

### Server → client

| type | when / payload |
|------|----------------|
| `session.ready` | on attach: `{ last_seq, run_active, backlog_count, epoch }` then catch-up packets |
| `run.started` | `{ run_id, query, checkpoint_id? }` |
| `node.started` / `node.finished` | `{ node: "agent"\|"tool"\|"subagent", ... }` |
| `llm.token` | `{ text, channel: "reasoning"\|"output" }` |
| `llm.done` | end of LLM visible stream for a finish turn |
| `tool.started` / `tool.finished` | tool name, args / result summary |
| `checkpoint.created` | `{ checkpoint_id, rollback? }` |
| `run.completed` | `{ run_id, stopped, answer?, checkpoint_id? }` |
| `run.error` | `{ run_id, message }` |
| `error` | protocol / validation errors |
| `pong` | reply to `ping` |

### Minimal client flow

1. Login → save `access_token`.
2. `POST /v1/chats` → `chat_id`.
3. Open WS with token.
4. Read `session.ready` + backlog.
5. Send `{ "type": "run.start", "payload": { "query": "Hello" } }`.
6. Handle `llm.token` / `node.*` / `run.completed`.
7. Periodically `ack` the latest `seq` to free queue memory.
8. On UI navigate away: close WS (queue keeps buffering). On return: reconnect (optionally `after_seq`).

### Example messages

**Client**

```json
{ "type": "run.start", "payload": { "query": "What time is it?" } }
```

**Server (token stream)**

```json
{
  "v": 1,
  "type": "llm.token",
  "id": "...",
  "chat_id": "chat_abc",
  "seq": 12,
  "ts": "...",
  "payload": { "text": "The ", "channel": "output" },
  "epoch": 0
}
```

---

## Data store

Current v2 implementation uses PostgreSQL repositories for users/chats/messages/preferences/memory and LangGraph checkpoint persistence.

Some historical references to file-backed `data/` collections may still appear in older notes; treat those as legacy context, not current architecture.

---

## Running tests

Run backend tests from `backend/`:

```bash
.venv/bin/python -m pytest
```

Run cross-app tests from repo root:

```bash
pytest tests/
```

The suite covers every endpoint, auth/ownership edge cases, WS catch-up, rollback, isolation between users, and logout revocation.

---

## Operational notes

- Use **`workers=1`**. Packet queues and `ChatRuntimeManager` are process-local.
- Set `JWT_SECRET` (or `jwt_secret`) in env / `.env` for non-dev use (min 32 chars recommended).
- AWS credentials must be available for Bedrock when running real agent turns.
- `run.stop` is cooperative only; in-flight tool processes may still finish.
