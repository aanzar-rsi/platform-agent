from __future__ import annotations

from typing import Any

from api.core.deps import CurrentUser, Repositories
from src.tools import INTERNAL_TOOLS
from api.services.mcp_runtime import available_mcp_tools


def _parameters_from_schema(schema: Any) -> list[dict[str, Any]]:
    if schema is None:
        return []
    try:
        js = schema.model_json_schema()
    except Exception:
        return []
    props = js.get("properties") or {}
    if not isinstance(props, dict):
        return []
    required = set(js.get("required") or [])
    out: list[dict[str, Any]] = []
    for name, meta in props.items():
        if not isinstance(meta, dict):
            continue
        param_type = meta.get("type")
        if not param_type and meta.get("anyOf"):
            param_type = "|".join(
                str(x.get("type", "any"))
                for x in meta["anyOf"]
                if isinstance(x, dict)
            )
        out.append(
            {
                "name": str(name),
                "type": str(param_type or "any"),
                "description": str(meta.get("description") or "").strip(),
                "required": name in required,
            }
        )
    return out


def _parameters_from_mcp_item(item: dict[str, Any]) -> list[dict[str, Any]]:
    raw = item.get("parameters")
    if isinstance(raw, list):
        out: list[dict[str, Any]] = []
        for p in raw:
            if isinstance(p, dict) and p.get("name"):
                out.append(
                    {
                        "name": str(p.get("name", "")),
                        "type": str(p.get("type") or "any"),
                        "description": str(p.get("description") or "").strip(),
                        "required": bool(p.get("required")),
                    }
                )
        if out:
            return out
    schema = item.get("inputSchema") or item.get("input_schema")
    if isinstance(schema, dict):
        return _parameters_from_schema_dict(schema)
    return []


def _parameters_from_schema_dict(schema: dict[str, Any]) -> list[dict[str, Any]]:
    props = schema.get("properties") or {}
    if not isinstance(props, dict):
        return []
    required = set(schema.get("required") or [])
    out: list[dict[str, Any]] = []
    for name, meta in props.items():
        if not isinstance(meta, dict):
            continue
        param_type = meta.get("type") or "any"
        out.append(
            {
                "name": str(name),
                "type": str(param_type),
                "description": str(meta.get("description") or "").strip(),
                "required": name in required,
            }
        )
    return out


def _tool_info(tool: Any) -> dict[str, Any]:
    name = getattr(tool, "name", None)
    if not name and hasattr(tool, "func"):
        name = getattr(tool.func, "__name__", "unknown")
    description = getattr(tool, "description", None) or ""
    if not description and hasattr(tool, "func") and tool.func.__doc__:
        description = tool.func.__doc__.strip().split("\n")[0]
    info: dict[str, Any] = {
        "name": str(name or "unknown"),
        "description": str(description).strip(),
    }
    params = _parameters_from_schema(getattr(tool, "args_schema", None))
    if params:
        info["parameters"] = params
    return info


def _mcp_tools_from_metadata(server: dict[str, Any]) -> list[dict[str, Any]]:
    raw = (server.get("metadata") or {}).get("tools") or []
    if not isinstance(raw, list):
        return []

    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            out.append(
                {
                    "name": item.strip(),
                    "description": "",
                    "server_id": str(server.get("id", "")),
                    "server_name": str(server.get("name", "")),
                }
            )
        elif isinstance(item, dict) and item.get("name"):
            info: dict[str, Any] = {
                "name": str(item.get("name", "")),
                "description": str(item.get("description") or "").strip(),
                "server_id": str(server.get("id", "")),
                "server_name": str(server.get("name", "")),
            }
            params = _parameters_from_mcp_item(item)
            if params:
                info["parameters"] = params
            out.append(info)
    return out


class ToolsService:
    def __init__(self, repos: Repositories) -> None:
        self.repos = repos

    def list_catalog(self, user: CurrentUser) -> dict[str, Any]:
        internal = [_tool_info(tool) for tool in INTERNAL_TOOLS]
        mcp = [
            {"name": tool.name, "description": tool.description,
             "server_id": tool.server_id, "server_name": tool.server_name,
             "parameters": _parameters_from_schema_dict(tool.input_schema)}
            for tool in available_mcp_tools(user.uid).values()
        ]
        return {
            "internal": internal,
            "mcp": mcp,
            "counts": {"internal": len(internal), "mcp": len(mcp)},
        }
