import sys
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pydantic import ValidationError
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from src.agent.control import (
    clear_pause,
    note_text_from_resume,
    pause_gate_active,
    thread_id_from_config,
)
from src.agent.policy_schema import armory_resource_allowed
from src.agent.memory import count_content_tokens, record_execution, record_human_input
from src.agent.state import PlanExecuteState
from src.tools import INTERNAL_TOOLS
from api.services.mcp_runtime import available_mcp_tools, call_mcp_tool
from src.utils.text_truncate import truncate_for_aimessage


_TOOL_MAP = {t.name: t for t in INTERNAL_TOOLS}

# Tools whose effects are destructive/hard-to-reverse or execute arbitrary code —
# require an explicit human approval interrupt before running.
CONFIRM_REQUIRED_TOOLS = frozenset(
    {"execute_bash", "execute_powershell", "execute_python_script", "edit_file"}
)


def tool_node(state: PlanExecuteState, config: RunnableConfig | None = None) -> dict:
    from src.utils.trace import in_run, emit as trace_emit

    traced = in_run()
    next_step         = state["next_step"]
    execution_history = list(state.get("execution_history", []))
    execution_memory  = dict(state.get("execution_memory", {}))
    context_memory    = state.get("context_memory")

    tool_name = next_step.get("tool_name", "")
    raw_args  = next_step.get("tool_args", {})
    task = state.get("current_task") or next_step.get("task") or ""

    # ── Pause + confirmation gate ────────────────────────────────────────────
    # Combined into a single interrupt() call site (never two independently
    # conditioned calls in the same node — see src/agent/control.py docstring).
    thread_id = thread_id_from_config(config)
    pause_requested = pause_gate_active(
        thread_id,
        "tool_node",
        kinds=frozenset({"paused", "confirm_tool"}),
    )
    configurable = (config or {}).get("configurable") or {}
    enabled_tools = configurable.get("enabled_tools")
    armory = (configurable.get("policy") or {}).get("armory") or {}
    mcp_tools = available_mcp_tools(configurable.get("owner_id"))
    tool_disabled = ((enabled_tools is not None and tool_name not in enabled_tools)
                     or ("policy" in configurable
                         and not armory_resource_allowed(armory, group="tools", name=tool_name)))
    if tool_disabled:
        result = {"success": False, "error": f"Tool '{tool_name}' is disabled for this session."}
        if traced:
            trace_emit("armory.authz.deny", status="denied", error=PermissionError("tool_disabled"),
                       data={"tool_name": tool_name}, component="tool_node")
        return _record_tool_result(tool_name=tool_name, raw_args=raw_args, task=task, result=result,
                                   execution_history=execution_history, execution_memory=execution_memory,
                                   context_memory=context_memory)
    if traced:
        trace_emit("armory.authz.allow", status="ok",
                   data={"tool_name": tool_name}, component="tool_node")
        trace_emit("guardrail.resource.check", data={"tool_name": tool_name}, component="tool_node")
    if not tool_name or not isinstance(raw_args, dict):
        if traced:
            trace_emit("guardrail.decision.deny", status="denied", error=ValueError("invalid_resource_call"),
                       data={"guardrail_type": "resource", "decision": "deny", "reason_code": "invalid_arguments"},
                       component="tool_node")
        return _record_tool_result(tool_name=tool_name, raw_args=raw_args, task=task,
                                   result={"success": False, "error": "Invalid tool arguments"},
                                   execution_history=execution_history, execution_memory=execution_memory,
                                   context_memory=context_memory)
    if traced and not (pause_requested or tool_name in CONFIRM_REQUIRED_TOOLS):
        trace_emit("guardrail.decision.allow", data={"guardrail_type": "resource", "decision": "allow"},
                   component="tool_node")
    needs_confirm = (
        (configurable.get("confirm_tools", True) or armory.get("confirm_tools", True)
         or (configurable.get("policy") or {}).get("guardrails", {}).get("confirm_tools", True))
        and tool_name in CONFIRM_REQUIRED_TOOLS
    )

    decline_reason: str | None = None
    if pause_requested or needs_confirm:
        if traced and needs_confirm:
            trace_emit("guardrail.decision.approval_required", data={"guardrail_type": "resource",
                     "decision": "approval_required"}, component="tool_node")
        from langgraph.types import interrupt

        decision = interrupt(
            {
                "kind": "paused" if pause_requested and not needs_confirm else "confirm_tool",
                "node": "tool_node",
                "tool_name": tool_name,
                "tool_args": raw_args,
                "task": task,
                "paused": pause_requested,
                "confirm_required": needs_confirm,
            }
        )
        if pause_requested:
            clear_pause(thread_id)

        approved = True
        if isinstance(decision, dict):
            if needs_confirm:
                approved = bool(decision.get("approved", False))
            decline_reason = decision.get("reason")
            injected_note = decision.get("note") or decision.get("text") or decision.get("answer")
        else:
            injected_note = note_text_from_resume(decision)

        note = (injected_note or "").strip() if isinstance(injected_note, str) else ""
        if note:
            execution_history, execution_memory, context_memory = record_human_input(
                execution_history, execution_memory, context_memory, value=note,
                description="User response at tool approval or pause gate", task=task,
            )

        if pause_requested and not needs_confirm:
            # A plain pause (no confirmation needed): skip this tool call
            # entirely and let agent_node re-plan, optionally with a new
            # instruction the user typed while paused.
            if note:
                return {
                    "messages": [
                        HumanMessage(
                            content=note,
                            additional_kwargs={
                                "ui_hidden": True,
                                "ui_step": {"type": "reasoning", "content": f"User response: {note}"},
                            },
                        )
                    ],
                    "execution_history": execution_history,
                    "execution_memory": execution_memory,
                    "context_memory": context_memory,
                }
            return {}

        if needs_confirm and not approved:
            if traced:
                trace_emit("guardrail.decision.deny", status="denied", error=PermissionError("declined"),
                           data={"guardrail_type": "resource", "decision": "deny", "reason_code": "user_declined"},
                           component="tool_node")
            result = {
                "success": False,
                "error": "User declined to run this action.",
                "user_reason": decline_reason or "",
            }
            return _record_tool_result(
                tool_name=tool_name,
                raw_args=raw_args,
                task=task,
                result=result,
                execution_history=execution_history,
                execution_memory=execution_memory,
                context_memory=context_memory,
            )

        if traced:
            trace_emit("guardrail.decision.allow", data={"guardrail_type": "resource", "decision": "allow"},
                       component="tool_node")

    try:
        from src.utils.agent_logger import log_tool

        log_tool("start", tool_name=tool_name, tool_args=raw_args, task=task)
    except Exception:
        pass

    if traced:
        trace_emit("tool.call.start", data={"tool_name": tool_name,
                                             "arg_keys": sorted(raw_args) if isinstance(raw_args, dict) else []},
                   component="tool_node")

    tool = _TOOL_MAP.get(tool_name) or mcp_tools.get(tool_name)

    if tool is None:
        result = {
            "success": False,
            "error": f"Unknown tool '{tool_name}'. Available: {sorted(set(_TOOL_MAP) | set(mcp_tools))}",
        }
    else:
        if tool_name in mcp_tools:
            try:
                arguments = raw_args if isinstance(raw_args, dict) else {}
                if "arguments" in arguments and isinstance(arguments["arguments"], str):
                    arguments = json.loads(arguments["arguments"])
                if not isinstance(arguments, dict):
                    raise ValueError("MCP tool arguments must be a JSON object")
                result = call_mcp_tool(configurable["owner_id"], mcp_tools[tool_name], arguments)
            except Exception as e:
                result = {"success": False, "error": f"MCP tool '{tool_name}' failed: {e}"}
            return _record_tool_result(
                tool_name=tool_name, raw_args=raw_args, task=task, result=result,
                execution_history=execution_history, execution_memory=execution_memory,
                context_memory=context_memory,
            )
        schema = getattr(tool, "args_schema", None)
        if schema is not None:
            try:
                validated   = schema.model_validate(raw_args)
                invoke_args = validated.model_dump()
            except ValidationError as e:
                result      = {"success": False, "error": f"Invalid args for '{tool_name}': {e}"}
                invoke_args = None
        else:
            invoke_args = dict(raw_args) if isinstance(raw_args, dict) else raw_args

        if invoke_args is not None:
            try:
                result = tool.invoke(invoke_args)
            except Exception as e:
                result = {"success": False, "error": f"Tool '{tool_name}' raised: {e}"}

    return _record_tool_result(
        tool_name=tool_name,
        raw_args=raw_args,
        task=task,
        result=result,
        execution_history=execution_history,
        execution_memory=execution_memory,
        context_memory=context_memory,
    )


