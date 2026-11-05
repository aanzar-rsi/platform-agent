"""Govern working and episodic context before planner exposure."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as SearchTimeout
from contextvars import copy_context
from typing import Any, Callable

from src.agent.memory import count_content_tokens
from src.agent import kb
from src.agent.policy_schema import normalize_memory_policy
from src.models import llm_client

from .contracts import GovernedContextItem, GovernedContextResult, GovernedMemoryReference
from src.utils.trace import emit as trace_emit, in_run

SENSITIVITY_LEVELS = {"PUBLIC": 0, "INTERNAL": 1, "CONFIDENTIAL": 2, "RESTRICTED": 3}
_search_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="preflight-memory")
DEFAULT_GOVERNANCE_POLICY: dict[str, Any] = {
    "allowed_memory_scopes": ["USER", "AGENT"],
    "allowed_memory_types": ["workflow", "user_preference", "user_details", "tenant_details"],
    "maximum_sensitivity": "INTERNAL",
    "allow_memory_assumptions_for_reads": True,
    "episodic_memory_enabled": True,
    "memory_top_k": 5,
    "memory_context_tokens": 1500,
}
MEMORY_NEED_SYSTEM_PROMPT = """You classify whether a request needs durable episodic memory.
Episodic memory contains prior user preferences, prior workflows, and historical tenant context.
It is not current-turn conversation, tool output, authentication, permissions, or current external data.
Return strict JSON only: {"needed": true|false, "reason_code": "prior_context_required"|"personalization_useful"|"current_context_sufficient"}.
Set needed=true only when prior persisted context is required or materially useful to answer the request."""


def _timed_context_step(stage: str, started_at: float, *, reason_code: str = "completed") -> None:
    if in_run():
        trace_emit("run.timing.step", component="preflight_context",
                   duration_ms=(time.monotonic() - started_at) * 1000,
                   data={"stage": stage, "reason_code": reason_code})


def _bounded_int(value: Any, default: int, *, minimum: int, maximum: int) -> int:
    """Normalize a bounded integer policy value."""

    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return min(max(number, minimum), maximum)


def _string_list(value: Any, default: list[str]) -> list[str]:
    """Normalize a policy list into unique non-empty strings."""

    if not isinstance(value, list):
        return list(default)
    return list(dict.fromkeys(str(item).strip() for item in value if str(item).strip()))


def derive_governed_memory_policy(identity_context: dict[str, Any], config: dict | None) -> dict[str, Any]:
    """Intersect agent memory access with verified tenant governance."""

    configurable = (config or {}).get("configurable") or {}
    runtime_policy = configurable.get("policy") or {}
    agent_policy = runtime_policy.get("memory") or {}
    normalized = normalize_memory_policy(agent_policy)
    if "memory" not in runtime_policy:
        normalized["enabled"] = False
    tenant_id = str(identity_context.get("tenant_id") or "").strip()
    configured_tenant = str(normalized.get("tenant_id") or "").strip()
    if configured_tenant and configured_tenant != tenant_id:
        raise PermissionError("memory_tenant_mismatch")

    tenant_policy = identity_context.get("tenant_policy") or {}
    allowed_scopes = _string_list(
        tenant_policy.get("allowed_memory_scopes"),
        DEFAULT_GOVERNANCE_POLICY["allowed_memory_scopes"],
    )
    scopes = [scope for scope in normalized.get("read", []) if scope in allowed_scopes]
    if "TENANT" in scopes:
        if not tenant_id:
            scopes.remove("TENANT")
        else:
            normalized["tenant_id"] = tenant_id
    normalized["read"] = scopes

    allowed_types = set(_string_list(
        tenant_policy.get("allowed_memory_types"),
        DEFAULT_GOVERNANCE_POLICY["allowed_memory_types"],
    ))
    enabled_types = {
        name for name, policy in normalized.get("chunks", {}).items()
        if isinstance(policy, dict) and policy.get("enabled") and any(
            scope in scopes for scope in policy.get("read", [])
        )
    }
    if agent_policy and not isinstance(agent_policy.get("chunks"), dict):
        enabled_types = allowed_types
    enabled_types &= allowed_types
    allowed_types = enabled_types
    for chunk_type, chunk_policy in normalized.get("chunks", {}).items():
        if chunk_type not in enabled_types and isinstance(chunk_policy, dict):
            chunk_policy["read"] = []
    maximum_sensitivity = str(
        tenant_policy.get("maximum_sensitivity") or DEFAULT_GOVERNANCE_POLICY["maximum_sensitivity"]
    ).strip().upper()
    if maximum_sensitivity not in SENSITIVITY_LEVELS:
        maximum_sensitivity = DEFAULT_GOVERNANCE_POLICY["maximum_sensitivity"]
    if not allowed_types:
        normalized["read"] = []

    return {
        **normalized,
        "tenant_id": tenant_id if "TENANT" in scopes else None,
        "allowed_memory_types": sorted(allowed_types & enabled_types),
        "maximum_sensitivity": maximum_sensitivity,
        "allow_memory_assumptions_for_reads": bool(tenant_policy.get(
            "allow_memory_assumptions_for_reads",
            DEFAULT_GOVERNANCE_POLICY["allow_memory_assumptions_for_reads"],
        )),
        "episodic_memory_enabled": bool(tenant_policy.get(
            "episodic_memory_enabled", DEFAULT_GOVERNANCE_POLICY["episodic_memory_enabled"]
        )),
        "memory_top_k": _bounded_int(
            tenant_policy.get("memory_top_k"), DEFAULT_GOVERNANCE_POLICY["memory_top_k"], minimum=1, maximum=20
        ),
        "memory_context_tokens": _bounded_int(
            tenant_policy.get("memory_context_tokens"),
            DEFAULT_GOVERNANCE_POLICY["memory_context_tokens"],
            minimum=100,
            maximum=5000,
        ),
    }


def _working_items(
    state: dict[str, Any], identity_context: dict[str, Any], token_budget: int, maximum_sensitivity: str
) -> tuple[list[GovernedContextItem], int]:
    """Project visible current-thread memory into bounded governed items."""

    entries = (state.get("context_memory") or {}).get("entries") or []
    execution_memory = state.get("execution_memory") or {}
    items: list[GovernedContextItem] = []
    rejected = 0
    used_tokens = 0
    for visible in entries:
        if not isinstance(visible, dict) or not visible.get("key"):
            continue
        source = execution_memory.get(visible["key"])
        if not isinstance(source, dict):
            continue
        source_user = str(source.get("owner_user_id") or "")
        source_tenant = str(source.get("tenant_id") or "")
        if not source_user or not source_tenant:
            rejected += 1
            continue
        if source_user and source_user != str(identity_context.get("user_id") or ""):
            rejected += 1
            continue
        if source_tenant and source_tenant != str(identity_context.get("tenant_id") or ""):
            rejected += 1
            continue
        content = visible.get("content")
        tokens = count_content_tokens(content)
        if used_tokens + tokens > token_budget:
            rejected += 1
            break
        used_tokens += tokens
        sensitivity = str(source.get("sensitivity") or "INTERNAL").upper()
        if SENSITIVITY_LEVELS.get(sensitivity, 99) > SENSITIVITY_LEVELS[maximum_sensitivity]:
            rejected += 1
            continue
        items.append(GovernedContextItem(
            reference_id=f"working:{visible['key']}",
            kind="working",
            content=content,
            source={"type": "execution_memory", "key": visible["key"], "scope": "THREAD"},
            sensitivity=sensitivity if sensitivity in SENSITIVITY_LEVELS else "INTERNAL",
            provenance=str(source.get("provenance") or source.get("type") or "execution_memory"),
            complete=bool(visible.get("complete", False)),
        ))
    return items, rejected


def _episodic_items(hits: list[dict[str, Any]], policy: dict[str, Any], token_budget: int) -> tuple[list[GovernedContextItem], list[GovernedMemoryReference], int]:
    """Filter and budget authoritative KB hits for planner exposure."""

    items: list[GovernedContextItem] = []
    references: list[GovernedMemoryReference] = []
    rejected = 0
    used_tokens = 0
    ceiling = SENSITIVITY_LEVELS[policy["maximum_sensitivity"]]
    allowed_types = set(policy["allowed_memory_types"])
    for hit in hits:
        sensitivity = str(hit.get("sensitivity") or "INTERNAL").upper()
        if hit.get("chunk_type") not in allowed_types or SENSITIVITY_LEVELS.get(sensitivity, 99) > ceiling:
            rejected += 1
            continue
        content = str(hit.get("content") or "").strip()
        tokens = count_content_tokens(content)
        if not content or used_tokens + tokens > token_budget:
            rejected += 1
            continue
        used_tokens += tokens
        chunk_id = str(hit.get("chunk_id") or "")
        version_id = str(hit.get("active_version_id") or "")
        scope = str(hit.get("scope") or "")
        reference = GovernedMemoryReference(chunk_id=chunk_id, version_id=version_id, scope=scope)
        references.append(reference)
        items.append(GovernedContextItem(
            reference_id=f"memory:{version_id}",
            kind="episodic",
            content=content,
            source={
                "type": "episodic_memory",
                "chunk_id": chunk_id,
                "version_id": version_id,
                "scope": scope,
            },
            sensitivity=sensitivity,
            provenance="governed_kb",
            score=float(hit.get("score") or 0),
        ))
    return items, references, rejected


def classify_episodic_memory_need(
    query: str,
    *,
    working_context_count: int,
    model_id: str | None = None,
) -> tuple[bool, str]:
    """Use the configured LLM to classify whether durable episodic memory is useful."""

    result = llm_client.call_llm(
        f"Request: {query}\nAvailable current-turn working context items: {working_context_count}",
        system_prompt=MEMORY_NEED_SYSTEM_PROMPT,
        output_type="json",
        model_id=model_id or llm_client.DEFAULT_MODEL,
        temperature=0.0,
    )
    if not isinstance(result, dict) or not isinstance(result.get("needed"), bool):
        raise ValueError("invalid_memory_need_classification")
    reason_code = str(result.get("reason_code") or "").strip()
    allowed_reasons = {"prior_context_required", "personalization_useful", "current_context_sufficient"}
    if reason_code not in allowed_reasons:
        raise ValueError("invalid_memory_need_classification")
    if result["needed"] != (reason_code != "current_context_sufficient"):
        raise ValueError("invalid_memory_need_classification")
    return result["needed"], reason_code


def load_governed_context(
    *,
    request: dict[str, Any],
    state: dict[str, Any],
    identity_context: dict[str, Any],
    config: dict | None,
    search: Callable[..., list[dict[str, Any]]] | None = None,
    index_available: Callable[[], bool] | None = None,
    classify_memory_need: Callable[..., tuple[bool, str]] | None = None,
) -> GovernedContextResult:
    """Load policy-scoped working context first and optional episodic memory second."""

    try:
        policy = derive_governed_memory_policy(identity_context, config)
    except PermissionError as exc:
        return GovernedContextResult(
            "deny", str(exc), "Blocked request: memory tenant policy mismatch",
            context={"stage": "governed_context"},
        )

    budget = policy["memory_context_tokens"]
    working, working_rejected = _working_items(
        state, identity_context, budget, policy["maximum_sensitivity"]
    )
    working_tokens = sum(count_content_tokens(item.content) for item in working)
    details = {
        "working_context_count": len(working),
        "working_rejected_count": working_rejected,
        "episodic_candidate_count": 0,
        "episodic_selected_count": 0,
        "maximum_sensitivity": policy["maximum_sensitivity"],
    }
    if not policy.get("enabled") or not policy.get("episodic_memory_enabled") or not policy.get("read"):
        return GovernedContextResult(
            "degrade" if working_rejected else "allow",
            "memory_context_reduced" if working_rejected else "context_ready",
            context={"stage": "governed_context"},
            items=tuple(working),
            reduced=bool(working_rejected),
            degradations=("working_memory_filtered",) if working_rejected else (),
            details=details,
        )
    classifier = classify_memory_need or classify_episodic_memory_need
    step_started = time.monotonic()
    try:
        needs_episodic, classification_reason = classifier(
            str(request.get("query") or ""),
            working_context_count=len(working),
            model_id=((config or {}).get("configurable") or {}).get("model_id"),
        )
    except Exception:
        _timed_context_step("memory.need_classification", step_started, reason_code="unavailable")
        details["memory_need_reason"] = "classification_unavailable"
        return GovernedContextResult(
            "degrade",
            "memory_need_classification_unavailable",
            context={"stage": "governed_context"},
            items=tuple(working),
            reduced=True,
            degradations=("episodic_memory_not_evaluated",),
            details=details,
        )
    _timed_context_step("memory.need_classification", step_started, reason_code=classification_reason)
    details["memory_need_reason"] = classification_reason
    if not needs_episodic:
        return GovernedContextResult(
            "degrade" if working_rejected else "allow",
            "memory_context_reduced" if working_rejected else "context_ready",
            context={"stage": "governed_context"},
            items=tuple(working),
            reduced=bool(working_rejected),
            degradations=("working_memory_filtered",) if working_rejected else (),
            details=details,
        )

    if search is None or index_available is None:
        search = search or kb.search
        index_available = index_available or kb.memory_index_available
    step_started = time.monotonic()
    try:
        available = index_available()
    except Exception:
        available = False
    _timed_context_step("memory.index_check", step_started, reason_code="available" if available else "unavailable")
    if not available:
        return GovernedContextResult(
            "degrade",
            "optional_memory_unavailable",
            context={"stage": "governed_context"},
            items=tuple(working),
            reduced=True,
            degradations=("episodic_memory_unavailable",),
            details=details,
        )
    step_started = time.monotonic()
    try:
        # Optional recall must not hold the entire preflight path hostage.
        future = _search_executor.submit(copy_context().run, search,
                                         str(identity_context.get("user_id") or ""), policy,
                                         str(request.get("query") or ""), top_k=policy["memory_top_k"])
        hits = future.result(timeout=5)
    except SearchTimeout:
        future.cancel()
        _timed_context_step("memory.search", step_started, reason_code="timeout")
        return GovernedContextResult(
            "degrade", "optional_memory_timeout", context={"stage": "governed_context"},
            items=tuple(working), reduced=True, degradations=("episodic_memory_timeout",), details=details,
        )
    except PermissionError:
        _timed_context_step("memory.search", step_started, reason_code="denied")
        return GovernedContextResult(
            "deny",
            "memory_scope_mismatch",
            "Blocked request: governed memory authorization failed",
            context={"stage": "governed_context"},
            items=tuple(working),
            details=details,
        )
    except Exception:
        _timed_context_step("memory.search", step_started, reason_code="unavailable")
        return GovernedContextResult(
            "degrade",
            "optional_memory_unavailable",
            context={"stage": "governed_context"},
            items=tuple(working),
            reduced=True,
            degradations=("episodic_memory_unavailable",),
            details=details,
        )

    _timed_context_step("memory.search", step_started, reason_code="completed")
    details["episodic_candidate_count"] = len(hits)
    episodic, references, rejected = _episodic_items(hits, policy, max(0, budget - working_tokens))
    details["episodic_selected_count"] = len(episodic)
    details["episodic_rejected_count"] = rejected
    reduced = bool(rejected or working_rejected)
    return GovernedContextResult(
        "degrade" if reduced else "allow",
        "memory_context_reduced" if reduced else "context_ready",
        context={"stage": "governed_context"},
        items=tuple([*working, *episodic]),
        memory_references=tuple(references),
        reduced=reduced,
        degradations=("memory_items_filtered",) if reduced else (),
        details=details,
    )
