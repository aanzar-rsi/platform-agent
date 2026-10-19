"""Policy schema normalization and authorization helpers.

Canonical policy schema (v2) remains backward compatible with legacy fields.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

SCOPES = ("USER", "TENANT", "AGENT")
DEFAULT_CHUNK_TYPES = (
    "resource",
    "user_preference",
    "user_details",
    "tenant_details",
    "workflow",
    "troubleshooting",
    "anti_pattern",
)


def _as_string_list(value: Any) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _bool(value: Any, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def _canonical_resource(entry: Any, *, kind: str) -> dict[str, Any] | None:
    if isinstance(entry, str):
        return {"type": kind, "name": entry, "enabled": True}
    if not isinstance(entry, dict):
        return None
    name = entry.get("name")
    if not isinstance(name, str) or not name:
        return None
    resource_type = entry.get("type") if isinstance(entry.get("type"), str) else kind
    enabled = entry.get("enabled")
    return {"type": resource_type, "name": name, "enabled": bool(enabled) if enabled is not None else True}


def normalize_armory_policy(raw: dict[str, Any] | None) -> dict[str, Any]:
    raw = raw if isinstance(raw, dict) else {}
    resources: dict[str, list[dict[str, Any]]] = {}
    groups: dict[str, dict[str, Any]] = {}

    raw_resources = raw.get("resources") if isinstance(raw.get("resources"), dict) else {}
    raw_groups = raw.get("groups") if isinstance(raw.get("groups"), dict) else {}

    for group_name, entries in raw_resources.items():
        if not isinstance(group_name, str):
            continue
        kind = "tool" if group_name == "tools" else "subagent" if group_name == "subagents" else group_name.rstrip("s")
        normalized_entries = []
        if isinstance(entries, list):
            for entry in entries:
                resource = _canonical_resource(entry, kind=kind)
                if resource:
                    normalized_entries.append(resource)
        resources[group_name] = normalized_entries

    # Legacy fields.
    legacy_tools = _as_string_list(raw.get("tools"))
    if legacy_tools is not None:
        resources["tools"] = []
        saw_mcp_wildcard = False
        for name in legacy_tools:
            if name == "mcp:*":
                saw_mcp_wildcard = True
                resources.setdefault("mcp_servers", [])
                if not any(item["name"] == "*" for item in resources["mcp_servers"]):
                    resources["mcp_servers"].append({"type": "mcp_server", "name": "*", "enabled": True})
                continue
            resources["tools"].append({"type": "tool", "name": name, "enabled": True})
        if not saw_mcp_wildcard and "mcp_servers" in resources:
            resources["mcp_servers"] = []
            raw_groups.setdefault("mcp_servers", {"enabled": False})

    legacy_subagents = _as_string_list(raw.get("subagents"))
    if legacy_subagents is not None:
        resources["subagents"] = []
        for name in legacy_subagents:
            resources["subagents"].append({"type": "subagent", "name": name, "enabled": True})

    for group_name, entries in resources.items():
        group_raw = raw_groups.get(group_name) if isinstance(raw_groups.get(group_name), dict) else {}
        if "enabled" in group_raw and isinstance(group_raw.get("enabled"), bool):
            enabled = group_raw["enabled"]
        else:
            # New groups are disabled by default unless explicitly configured.
            enabled = bool(entries)
        groups[group_name] = {"enabled": enabled}

    # Legacy configs imply group exists and enabled if configured.
    if legacy_tools is not None and "tools" not in groups:
        groups["tools"] = {"enabled": True}
    if legacy_subagents is not None and "subagents" not in groups:
        groups["subagents"] = {"enabled": True}

    tool_snapshot = sorted(_enabled_resource_names({"resources": resources, "groups": groups}, "tools"))
    if "*" in _enabled_resource_names({"resources": resources, "groups": groups}, "mcp_servers"):
        tool_snapshot.append("mcp:*")
    return {
        "version": 2,
        "resources": resources,
        "groups": groups,
        "confirm_tools": _bool(raw.get("confirm_tools"), True),
        # Legacy compatibility snapshots.
        "tools": tool_snapshot,
        "subagents": sorted(_enabled_resource_names({"resources": resources, "groups": groups}, "subagents")),
    }


def _enabled_resource_names(armory: dict[str, Any], group: str) -> set[str]:
    groups = armory.get("groups") if isinstance(armory.get("groups"), dict) else {}
    if not groups.get(group, {}).get("enabled", False):
        return set()
    resources = armory.get("resources") if isinstance(armory.get("resources"), dict) else {}
    out: set[str] = set()
    for item in resources.get(group, []) if isinstance(resources.get(group), list) else []:
        if isinstance(item, dict) and item.get("enabled", True) and isinstance(item.get("name"), str):
            out.add(item["name"])
    return out


def armory_resource_allowed(armory: dict[str, Any], *, group: str, name: str) -> bool:
    normalized = normalize_armory_policy(armory)
    allowed = _enabled_resource_names(normalized, group)
    if group == "tools" and name.startswith("mcp_"):
        mcp_allowed = _enabled_resource_names(normalized, "mcp_servers")
        return "*" in mcp_allowed or name in allowed
    return name in allowed


def normalize_memory_policy(raw: dict[str, Any] | None) -> dict[str, Any]:
    raw = raw if isinstance(raw, dict) else {}
    version = 2
    enabled = _bool(raw.get("enabled"), True)
    tenant_id = raw.get("tenant_id") if isinstance(raw.get("tenant_id"), str) else None

    legacy_read = _as_string_list(raw.get("read"))
    legacy_write = _as_string_list(raw.get("write"))
    read = [scope for scope in (legacy_read if legacy_read is not None else ["USER", "AGENT"]) if scope in SCOPES]
    write = [scope for scope in (legacy_write if legacy_write is not None else ["USER"]) if scope in SCOPES]
    promote = [scope for scope in _as_string_list(raw.get("promote") or ["TENANT", "AGENT"]) or [] if scope in {"TENANT", "AGENT"}]
    publish = [scope for scope in _as_string_list(raw.get("publish") or []) or [] if scope in {"TENANT", "AGENT"}]

    if not tenant_id:
        read = [scope for scope in read if scope != "TENANT"]
        write = [scope for scope in write if scope != "TENANT"]

    chunk_policies_raw = raw.get("chunks") if isinstance(raw.get("chunks"), dict) else {}
    chunk_policies: dict[str, dict[str, Any]] = {}
    known_types = set(DEFAULT_CHUNK_TYPES) | set(chunk_policies_raw.keys())
    for chunk_type in sorted(known_types):
        chunk_raw = chunk_policies_raw.get(chunk_type) if isinstance(chunk_policies_raw.get(chunk_type), dict) else {}
        chunk_enabled = _bool(chunk_raw.get("enabled"), chunk_type in DEFAULT_CHUNK_TYPES)
        chunk_read = [scope for scope in _as_string_list(chunk_raw.get("read") or read) or [] if scope in SCOPES]
        chunk_write = [scope for scope in _as_string_list(chunk_raw.get("write") or write) or [] if scope in SCOPES]
        chunk_promote = [scope for scope in _as_string_list(chunk_raw.get("promote") or promote) or [] if scope in {"TENANT", "AGENT"}]
        chunk_policies[chunk_type] = {
            "enabled": chunk_enabled,
            "read": chunk_read,
            "write": chunk_write,
            "promote": chunk_promote,
            "confirm_before_extracting": _bool(
                chunk_raw.get("confirm_before_extracting"),
                _bool(raw.get("confirm_before_extracting"), False),
            ),
            "allow_admin_promotion": _bool(
                chunk_raw.get("allow_admin_promotion"),
                _bool(raw.get("allow_admin_promotion"), True),
            ),
        }

    return {
        "version": version,
        "enabled": enabled,
        "tenant_id": tenant_id,
        "read": read,
        "write": write,
        "promote": promote,
        "publish": publish,
        "confirm_before_extracting": _bool(raw.get("confirm_before_extracting"), False),
        "allow_admin_promotion": _bool(raw.get("allow_admin_promotion"), True),
        "chunks": chunk_policies,
    }


def memory_action_allowed(
    memory: dict[str, Any],
    *,
    action: str,
    scope: str,
    chunk_type: str | None = None,
    promote_target: str | None = None,
) -> bool:
    policy = normalize_memory_policy(memory)
    if not policy.get("enabled", True):
        return False
    if scope not in SCOPES:
        return False
    if scope == "TENANT" and not policy.get("tenant_id"):
        return False
    if action in {"read", "write"} and scope not in policy.get(action, []):
        return False
    if action == "promote" and promote_target not in policy.get("promote", []):
        return False
    if not chunk_type:
        return True
    chunk = policy.get("chunks", {}).get(chunk_type)
    if not isinstance(chunk, dict) or not chunk.get("enabled", False):
        return False
    if action in {"read", "write"} and scope not in chunk.get(action, []):
        return False
    if action == "promote" and promote_target not in chunk.get("promote", []):
        return False
    return True


def memory_requires_extract_confirmation(memory: dict[str, Any], *, chunk_type: str) -> bool:
    policy = normalize_memory_policy(memory)
    if not policy.get("enabled", True):
        return False
    chunk = policy.get("chunks", {}).get(chunk_type)
    if not isinstance(chunk, dict) or not chunk.get("enabled", False):
        return False
    return bool(policy.get("confirm_before_extracting", False) or chunk.get("confirm_before_extracting", False))


def effective_memory_policy(agent_memory: dict[str, Any], user_memory_ceiling: dict[str, Any] | None = None) -> dict[str, Any]:
    if not user_memory_ceiling:
        return normalize_memory_policy(agent_memory)
    ceiling = normalize_memory_policy(user_memory_ceiling)
    requested = normalize_memory_policy(agent_memory)
    return intersect_memory(ceiling, requested, ceiling)


def intersect_armory(parent: dict[str, Any], requested: dict[str, Any], platform: dict[str, Any]) -> dict[str, Any]:
    p = normalize_armory_policy(parent)
    r = normalize_armory_policy(requested)
    t = normalize_armory_policy(platform)
    groups = sorted(set(p["resources"]) | set(r["resources"]) | set(t["resources"]) | set(p["groups"]) | set(r["groups"]) | set(t["groups"]))

    resources: dict[str, list[dict[str, Any]]] = {}
    group_flags: dict[str, dict[str, Any]] = {}
    for group in groups:
        p_enabled = p.get("groups", {}).get(group, {}).get("enabled", False)
        r_enabled = r.get("groups", {}).get(group, {}).get("enabled", False)
        t_enabled = t.get("groups", {}).get(group, {}).get("enabled", False)
        group_flags[group] = {"enabled": bool(p_enabled and r_enabled and t_enabled)}
        p_map = {item["name"]: item for item in p.get("resources", {}).get(group, [])}
        r_map = {item["name"]: item for item in r.get("resources", {}).get(group, [])}
        t_map = {item["name"]: item for item in t.get("resources", {}).get(group, [])}
        entries: list[dict[str, Any]] = []
        for name in sorted(set(p_map) & set(r_map) & set(t_map)):
            if p_map[name].get("enabled", True) and r_map[name].get("enabled", True) and t_map[name].get("enabled", True):
                entries.append({"type": p_map[name].get("type") or r_map[name].get("type") or t_map[name].get("type") or group.rstrip("s"), "name": name, "enabled": True})
        resources[group] = entries
    merged = {
        "version": 2,
        "resources": resources,
        "groups": group_flags,
        "confirm_tools": bool(p.get("confirm_tools", True) or r.get("confirm_tools", True) or t.get("confirm_tools", True)),
    }
    return normalize_armory_policy(merged)


def intersect_memory(parent: dict[str, Any], requested: dict[str, Any], platform: dict[str, Any]) -> dict[str, Any]:
    p = normalize_memory_policy(parent)
    r = normalize_memory_policy(requested)
    t = normalize_memory_policy(platform)
    out = deepcopy(p)
    out["enabled"] = bool(p.get("enabled", True) and r.get("enabled", True) and t.get("enabled", True))

    for field in ("read", "write", "promote", "publish"):
        out[field] = [
            scope for scope in p.get(field, [])
            if scope in r.get(field, []) and scope in t.get(field, [])
        ]

    out["tenant_id"] = (
        p.get("tenant_id")
        if p.get("tenant_id") and p.get("tenant_id") == r.get("tenant_id") == t.get("tenant_id")
        else None
    )
    if not out["tenant_id"]:
        out["read"] = [scope for scope in out["read"] if scope != "TENANT"]
        out["write"] = [scope for scope in out["write"] if scope != "TENANT"]

    out["confirm_before_extracting"] = bool(
        p.get("confirm_before_extracting", False)
        or r.get("confirm_before_extracting", False)
        or t.get("confirm_before_extracting", False)
    )
    out["allow_admin_promotion"] = bool(
        p.get("allow_admin_promotion", True)
        and r.get("allow_admin_promotion", True)
        and t.get("allow_admin_promotion", True)
    )

    chunk_keys = set(p.get("chunks", {})) | set(r.get("chunks", {})) | set(t.get("chunks", {}))
    chunks: dict[str, dict[str, Any]] = {}
    for chunk in chunk_keys:
        pc = p.get("chunks", {}).get(chunk, {})
        rc = r.get("chunks", {}).get(chunk, {})
        tc = t.get("chunks", {}).get(chunk, {})
        chunks[chunk] = {
            "enabled": bool(pc.get("enabled", False) and rc.get("enabled", False) and tc.get("enabled", False)),
            "read": [scope for scope in pc.get("read", []) if scope in rc.get("read", []) and scope in tc.get("read", [])],
            "write": [scope for scope in pc.get("write", []) if scope in rc.get("write", []) and scope in tc.get("write", [])],
            "promote": [scope for scope in pc.get("promote", []) if scope in rc.get("promote", []) and scope in tc.get("promote", [])],
            "confirm_before_extracting": bool(pc.get("confirm_before_extracting", False) or rc.get("confirm_before_extracting", False) or tc.get("confirm_before_extracting", False)),
            "allow_admin_promotion": bool(pc.get("allow_admin_promotion", True) and rc.get("allow_admin_promotion", True) and tc.get("allow_admin_promotion", True)),
        }
    out["chunks"] = chunks
    return normalize_memory_policy(out)
