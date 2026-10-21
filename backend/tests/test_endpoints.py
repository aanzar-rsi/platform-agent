"""Comprehensive endpoint + edge-case tests for the EVA FastAPI API."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from api.app import create_app
from api.services.chat_runtime_manager import get_runtime_manager
from api.core.deps import get_repos

PASS = 0
FAIL = 0
ERRORS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        msg = f"  FAIL  {name}" + (f" -- {detail}" if detail else "")
        print(msg)
        ERRORS.append(msg)


def ws_rejected(client: TestClient, url: str) -> bool:
    """Return True if the socket is rejected/closed without a session.ready."""
    try:
        with client.websocket_connect(url) as ws:
            msg = ws.receive_json()
            # If we somehow get a message, rejection failed
            return msg.get("type") != "session.ready"
    except (WebSocketDisconnect, Exception):
        return True


def main() -> int:
    app = create_app()
    with TestClient(app) as c:
        print("\n=== AUTH ===")
        r = c.post("/v1/auth/login", json={"identifier": "nope", "password": "x"})
        check("login invalid credentials -> 401", r.status_code == 401, str(r.status_code))

        r = c.post("/v1/auth/login", json={"password": "x"})
        check("login missing identifier -> 422", r.status_code == 422, str(r.status_code))

        r = c.post("/v1/auth/login", json={"identifier": "ahad_anzar", "password": ""})
        check("login empty password -> 401", r.status_code == 401, str(r.status_code))

        r = c.post(
            "/v1/auth/login",
            json={"identifier": "ahad_anzar", "password": "password123"},
        )
        check("login user_name -> 200", r.status_code == 200, r.text)
        body = r.json() if r.status_code == 200 else {}
        check("login returns access_token", bool(body.get("access_token")))
        check("login returns session_id", bool(body.get("session_id")))
        check("login returns user.uid", bool(body.get("user", {}).get("uid")))
        token = body.get("access_token", "")
        uid = body.get("user", {}).get("uid", "")
        h = {"Authorization": f"Bearer {token}"}

        r = c.post(
            "/v1/auth/login",
            json={"identifier": "ahad.anzar@chryselys.com", "password": "password123"},
        )
        check("login email -> 200", r.status_code == 200, r.text)
        token2 = r.json().get("access_token", "") if r.status_code == 200 else ""
        h2 = {"Authorization": f"Bearer {token2}"}

        r = c.post(
            "/v1/auth/login",
            json={"identifier": uid, "password": "password123"},
        )
        check("login by uid -> 200", r.status_code == 200, r.text)

        r = c.get("/v1/auth/me", headers=h)
        check("me -> 200", r.status_code == 200, r.text)
        check("me uid matches", r.json().get("uid") == uid if r.status_code == 200 else False)

        r = c.get("/v1/auth/me")
        check("me without token -> 401", r.status_code == 401, str(r.status_code))

        r = c.get("/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
        check("me bad token -> 401", r.status_code == 401, str(r.status_code))

        print("\n=== HEALTH ===")
        r = c.get("/v1/live")
        check("live public -> 200", r.status_code == 200 and r.json().get("ok") is True, r.text)

        r = c.get("/v1/health")
        check("health without auth -> 401", r.status_code == 401, str(r.status_code))

        r = c.get("/v1/health", headers=h)
        check("health -> 200", r.status_code == 200, r.text)
        if r.status_code == 200:
            check("health has agent_ready", "agent_ready" in r.json())

        print("\n=== CHATS ===")
        r = c.get("/v1/agents")
        check("list chats no auth -> 401", r.status_code == 401)

        r = c.post("/v1/agents", json={"title": "Edge Chat A"}, headers=h)
        check("create chat -> 200", r.status_code == 200, r.text)
        chat_a = r.json() if r.status_code == 200 else {}
        chat_a_id = chat_a.get("agent_id", "")

        r = c.post("/v1/agents", json={}, headers=h)
        check("create chat defaults -> 200", r.status_code == 200, r.text)
        chat_b_id = r.json().get("agent_id", "") if r.status_code == 200 else ""

        r = c.get("/v1/agents", headers=h)
        check("list chats -> 200", r.status_code == 200, r.text)
        ids = [x["agent_id"] for x in r.json()] if r.status_code == 200 else []
        check("list contains created chats", chat_a_id in ids and chat_b_id in ids, str(ids[:5]))

        r = c.get(f"/v1/agents/{chat_a_id}", headers=h)
        check("get chat -> 200", r.status_code == 200, r.text)
        if r.status_code == 200:
            d = r.json()
            check("get has messages list", isinstance(d.get("messages"), list))
            check("get has preloaded_context", isinstance(d.get("preloaded_context"), dict))
            check(
                "preload has user",
                bool(d.get("preloaded_context", {}).get("user")),
                str(list(d.get("preloaded_context", {}).keys())),
            )

        r = c.get("/v1/agents/chat_does_not_exist", headers=h)
        check("get missing chat -> 404", r.status_code == 404, str(r.status_code))

        r = c.patch(f"/v1/agents/{chat_a_id}", json={"title": "Renamed"}, headers=h)
        check("patch chat -> 200", r.status_code == 200, r.text)
        check(
            "patch title applied",
            r.json().get("title") == "Renamed" if r.status_code == 200 else False,
        )

        r = c.patch(f"/v1/agents/{chat_a_id}", json={}, headers=h)
        check("patch empty body -> 200", r.status_code == 200, r.text)

        r = c.patch("/v1/agents/chat_does_not_exist", json={"title": "x"}, headers=h)
        check("patch missing -> 404", r.status_code == 404)

        r = c.post(
            "/v1/auth/login",
            json={"identifier": "jane_doe", "password": "password123"},
        )
        check("login jane -> 200", r.status_code == 200, r.text)
        jane_token = r.json()["access_token"] if r.status_code == 200 else ""
        jane_h = {"Authorization": f"Bearer {jane_token}"}
        jane_uid = r.json()["user"]["uid"] if r.status_code == 200 else ""

        r = c.get(f"/v1/agents/{chat_a_id}", headers=jane_h)
        check("other user get chat -> 403", r.status_code == 403, str(r.status_code))

        r = c.patch(f"/v1/agents/{chat_a_id}", json={"title": "hack"}, headers=jane_h)
        check("other user patch chat -> 403", r.status_code == 403, str(r.status_code))

        r = c.delete(f"/v1/agents/{chat_a_id}", headers=jane_h)
        check("other user delete chat -> 403", r.status_code == 403, str(r.status_code))

        r = c.delete(f"/v1/agents/{chat_b_id}", headers=h)
        check("delete chat -> 200", r.status_code == 200, r.text)
        r = c.get(f"/v1/agents/{chat_b_id}", headers=h)
        check("get deleted chat -> 404", r.status_code == 404)
        r = c.patch(f"/v1/agents/{chat_b_id}", json={"title": "x"}, headers=h)
        check("patch deleted chat -> 404", r.status_code == 404)
        r = c.delete(f"/v1/agents/{chat_b_id}", headers=h)
        check("delete already deleted -> 404", r.status_code == 404)
        r = c.get("/v1/agents", headers=h)
        listed = [x["agent_id"] for x in r.json()] if r.status_code == 200 else []
        check("deleted not in list", chat_b_id not in listed)

        # jane's chats isolated
        r = c.post("/v1/agents", json={"title": "Jane chat"}, headers=jane_h)
        check("jane create chat -> 200", r.status_code == 200, r.text)
        jane_chat = r.json().get("agent_id") if r.status_code == 200 else ""
        r = c.get("/v1/agents", headers=jane_h)
        jane_ids = [x["agent_id"] for x in r.json()] if r.status_code == 200 else []
        check("jane list excludes ahad chat", chat_a_id not in jane_ids)
        check("jane list includes own chat", jane_chat in jane_ids)

        print("\n=== CHECKPOINTS ===")
        r = c.get(f"/v1/agents/{chat_a_id}/checkpoints", headers=h)
        check("list checkpoints -> 200", r.status_code == 200, r.text)
        check("checkpoints is list", isinstance(r.json(), list) if r.status_code == 200 else False)

        r = c.get("/v1/agents/chat_missing/checkpoints", headers=h)
        check("checkpoints missing chat -> 404", r.status_code == 404)

        r = c.get(f"/v1/agents/{chat_a_id}/checkpoints", headers=jane_h)
        check("checkpoints other user -> 403", r.status_code == 403)

        r = c.get(f"/v1/agents/{chat_b_id}/checkpoints", headers=h)
        check("checkpoints deleted chat -> 404", r.status_code == 404)

        r = c.post(
            f"/v1/agents/{chat_a_id}/rollback",
            json={"checkpoint_id": "cp_test_edge"},
            headers=h,
        )
        check("rollback foreign checkpoint -> 400", r.status_code == 400, r.text)
        r = c.get(f"/v1/agents/{chat_a_id}", headers=h)
        check(
            "rollback tip stored",
            r.json().get("rollback_checkpoint_id") is None
            if r.status_code == 200
            else False,
            str(r.json().get("rollback_checkpoint_id") if r.status_code == 200 else r.text),
        )

        r = c.post(f"/v1/agents/{chat_a_id}/rollback", json={}, headers=h)
        check("rollback missing checkpoint_id -> 422", r.status_code == 422)

        r = c.post(
            f"/v1/agents/{chat_b_id}/rollback",
            json={"checkpoint_id": "x"},
            headers=h,
        )
        check("rollback deleted chat -> 404", r.status_code == 404)

        print("\n=== MEMORY ===")
        r = c.get("/v1/memory", headers=h)
        check("get memory -> 200", r.status_code == 200, r.text)

        r = c.post(
            "/v1/memory/entries",
            json={"key": "city", "value": "Bangalore", "category": "user_data"},
            headers=h,
        )
        check("add memory entry -> 200", r.status_code == 200, r.text)
        check("add returns key", r.json().get("key") == "city" if r.status_code == 200 else False)

        r = c.post(
            "/v1/memory/entries",
            json={"key": "city", "value": "Bengaluru", "category": "user_data"},
            headers=h,
        )
        check("upsert memory -> 200", r.status_code == 200)
        r = c.get("/v1/memory", headers=h)
        entries = r.json() if r.status_code == 200 else []
        cities = [e for e in entries if e.get("key") == "city"]
        check("upsert replaces not duplicates", len(cities) == 1, str(cities))
        check("upsert value updated", cities[0].get("value") == "Bengaluru" if cities else False)

        # isolation
        r = c.post(
            "/v1/memory/entries",
            json={"key": "secret", "value": "jane-only"},
            headers=jane_h,
        )
        check("jane add memory -> 200", r.status_code == 200)
        r = c.get("/v1/memory", headers=h)
        ahad_keys = {e["key"] for e in (r.json() if r.status_code == 200 else [])}
        check("ahad cannot see jane memory key", "secret" not in ahad_keys, str(ahad_keys))

        r = c.put(
            "/v1/memory",
            json={
                "entries": [
                    {"key": "name", "value": "Ahad", "category": "user_data"},
                    {"key": "role", "value": "admin", "category": "user_data"},
                ]
            },
            headers=h,
        )
        check("put memory -> 200", r.status_code == 200, r.text)
        check("put replaces all", len(r.json()) == 2 if r.status_code == 200 else False)

        r = c.delete("/v1/memory", headers=h)
        check("clear memory -> 200", r.status_code == 200)
        r = c.get("/v1/memory", headers=h)
        check("memory empty after clear", r.json() == [] if r.status_code == 200 else False)

        r = c.get("/v1/memory", headers=jane_h)
        check(
            "jane memory survives ahad clear",
            any(e.get("key") == "secret" for e in (r.json() if r.status_code == 200 else [])),
            str(r.json()),
        )

        r = c.post("/v1/memory/entries", json={"key": "x"}, headers=h)
        check("add memory missing value -> 422", r.status_code == 422)

        print("\n=== PREFERENCES ===")
        r = c.get("/v1/preferences", headers=h)
        check("get prefs -> 200", r.status_code == 200, r.text)

        r = c.put(
            "/v1/preferences",
            json={"theme": "dark", "console_mode": "advanced"},
            headers=h,
        )
        check("put prefs -> 200", r.status_code == 200, r.text)
        check("prefs theme", r.json().get("theme") == "dark" if r.status_code == 200 else False)

        r = c.get("/v1/preferences", headers=h)
        check(
            "prefs persisted",
            r.json().get("console_mode") == "advanced" if r.status_code == 200 else False,
        )

        r = c.put("/v1/preferences", json={"theme": "light"}, headers=h)
        check(
            "partial prefs merge keeps console_mode",
            r.json().get("console_mode") == "advanced" if r.status_code == 200 else False,
            str(r.json()),
        )

        r = c.put("/v1/preferences", json={"theme": "jane-theme"}, headers=jane_h)
        check("jane prefs -> 200", r.status_code == 200)
        r = c.get("/v1/preferences", headers=h)
        check(
            "ahad prefs isolated from jane",
            r.json().get("theme") != "jane-theme" if r.status_code == 200 else False,
            str(r.json()),
        )

        print("\n=== MCP ===")
        r = c.get("/v1/armory/mcp", headers=h)
        check("list mcp -> 200", r.status_code == 200, r.text)

        r = c.post(
            "/v1/armory/mcp",
            json={"name": "local", "url": "http://127.0.0.1:9999", "metadata": {"a": 1}},
            headers=h,
        )
        check("create mcp -> 200", r.status_code == 200, r.text)
        mcp_id = r.json().get("id") if r.status_code == 200 else None

        r = c.patch(
            f"/v1/armory/mcp/{mcp_id}",
            json={"connected": True, "name": "local-renamed"},
            headers=h,
        )
        check("patch mcp -> 200", r.status_code == 200, r.text)
        check(
            "mcp connected",
            r.json().get("connected") is True if r.status_code == 200 else False,
        )

        r = c.patch(f"/v1/armory/mcp/{mcp_id}", json={"connected": False}, headers=jane_h)
        # jane's repo is separate - update returns 404 for unknown id in jane's list
        check("jane cannot patch ahad mcp -> 404", r.status_code == 404, str(r.status_code))

        r = c.patch("/v1/armory/mcp/mcp_missing", json={"connected": True}, headers=h)
        check("patch missing mcp -> 404", r.status_code == 404)

        r = c.delete(f"/v1/armory/mcp/{mcp_id}", headers=h)
        check("delete mcp -> 200", r.status_code == 200)
        r = c.delete("/v1/armory/mcp/mcp_missing", headers=h)
        check("delete missing mcp -> 404", r.status_code == 404)

        r = c.post("/v1/armory/mcp", json={"name": "x"}, headers=h)
        check("create mcp missing url -> 422", r.status_code == 422)

        print("\n=== ANALYTICS ===")
        r = c.get("/v1/analytics", headers=h)
        check("analytics admin -> 200", r.status_code == 200, r.text)
        if r.status_code == 200:
            check("analytics has by_type", isinstance(r.json().get("by_type"), dict))
            check("admin analytics unscoped uid", r.json().get("uid") is None, str(r.json()))

        r = c.get("/v1/analytics", headers=jane_h)
        check("analytics user -> 200", r.status_code == 200, r.text)
        if r.status_code == 200:
            check("analytics user scoped", r.json().get("uid") == jane_uid, str(r.json()))

        print("\n=== WEBSOCKET ===")
        check("ws no token rejected", ws_rejected(c, f"/v1/ws/agents/{chat_a_id}"))
        check("ws bad token rejected", ws_rejected(c, f"/v1/ws/agents/{chat_a_id}?token=bad"))
        check(
            "ws missing chat rejected",
            ws_rejected(c, f"/v1/ws/agents/agent_missing?token={token}"),
        )
        check(
            "ws other user rejected",
            ws_rejected(c, f"/v1/ws/agents/{chat_a_id}?token={jane_token}"),
        )
        check(
            "ws deleted chat rejected",
            ws_rejected(c, f"/v1/ws/agents/{chat_b_id}?token={token}"),
        )

        mgr = get_runtime_manager()
        repos = get_repos()
        ex = repos.agents.start_execution(chat_a_id)
        execution_id = str(ex["execution_id"])
        repos.execution_events.append(
            agent_id=chat_a_id,
            execution_id=execution_id,
            event_type="run.started",
            payload={"execution_id": execution_id},
        )
        repos.execution_events.append(
            agent_id=chat_a_id,
            execution_id=execution_id,
            event_type="llm.token",
            payload={"text": "hi", "channel": "output"},
        )

        with c.websocket_connect(f"/v1/ws/agents/{chat_a_id}?token={token}") as ws:
            ready = ws.receive_json()
            check("ws session.ready", ready.get("type") == "session.ready", str(ready))
            backlog = ready.get("payload", {}).get("backlog_count", 0)
            check("ws backlog >= 2", backlog >= 2, str(ready.get("payload")))
            msgs = [ws.receive_json() for _ in range(backlog)]
            types = [m["type"] for m in msgs]
            check(
                "ws catchup types",
                "run.started" in types and "llm.token" in types,
                str(types),
            )

            ws.send_json({"type": "ping", "payload": {}})
            pong = ws.receive_json()
            check("ws ping->pong", pong.get("type") == "pong", str(pong))

            ws.send_json({"type": "run.start", "payload": {"query": "   "}})
            err = ws.receive_json()
            check("ws whitespace query -> error", err.get("type") == "error", str(err))

            ws.send_json({"type": "run.start", "payload": {}})
            err = ws.receive_json()
            check("ws run.start empty query -> error", err.get("type") == "error", str(err))

            ws.send_json(
                {"type": "run.rollback", "payload": {"checkpoint_id": "cp_ws_roll"}}
            )
            rolled = ws.receive_json()
            check(
                "ws rollback invalid -> error",
                rolled.get("type") == "error",
                str(rolled),
            )

            ws.send_json({"type": "run.rollback", "payload": {}})
            miss = ws.receive_json()
            check(
                "ws rollback missing id -> error",
                miss.get("type") == "error",
                str(miss),
            )

            ws.send_json({"type": "nope", "payload": {}})
            unk = ws.receive_json()
            check("ws unknown type -> error", unk.get("type") == "error", str(unk))

            ws.send_json({"type": "run.stop", "payload": {}})
            stop_msg = ws.receive_json()
            check(
                "ws stop with no run -> error",
                stop_msg.get("type") == "error",
                str(stop_msg),
            )

            # double run: force active flag
            rt = mgr.get_or_create(chat_a_id, uid)
            rt.run_active = True
            ws.send_json(
                {"type": "run.start", "payload": {"query": "should fail busy"}}
            )
            busy = ws.receive_json()
            check(
                "ws second run while active -> error",
                busy.get("type") == "error"
                and "already active" in str(busy.get("payload", {})).lower(),
                str(busy),
            )
            rt.run_active = False

        with c.websocket_connect(
            f"/v1/ws/agents/{chat_a_id}?token={token}&execution_id={execution_id}&after_seq=0"
        ) as ws:
            ready = ws.receive_json()
            check("ws reconnect session.ready", ready.get("type") == "session.ready")

        print("\n=== LOGOUT / REVOCATION ===")
        r = c.post("/v1/auth/logout", headers=h)
        check("logout -> 200", r.status_code == 200, r.text)
        r = c.get("/v1/auth/me", headers=h)
        check("me after logout -> 401", r.status_code == 401)
        r = c.get("/v1/agents", headers=h)
        check("chats after logout -> 401", r.status_code == 401)

        check(
            "ws revoked token rejected",
            ws_rejected(c, f"/v1/ws/agents/{chat_a_id}?token={token}"),
        )

        r = c.get("/v1/auth/me", headers=h2)
        check(
            "other session still valid after first logout",
            r.status_code == 200,
            str(r.status_code),
        )

        r = c.post("/v1/auth/logout")
        check("logout no auth -> 401", r.status_code == 401)

        r = c.post(
            "/v1/auth/login",
            json={"identifier": "ahad_anzar", "password": "wrong"},
        )
        check("wrong password -> 401", r.status_code == 401)

        # preload reflects memory at create time
        r = c.post(
            "/v1/auth/login",
            json={"identifier": "ahad_anzar", "password": "password123"},
        )
        h3 = {"Authorization": f"Bearer {r.json()['access_token']}"}
        c.post(
            "/v1/memory/entries",
            json={"key": "fav", "value": "tea"},
            headers=h3,
        )
        r = c.post("/v1/agents", json={"title": "preload check"}, headers=h3)
        check("create after memory -> 200", r.status_code == 200)
        cid = r.json()["agent_id"]
        r = c.get(f"/v1/agents/{cid}", headers=h3)
        mem = r.json().get("preloaded_context", {}).get("memory", [])
        check(
            "new chat preloads memory",
            any(e.get("key") == "fav" for e in mem),
            str(mem),
        )

    print(f"\n=== RESULT: {PASS} passed, {FAIL} failed ===")
    if ERRORS:
        print("\nFailures:")
        for e in ERRORS:
            print(e)
    return 1 if FAIL else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise SystemExit(2)
