"""Interactive authenticated terminal UI for Platform Agent."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import checkboxlist_dialog, input_dialog, radiolist_dialog
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from api.db.postgres import fetch_all
from api.db.repositories import AgentRepository, McpRepository, PreferencesRepository, SessionRepository, UserRepository
from src.agent.agent_core import AgentCore, child_runner, default_policy
from src.agent.edges.routing import AGENT_NODE, CONTEXT_SELECTOR_NODE, OUTPUT_SECURITY_GATE_NODE, SUBAGENT_NODE, TOOL_NODE
from src.agent.subagent_stream import reset_child_callback, reset_subagent_callback, set_child_callback, set_subagent_callback
from src.agent.token_stream import reset_token_callback, set_token_callback
from src.agent.token_stream import reset_usage_callback, set_usage_callback
from src.cli.renderer import TurnRenderer
from src.cli.theme import THEME
from src.config import get_settings
from src.subagents.registry import get_subagents
from src.tools import INTERNAL_TOOLS
from src.utils.postgres_checkpointer import list_checkpoints, rewind_config, run_turn

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLI_STATE_FILE = PROJECT_ROOT / "data" / "cli_state.json"
MODELS = ("gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini")
COMMANDS = (
    "/help", "/new", "/sessions", "/model", "/mcp", "/agents", "/settings",
    "/tools", "/clear", "/checkpoints", "/rewind", "/quit",
)


class OpenSessions(Exception):
    pass


def get_agent_app():
    from src.agent.graph import agent_app
    return agent_app


def _load_state() -> dict:
    try:
        return json.loads(CLI_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_state(state: dict) -> None:
    try:
        CLI_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError:
        pass


def _latest_answer(messages: list) -> str:
    for msg in reversed(messages):
        if getattr(msg, "type", None) == "ai":
            content = msg.content
            if isinstance(content, str):
                return content
            try:
                return "".join(part.get("text", "") for part in content if isinstance(part, dict))
            except (TypeError, AttributeError):
                return str(content)
    return ""


def _short_text(value: str, max_len: int = 80) -> str:
    value = str(value).replace("\n", " ")
    return value if len(value) <= max_len else value[: max_len - 3] + "..."


def handle_step(renderer: TurnRenderer, step: dict) -> dict | None:
    node, updates = next(iter(step.items()))
    if node == "__interrupt__":
        interrupts = updates.get("__interrupt__") if isinstance(updates, dict) else updates
        intr = (interrupts or (None,))[0]
        payload = getattr(intr, "value", None) if intr is not None else None
        renderer.pause()
        return payload if isinstance(payload, dict) else {"value": payload}

    if node == "plan_dispatcher":
        event = updates.get("plan_event") or {}
        renderer.set_status(f"Phase {event.get('sequence', '?')}: {len(event.get('steps') or [])} step(s)...")
        return None
    if node == "phase_collector":
        event = updates.get("plan_event") or {}
        renderer.set_status(f"Phase {event.get('sequence', '?')} {'failed' if event.get('failed') else 'complete'}")
        return None

    if node == AGENT_NODE:
        if updates.get("plan_created"):
            plan = updates["plan_created"]
            renderer.set_status(f"Planned {plan['step_count']} step(s) in {len(plan['phases'])} phase(s)")
            return None
        next_step = updates.get("next_step") or {}
        action = next_step.get("action")
        renderer.planner_decision(
            action=action,
            task=next_step.get("task") or "",
            name=next_step.get("tool_name") or next_step.get("agent_name") or "",
            args=next_step.get("tool_args") or {},
        )
        if action == "finish":
            renderer.final_answer(_latest_answer(updates.get("messages") or []))
        elif action == "tool":
            renderer.tool_call(
                next_step.get("tool_name", ""),
                next_step.get("tool_args") or {},
                next_step.get("task", ""),
            )
        elif action == "subagent":
            renderer.subagent_call(next_step.get("agent_name", ""), next_step.get("task", ""))
        else:
            renderer.set_status("Thinking...")
    elif node == TOOL_NODE:
        hist = updates.get("execution_history") or []
        entry = hist[-1] if hist else {}
        result = entry.get("result") or {}
        ok = not (isinstance(result, dict) and result.get("success") is False)
        renderer.tool_result(entry.get("tool_name") or "", ok=ok, error=None if ok else result.get("error"), result=result)
    elif node == SUBAGENT_NODE:
        hist = updates.get("execution_history") or []
        renderer.subagent_done((hist[-1] if hist else {}).get("agent_name") or "")
    elif node == OUTPUT_SECURITY_GATE_NODE:
        renderer.set_status("Running output security checks...")
    elif node == CONTEXT_SELECTOR_NODE:
        renderer.set_status("Loading context window...")
    else:
        renderer.set_status("Thinking...")
    return None


def prompt_for_interrupt(console: Console, payload: dict) -> Any:
    kind = payload.get("kind")
    if kind == "question":
        question = payload.get("prompt") or "?"
        options = [str(o) for o in payload.get("options") or []]
        prompt_text = question
        if options:
            prompt_text += "\n" + "\n".join(f"  {index}. {label}" for index, label in enumerate(options, 1))
        console.print(Panel(prompt_text, title="The agent asks", border_style=THEME["info"]))
        answer = str(Prompt.ask("Your answer", console=console)).strip()
        answer = options[int(answer) - 1] if answer.isdigit() and 1 <= int(answer) <= len(options) else answer
        console.print(
            Panel(
                Group(Text(question, style=THEME["muted"]), Text(f"You: {answer}", style=THEME["user.prompt"])),
                title="Question answered",
                border_style=THEME["info"],
            )
        )
        return answer
    if kind == "confirm_tool":
        approved = Confirm.ask(f"Run {payload.get('tool_name', 'tool')}?", console=console)
        return {"approved": approved, "reason": "" if approved else str(Prompt.ask("Reason (optional)", default="", console=console))}
    if kind == "paused":
        return str(Prompt.ask("Instruction (Enter to resume)", default="", console=console))
    return str(Prompt.ask(str(payload.get("prompt") or payload.get("value") or "Input"), console=console))


def run_turn_interactive(
    console: Console,
    renderer: TurnRenderer,
    agent_app,
    thread_id: str,
    query: str,
    *,
    owner_id: str = "local-user",
    checkpoint_id: str | None = None,
    runtime: dict[str, Any] | None = None,
    authenticated: bool = False,
) -> None:
    from src.subagents.learner_agent.idle_watcher import set_chat_active
    from src.utils.trace import bind, emit, reset

    agent = None
    trace_token = None
    if authenticated:
        repository = AgentRepository()
        agent = AgentCore(repository.for_agent(thread_id, owner_id, (runtime or {}).get("session_id")), repository)
        execution_id = agent.run()
        runtime = {**(runtime or {}), "agent_id": agent.id.agent_id, "owner_id": owner_id,
                   "policy": agent.policy.as_dict(),
                   "policy_version": agent.policy.version}
        permitted = agent.policy.armory
        runtime["enabled_tools"] = permitted["tools"]
        runtime["enabled_subagents"] = permitted["subagents"]
        trace_token = bind(agent_id=agent.id.agent_id, execution_id=execution_id,
                           owner_id=owner_id, session_id=agent.id.latest_session_id)
        emit("run.lifecycle.start", component="cli")

    set_chat_active(thread_id, True)
    token = set_token_callback(lambda text, channel: renderer.on_token(text, channel))
    usage_token = set_usage_callback(renderer.add_usage)
    sub_token = set_subagent_callback(lambda name, event: renderer.subagent_progress(name, event))
    child_token = set_child_callback(lambda name, event: renderer.subagent_progress(name, event))
    renderer.start()
    try:
        params = {"query": query, "checkpoint_id": checkpoint_id, "resume_value": None, "is_resume": False}
        while True:
            stream = run_turn(
                agent_app, thread_id, params["query"], owner_id=owner_id,
                checkpoint_id=params["checkpoint_id"], resume_value=params["resume_value"],
                is_resume=params["is_resume"], runtime=runtime,
                **({"execution_id": agent.active_execution_id} if agent else {}),
            )
            for step in stream:
                payload = handle_step(renderer, step)
                if payload is not None:
                    answer = prompt_for_interrupt(console, payload)
                    renderer.resume()
                    params = {"query": None, "checkpoint_id": None, "resume_value": answer, "is_resume": True}
                    break
            else:
                if agent:
                    child_runner.join(agent.active_execution_id)
                    agent.finish("completed")
                    emit("run.lifecycle.end", component="cli", duration_ms=0)
                renderer.finish()
                return
    except BaseException as exc:
        if agent and agent.active_execution_id:
            child_runner.join(agent.active_execution_id, cancel=True)
            agent.finish("cancelled" if isinstance(exc, KeyboardInterrupt) else "failed",
                         error=type(exc).__name__)
            emit("run.lifecycle.cancel" if isinstance(exc, KeyboardInterrupt) else "run.lifecycle.error",
                 status="cancelled" if isinstance(exc, KeyboardInterrupt) else "error",
                 error=exc, component="cli", duration_ms=0)
        raise
    finally:
        reset_token_callback(token)
        reset_usage_callback(usage_token)
        reset_subagent_callback(sub_token)
        reset_child_callback(child_token)
        set_chat_active(thread_id, False)
        if trace_token is not None:
            reset(trace_token)


def print_banner(console: Console, subtitle: str = "New chat") -> None:
    console.print(Panel(Text("Platform Agent", justify="center", style=THEME["banner"]), subtitle=subtitle, border_style=THEME["banner"]))
    console.print(Text("Type / for commands. Left Arrow on an empty editor opens previous chats.", style=THEME["muted"]))


def print_help(console: Console) -> None:
    rows = [
        ("/new", "start a new chat"), ("/sessions", "open previous chats"),
        ("/model", "choose model"), ("/tools", "enable or disable tools"),
        ("/agents", "enable or disable sub-agents"), ("/mcp", "manage MCP connections"),
        ("/settings", "agent runtime settings"), ("/checkpoints", "list checkpoints"),
        ("/rewind <id>", "resume from checkpoint"), ("/clear", "clear screen"),
        ("/quit", "exit"),
    ]
    table = Table(show_header=False, box=None)
    for command, description in rows:
        table.add_row(command, description)
    console.print(table)


def print_checkpoints(console: Console, thread_id: str) -> None:
    rows = list_checkpoints(thread_id)
    if not rows:
        console.print("(no checkpoints yet)", style=THEME["muted"])
        return
    table = Table("checkpoint", "time", "task", "snippet", box=None)
    for row in rows:
        table.add_row(row.get("checkpoint_id", ""), str(row.get("timestamp", ""))[:19], _short_text(row.get("current_task", ""), 30), _short_text(row.get("message_snippet", ""), 50))
    console.print(table)


def parse_command(line: str) -> tuple[str, str | None] | None:
    stripped = line.strip()
    if stripped in ("quit", "exit"):
        return "quit", None
    if not stripped.startswith("/"):
        return None
    parts = stripped[1:].split(maxsplit=1)
    return parts[0].lower(), parts[1].strip() if len(parts) > 1 else None


def _login(console: Console) -> Any | None:
    users = UserRepository()
    console.print(Text("Sign in", style=THEME["assistant.title"]))
    for _ in range(3):
        identifier = Prompt.ask("Email or username", console=console)
        password = Prompt.ask("Password", password=True, console=console)
        try:
            user = users.authenticate(identifier, password)
            if not user:
                raise ValueError("Invalid credentials")
            users.touch_last_login(user["uid"])
            from api.core.security import new_session_id
            from api.db.repositories import AuthSessionRepository

            session_id = new_session_id()
            AuthSessionRepository().create(session_id, user["uid"])
            return SimpleNamespace(uid=user["uid"], session_id=session_id, raw=user)
        except Exception:
            console.print("Invalid credentials", style=THEME["error"])
    return None


def _session_prompt() -> PromptSession:
    bindings = KeyBindings()

    @bindings.add("left")
    def open_sessions(event):
        if not event.current_buffer.text:
            event.app.exit(exception=OpenSessions())
        else:
            event.current_buffer.cursor_left()

    @bindings.add("escape", "enter")
    def newline(event):
        event.current_buffer.insert_text("\n")

    return PromptSession(completer=WordCompleter(COMMANDS, sentence=True), key_bindings=bindings)


def _choose(title: str, values: list[tuple[Any, str]]) -> Any:
    if not values:
        return None
    return radiolist_dialog(title=title, text="Use arrows and Enter", values=values).run()


def _select_chat(sessions: SessionRepository, user: Any) -> str | None:
    chats = sessions.list_for_user(user.uid)
    return _choose("Previous agents", [(c["agent_id"], f"{c['title']}  {(c['updated_at'] or '')[:16]}") for c in chats])


def _show_chat(console: Console, sessions: SessionRepository, user: Any, agent_id: str) -> None:
    detail = sessions.get(agent_id)
    if not detail or detail["owner_id"] != user.uid:
        return
    console.clear()
    print_banner(console, detail["title"])
    messages = fetch_all(
        "SELECT role, content, checkpoint_id FROM messages WHERE agent_id = %s ORDER BY created_at",
        (agent_id,),
    )
    from src.utils.postgres_checkpointer import active_checkpoint_path
    active_path = active_checkpoint_path(agent_id)
    for message in messages:
        if active_path is not None and message.get("checkpoint_id") and message["checkpoint_id"] not in active_path:
            continue
        role = message.get("role", "")
        content = str(message.get("content", ""))
        if role in ("human", "user"):
            console.print(Text(f"You > {content}", style=THEME["user.prompt"]))
        elif role in ("ai", "assistant"):
            console.print(Markdown(content))


def _default_runtime(prefs: dict) -> dict[str, Any]:
    settings = get_settings()
    saved = prefs.get("agent") or {}
    return {
        "model_id": saved.get("model_id", settings.llm_model_id),
        "enabled_tools": saved.get("enabled_tools", [t.name for t in INTERNAL_TOOLS]),
        "enabled_subagents": saved.get("enabled_subagents", [s.name for s in get_subagents()]),
        "confirm_tools": saved.get("confirm_tools", True),
        "verbose": saved.get("verbose", False),
        "max_loops": int(saved.get("max_loops", settings.max_loops)),
    }


def _save_runtime(user: Any, runtime: dict[str, Any]) -> None:
    PreferencesRepository().put(user.uid, {"agent": runtime})


def _manage_mcp(console: Console, user: Any) -> None:
    repo = McpRepository()
    from api.core.deps import get_repos
    from api.domain.memory import McpCreateRequest
    from api.services.mcp_runtime import mcp_runtime
    from api.services.mcp_service import McpService

    service = McpService(get_repos())
    servers = [{**s, "connected": bool(mcp_runtime.get(user.uid, s["id"]))} for s in repo.list(user.uid)]
    action = _choose("MCP connections", [("add", "Add server")] + [(s["id"], f"{'[on]' if s['connected'] else '[off]'} {s['name']}  {s['url']}") for s in servers])
    if action == "add":
        name = input_dialog(title="MCP server", text="Name").run()
        url = input_dialog(title="MCP server", text="URL").run() if name else None
        if name and url:
            service.create(user, McpCreateRequest(name=name, url=url))
        return
    server = next((s for s in servers if s["id"] == action), None)
    if not server:
        return
    operation = _choose(server["name"], [("toggle", "Disconnect" if server["connected"] else "Connect"), ("delete", "Delete")])
    if operation == "toggle":
        if server["connected"]:
            service.disconnect(user, server["id"])
        else:
            service.connect(user, server["id"])
    elif operation == "delete":
        service.delete(user, server["id"])


def _handle_settings(runtime: dict[str, Any]) -> None:
    field = _choose("Settings", [("verbose", f"Verbose: {runtime['verbose']}"), ("confirm_tools", f"Confirm destructive tools: {runtime['confirm_tools']}"), ("max_loops", f"Max loops: {runtime['max_loops']}")])
    if field in ("verbose", "confirm_tools"):
        runtime[field] = not runtime[field]
    elif field:
        value = input_dialog(title="Settings", text=field.replace("_", " "), default=str(runtime[field])).run()
        if value and value.isdigit() and int(value) > 0:
            runtime[field] = int(value)


def run_cli() -> None:
    console = Console()
    user = _login(console)
    if not user:
        return
    from src.subagents.learner_agent.idle_watcher import BackgroundIdleWatcher

    idle_watcher = BackgroundIdleWatcher()
    idle_watcher.start()
    sessions = SessionRepository()
    preferences = PreferencesRepository()
    runtime = _default_runtime(preferences.get(user.uid))
    prompt = _session_prompt()
    agent_id: str | None = None
    checkpoint_id: str | None = None
    state = _load_state()
    print_banner(console)

    try:
        while True:
            try:
                line = (prompt.prompt("You > ") or "").strip()
            except OpenSessions:
                selected = _select_chat(sessions, user)
                if selected:
                    agent_id = selected
                    state["agent_id"] = agent_id
                    _save_state(state)
                    _show_chat(console, sessions, user, agent_id)
                continue
            except (EOFError, KeyboardInterrupt):
                break

            command = parse_command(line)
            if command:
                name, arg = command
                if name in ("quit", "exit"):
                    break
                if name == "help":
                    print_help(console)
                elif name == "clear":
                    console.clear(); print_banner(console, "Chat" if agent_id else "New chat")
                elif name == "new":
                    agent_id = checkpoint_id = None; console.clear(); print_banner(console)
                elif name == "sessions":
                    selected = _select_chat(sessions, user)
                    if selected:
                        agent_id = selected
                        state["agent_id"] = agent_id
                        _save_state(state)
                        _show_chat(console, sessions, user, agent_id)
                elif name == "model":
                    selected = _choose("Choose model", [(m, m) for m in MODELS])
                    if selected:
                        runtime["model_id"] = selected; _save_runtime(user, runtime)
                elif name == "tools":
                    selected = checkboxlist_dialog(title="Tools", text="Space toggles", values=[(t.name, t.name) for t in INTERNAL_TOOLS], default_values=runtime["enabled_tools"]).run()
                    if selected is not None:
                        runtime["enabled_tools"] = selected; _save_runtime(user, runtime)
                elif name == "agents":
                    agents = get_subagents(user.uid)
                    if not agents:
                        console.print("No sub-agents are registered.", style=THEME["muted"])
                    else:
                        selected = checkboxlist_dialog(title="Sub-agents", text="Space toggles", values=[(a.name, a.display_name) for a in agents], default_values=runtime["enabled_subagents"]).run()
                        if selected is not None:
                            runtime["enabled_subagents"] = selected; _save_runtime(user, runtime)
                elif name == "mcp":
                    _manage_mcp(console, user)
                elif name == "settings":
                    _handle_settings(runtime); _save_runtime(user, runtime)
                elif name == "checkpoints" and agent_id:
                    print_checkpoints(console, agent_id)
                elif name == "rewind" and agent_id and arg:
                    checkpoint_id = arg; rewind_config(agent_id, arg, owner_id=user.uid)
                else:
                    console.print(f"Unknown or unavailable command: /{name}", style=THEME["warning"])
                continue

            if not line:
                continue
            if agent_id is None:
                agent = sessions.create(owner_id=user.uid, session_id=user.session_id,
                                        title=_short_text(line, 60))
                agent_id = agent["agent_id"]
                state["agent_id"] = agent_id
                _save_state(state)
            renderer = TurnRenderer(
                console,
                verbose=runtime["verbose"],
                model_id=runtime["model_id"],
            )
            run_turn_interactive(console, renderer, get_agent_app(), agent_id, line, owner_id=user.uid,
                                 checkpoint_id=checkpoint_id, runtime={**runtime, "session_id": user.session_id}, authenticated=True)
            checkpoint_id = None
            sessions.update(agent_id, last_activity_at=datetime.now(timezone.utc).isoformat())
            console.print()
    finally:
        idle_watcher.stop()


if __name__ == "__main__":
    run_cli()
