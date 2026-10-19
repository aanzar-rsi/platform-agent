"""Live terminal renderer for one agent turn.

The renderer is fed two kinds of events while a turn runs:

 * incremental LLM tokens via ``on_token(text, channel)`` -- ``output`` is the
   user-facing answer and ``reasoning`` is shown as part of the runtime trace.
 * coarse progress events via methods like ``tool_call`` / ``tool_result`` /
   ``subagent_call`` -- these are printed once above the live region.

Only the current streaming text is drawn inside a transient Rich ``Live``
region. Completed events and the final answer are printed once, preventing a
growing frame from being redrawn into the terminal's scrollback.

All glyphs are ASCII so output never breaks on legacy (cp1252) Windows
consoles -- coloring does the work that symbols would otherwise do.
"""

from __future__ import annotations

import time
from typing import Any

from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from src.cli.theme import THEME

def _short(value: Any, max_len: int = 60) -> str:
    text = str(value).replace("\n", " ")
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def _format_args(args: Any) -> str:
    if not args:
        return ""
    if isinstance(args, dict):
        parts = [f"{k}={_short(v)}" for k, v in args.items()]
        return "(" + ", ".join(parts) + ")"
    return f"({_short(args)})"


class TurnRenderer:
    """Draws activity + streamed output for a single agent turn."""

    def __init__(
        self,
        console: Console | None = None,
        *,
        verbose: bool = True,
        live: bool = True,
        model_id: str = "unknown",
    ):
        self.console = console if console is not None else Console()
        self.verbose = verbose
        self.live_enabled = live
        self._live = None
        self._activity: list[Text] = []
        self._output_text = ""
        self._reasoning_text = ""
        self._status = ""
        self._busy = False
        self._final_printed = False
        self._model_id = model_id
        self._message_started_at = time.monotonic()
        self._usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self._usage_estimated = False
        self._llm_elapsed_ms = 0
        self._pending_tool: dict[str, Any] | None = None

    # ---- readable state (also the test surface) ---------------------------
    @property
    def lines(self) -> list[str]:
        """Plain text of the activity rows shown so far."""
        return [str(line) for line in self._activity]

    @property
    def output_text(self) -> str:
        return self._output_text

    @property
    def reasoning_text(self) -> str:
        return self._reasoning_text

    # ---- lifecycle --------------------------------------------------------
    def start(self, status: str = "Thinking...") -> None:
        self._busy = True
        self._status = status
        self._message_started_at = time.monotonic()
        self._open_live()

    def resume(self, status: str = "Thinking...") -> None:
        """Restart the live region after an interrupt prompt."""
        self.stop()
        self._busy = True
        self._status = status
        self._open_live()

    def pause(self) -> None:
        """Stop the live region (frame stays on screen) before an interrupt."""
        self._busy = False
        self._refresh()
        self.stop()

    def finish(self) -> None:
        """Close the live region and print the final answer exactly once."""
        self._busy = False
        self._status = ""
        self._clear_live()
        self.stop()
        if self._output_text and not self._final_printed:
            self.console.print(Markdown(self._output_text))
            self._final_printed = True
        self._message_boundary()

    def _open_live(self) -> None:
        if not self.live_enabled:
            return
        from rich.live import Live

        self._live = Live(
            self._renderable(),
            console=self.console,
            vertical_overflow="ellipsis",
            transient=True,
            auto_refresh=False,
        )
        self._live.start()

    def _clear_live(self) -> None:
        if self._live is not None:
            self._live.update(Text(""), refresh=True)

    def stop(self) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None

    def _refresh(self) -> None:
        if self._live is not None:
            self._live.update(self._renderable(), refresh=True)

    # ---- events -----------------------------------------------------------
    def set_status(self, text: str) -> None:
        self._busy = True
        self._status = text
        self._refresh()

    def on_token(self, text: str, channel: str) -> None:
        if channel == "output":
            self._output_text += text
            self._refresh()
        elif channel == "reasoning":
            self._reasoning_text += text
            self._refresh()

    def add_usage(self, usage: dict[str, Any]) -> None:
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            self._usage[key] += int(usage.get(key) or 0)
        self._usage_estimated = self._usage_estimated or bool(usage.get("usage_estimated"))
        self._llm_elapsed_ms += int(usage.get("latency_ms") or 0)

    def final_answer(self, text: str) -> None:
        """The complete answer for this turn (authoritative copy)."""
        if text:
            self._output_text = text
        self._busy = False
        self._refresh()

    def tool_call(self, name: str, args: Any = None, task: str = "") -> None:
        self._pending_tool = {"name": name, "args": args, "task": task}
        self._status = f"Running {name}..."
        self._refresh()

    def tool_result(
        self, name: str, *, ok: bool, error: str | None = None, result: Any = None
    ) -> None:
        marker = "OK" if ok else "FAILED"
        body = Text()
        pending = self._pending_tool or {}
        task = pending.get("task") or ""
        args = pending.get("args")
        if task:
            body.append(task + "\n", style="bold")
        body.append("Arguments: ", style=THEME["muted"])
        body.append((_format_args(args) or "(none)") + "\n", style=THEME["tool.args"])
        body.append("Result: ", style=THEME["muted"])
        if error:
            body.append(_short(error, 300), style=THEME["error"])
        elif result is not None:
            body.append(_short(result, 300), style=THEME["muted"])
        else:
            body.append("Completed", style=THEME["muted"])
        self._commit(
            Panel(
                body,
                title=f"Tool result · {name or 'tool'} · {marker}",
                border_style=THEME["tool.ok"] if ok else THEME["tool.fail"],
            ),
            f"[{marker}] {name or 'tool'}" + (f" {_short(error)}" if error else ""),
        )
        self._pending_tool = None
        self._status = "Thinking..."

    def subagent_call(self, name: str, task: str = "") -> None:
        self._commit(
            Panel(task or "Delegated task", title=f"Sub-agent · {name}", border_style=THEME["subagent"]),
            f"[sub-agent] {name}" + (f" -- {_short(task, 80)}" if task else ""),
        )
        self._status = f"Running {name}..."

    def subagent_done(self, name: str) -> None:
        self._commit(
            Panel("Completed", title=f"Sub-agent result · {name or 'subagent'}", border_style=THEME["tool.ok"]),
            f"[OK] {name or 'subagent'}",
        )
        self._status = "Thinking..."

    def subagent_progress(self, name: str, event: dict) -> None:
        message = event.get("message") or event.get("status") or event.get("step") or ""
        if not message:
            return
        if event.get("kind") == "reasoning_delta":
            self.on_token(str(message), "reasoning")
            return
        row = Text()
        row.append("  ", style=THEME["muted"])
        row.append(name, style=THEME["subagent"])
        row.append(f" {_short(message, 80)}", style=THEME["muted"])
        self._commit(row, f"{name} {_short(message, 80)}")

    def planner_decision(self, *, action: str | None, task: str, name: str, args: Any) -> None:
        """Record the planner's parsed decision after its streamed reasoning."""
        if not action:
            return
        reasoning = self._reasoning_text.strip()
        if reasoning:
            self._commit(
                Text(reasoning, style=THEME["thinking"]),
                f"[reasoning] {reasoning}",
            )

        body = Text()
        body.append("Action: ", style=THEME["muted"])
        body.append(action, style=THEME["tool.call"])
        if name:
            body.append(f"\nTarget: {name}", style=THEME["subagent"])
        if args:
            body.append(f"\nArguments: {_format_args(args)}", style=THEME["tool.args"])
        if task:
            body.append(f"\nGoal: {task}", style=THEME["muted"])
        self._reasoning_text = ""
        self._commit(
            Panel(body, title="Plan", border_style=THEME["info"]),
            f"[plan] {action}" + (f" {name}{_format_args(args)}" if name else "") + (f" -- {task}" if task else ""),
        )
        self._refresh()

    # ---- internals --------------------------------------------------------
    def _commit(self, renderable: Any, plain: str | None = None) -> None:
        self._activity.append(Text(plain if plain is not None else str(renderable)))
        self._clear_live()
        self.console.print()
        self.console.print(renderable)
        self.console.print()
        self._refresh()

    def _message_boundary(self) -> None:
        elapsed = time.monotonic() - self._message_started_at
        usage = self._usage
        estimate = "estimated " if self._usage_estimated else ""
        if usage["total_tokens"]:
            token_label = (
                f"{estimate}{usage['total_tokens']} tokens "
                f"({usage['prompt_tokens']} in / {usage['completion_tokens']} out)"
            )
        else:
            token_label = "usage unavailable"
        label = f"{self._model_id} · {token_label} · {elapsed:.1f}s"
        self._clear_live()
        self.console.print()
        self.console.print(Rule(label, style=THEME["rule"]), soft_wrap=True)
        self.console.print()
        self._message_started_at = time.monotonic()

    def _renderable(self):
        rows: list[Any] = []
        if self._reasoning_text:
            rows.append(Text(self._reasoning_text, style=THEME["thinking"]))
        if self._output_text:
            rows.append(Markdown(self._output_text))
        elif self._pending_tool:
            rows.append(Text(f"[ Running {self._pending_tool['name']}... ]", style=THEME["status"]))
        elif self._busy:
            status_label = self._status or "Working..."
            rows.append(Text(f"[ {status_label} ]", style=THEME["status"]))
        elif self._status:
            rows.append(Text(self._status, style=THEME["thinking"]))
        if not rows:
            rows.append(Text(""))
        return Group(*rows)