def _record_tool_result(
    *,
    tool_name: str,
    raw_args,
    task: str,
    result,
    execution_history: list,
    execution_memory: dict,
    context_memory,
) -> dict:
    step_key = f"tool_{len(execution_history) + 1}"
    history_entry = {
        "type":      "tool",
        "tool_name": tool_name,
        "tool_args": raw_args,
        "task":      task,
        "key":       step_key,
        "result":    result,
        "success":   not (isinstance(result, dict) and result.get("success") is False),
    }
    execution_memory, context_memory, stored_entry = record_execution(
        execution_memory,
        context_memory,
        key=step_key,
        value=result,
        description=task or f"Result of tool {tool_name or 'unknown'}",
        entry_type="tool",
        name=tool_name,
        task=task,
        success=history_entry["success"],
        metadata={"tool_name": tool_name, "tool_args": raw_args},
    )
    history_entry.update(stored_entry)
    execution_history.append(history_entry)

    tokens = count_content_tokens(result)

    success = history_entry["success"]
    from src.utils.trace import in_run, emit as trace_emit

    if in_run():
        trace_emit("tool.call.end" if success else "tool.call.error",
                   status="ok" if success else "error",
                   error=None if success else RuntimeError("tool_failed"), component="tool_node",
                   data={"tool_name": tool_name, "success": success})
    try:
        from src.utils.agent_logger import log_tool

        log_tool(
            "end",
            tool_name=tool_name,
            tool_args=raw_args,
            task=task,
            key=step_key,
            result=result,
            success=success,
            tokens=tokens,
        )
    except Exception:
        pass

    preview = truncate_for_aimessage(result)
    return {
        "messages": [
            AIMessage(
                content=f"Tool '{tool_name}' result: {preview}",
                additional_kwargs={
                    "ui_hidden": True,
                    "ui_step": {
                        "type": "tool",
                        "tool": {
                            "id": step_key,
                            "tool_name": tool_name,
                            "task": task,
                            "tool_args": raw_args,
                            "result": preview,
                            "success": success,
                            "status": "done" if success else "error",
                        },
                    },
                },
            )
        ],
        "execution_history": execution_history,
        "execution_memory":  execution_memory,
        "context_memory":    context_memory,
    }
