from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from psycopg.types.json import Jsonb

from api.db.postgres import execute
from api.db.postgres import fetch_all, fetch_one


logger = logging.getLogger(__name__)


@dataclass
class _TimeWindow:
    start: str | None
    end: str | None


class AnalyticsRepository:
    _ESTIMATED_RATES_PER_MILLION: dict[str, dict[str, float]] = {
        "gpt-4o": {"input": 2.5, "output": 10.0, "cached_input": 1.25, "reasoning": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.6, "cached_input": 0.075, "reasoning": 0.6},
        "gpt-4.1": {"input": 2.0, "output": 8.0, "cached_input": 1.0, "reasoning": 8.0},
        "gpt-4.1-mini": {"input": 0.4, "output": 1.6, "cached_input": 0.2, "reasoning": 1.6},
        "o4-mini": {"input": 1.1, "output": 4.4, "cached_input": 0.55, "reasoning": 4.4},
        "claude-3-5-sonnet": {"input": 3.0, "output": 15.0, "cached_input": 0.3, "reasoning": 15.0},
        "claude-3-7-sonnet": {"input": 3.0, "output": 15.0, "cached_input": 0.3, "reasoning": 15.0},
        "claude-sonnet-4": {"input": 3.0, "output": 15.0, "cached_input": 0.3, "reasoning": 15.0},
        "gemini-1.5-pro": {"input": 1.25, "output": 5.0, "cached_input": 0.3125, "reasoning": 5.0},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.3, "cached_input": 0.01875, "reasoning": 0.3},
    }
    _table_ready = False

    _CREATE_ANALYTICS_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS analytics_events (
        event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        owner_id TEXT,
        agent_id TEXT,
        event_type TEXT NOT NULL,
        payload JSONB NOT NULL DEFAULT '{}'
    )
    """
    _CREATE_ANALYTICS_INDEXES = (
        "CREATE INDEX IF NOT EXISTS idx_analytics_events_owner_time ON analytics_events (owner_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_analytics_events_agent_time ON analytics_events (agent_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_analytics_events_type_time ON analytics_events (event_type, created_at DESC)",
    )

    def _ensure_table(self) -> None:
        if self._table_ready:
            return
        execute(self._CREATE_ANALYTICS_TABLE_SQL)
        for statement in self._CREATE_ANALYTICS_INDEXES:
            execute(statement)
        self._table_ready = True

    def append(self, event_type: str, *, uid: str | None = None, payload: dict[str, Any] | None = None) -> None:
        payload = payload or {}
        try:
            self._ensure_table()
            execute(
                """
                INSERT INTO analytics_events (owner_id, agent_id, event_type, payload)
                VALUES (%s, %s, %s, %s::jsonb)
                """,
                (uid, str(payload.get("agent_id")) if payload.get("agent_id") else None, event_type, Jsonb(payload)),
            )
        except Exception:
            logger.warning("analytics append failed", exc_info=True)

    def summary(
        self,
        *,
        uid: str | None = None,
        agent_id: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> dict[str, Any]:
        window = _TimeWindow(start=start, end=end)
        llm = self._llm_analytics(uid=uid, agent_id=agent_id, window=window)
        messages = self._message_counts(uid=uid, agent_id=agent_id, window=window)
        planner = self._planner_analytics(uid=uid, agent_id=agent_id, window=window)
        runtime = self._runtime_analytics(uid=uid, agent_id=agent_id, window=window, llm_ms=llm["latency_ms_total"])
        armory = self._armory_analytics(uid=uid, agent_id=agent_id)
        memory = self._memory_analytics(uid=uid, agent_id=agent_id, window=window)
        context = self._context_analytics(uid=uid, agent_id=agent_id, window=window)

        response: dict[str, Any] = {
            "scope": {
                "type": "agent" if agent_id else ("global" if uid is None else "user"),
                "uid": uid,
                "agent_id": agent_id,
                "from": start,
                "to": end,
            },
            "llm": {
                "calls": llm["calls"],
                "tokens": llm["tokens"],
                "cost_usd": llm["cost_usd"],
                "models": llm["models"],
            },
            "agent": {
                "messages": messages,
                "context": context,
                "planner": planner,
                "armory": armory,
                "memory": memory,
                "runtime": runtime,
            },
        }
        if agent_id is None:
            response["agents"] = self._agent_counts(uid=uid)
        response["uid"] = uid
        response["agent_id"] = agent_id
        response["by_type"] = {
            "run_complete": runtime["successful_runs"],
            "run_error": runtime["failed_runs"],
            "agent_create": (response.get("agents") or {}).get("total", 0),
        }
        response["total_events"] = sum(int(v) for v in response["by_type"].values())
        return response

    def _where_scope(self, *, uid: str | None, agent_id: str | None, window: _TimeWindow, ts_col: str) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if uid is not None:
            clauses.append("a.owner_id::text = %s")
            params.append(uid)
        if agent_id is not None:
            clauses.append("a.agent_id::text = %s")
            params.append(agent_id)
        if window.start:
            clauses.append(f"{ts_col} >= %s")
            params.append(window.start)
        if window.end:
            clauses.append(f"{ts_col} < %s")
            params.append(window.end)
        return (" AND ".join(clauses), params)

    def _llm_rows(self, *, uid: str | None, agent_id: str | None, window: _TimeWindow) -> list[dict[str, Any]]:
        where = ["1=1"]
        params: list[Any] = []
        if uid is not None:
            where.append("a.owner_id::text = %s")
            params.append(uid)
        if agent_id is not None:
            where.append("l.agent_id = %s")
            params.append(agent_id)
        if window.start:
            where.append("l.created_at >= %s")
            params.append(window.start)
        if window.end:
            where.append("l.created_at < %s")
            params.append(window.end)
        return fetch_all(
            f"""
            SELECT
                l.model_id,
                l.provider_model,
                l.status,
                l.cached,
                l.prompt_tokens,
                l.completion_tokens,
                l.total_tokens,
                l.cost_usd,
                l.usage,
                l.latency_ms,
                l.prompt,
                l.created_at
            FROM llm_calls l
            JOIN agent_cores a ON a.agent_id::text = l.agent_id
            WHERE {' AND '.join(where)}
            ORDER BY l.created_at ASC
            """,
            tuple(params),
        )

    @staticmethod
    def _usage_int(usage: dict[str, Any] | None, *paths: str) -> int:
        value: Any = usage or {}
        for key in paths:
            if not isinstance(value, dict):
                return 0
            value = value.get(key)
        if value is None:
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _token_breakdown(self, row: dict[str, Any]) -> dict[str, int]:
        usage = row.get("usage") if isinstance(row.get("usage"), dict) else {}
        prompt_tokens = int(row.get("prompt_tokens") or 0)
        completion_tokens = int(row.get("completion_tokens") or 0)
        total_tokens = int(row.get("total_tokens") or (prompt_tokens + completion_tokens))
        cached_input = max(
            self._usage_int(usage, "prompt_tokens_details", "cached_tokens"),
            self._usage_int(usage, "input_token_details", "cached_tokens"),
            self._usage_int(usage, "cache_read_input_tokens"),
        )
        cache_creation = max(
            self._usage_int(usage, "cache_creation_input_tokens"),
            self._usage_int(usage, "input_token_details", "cache_creation_tokens"),
        )
        reasoning = max(
            self._usage_int(usage, "output_tokens_details", "reasoning_tokens"),
            self._usage_int(usage, "completion_tokens_details", "reasoning_tokens"),
            self._usage_int(usage, "reasoning_tokens"),
        )
        audio_input = max(
            self._usage_int(usage, "prompt_tokens_details", "audio_tokens"),
            self._usage_int(usage, "input_token_details", "audio_tokens"),
        )
        audio_output = max(
            self._usage_int(usage, "completion_tokens_details", "audio_tokens"),
            self._usage_int(usage, "output_tokens_details", "audio_tokens"),
        )
        other = max(total_tokens - prompt_tokens - completion_tokens, 0)
        return {
            "input": prompt_tokens,
            "output": completion_tokens,
            "cached_input": cached_input,
            "cache_creation": cache_creation,
            "reasoning": reasoning,
            "audio_input": audio_input,
            "audio_output": audio_output,
            "other": other,
            "total": total_tokens,
        }

    def _estimate_cost(self, model: str, tokens: dict[str, int]) -> float:
        key = (model or "").strip().lower()
        rates = self._ESTIMATED_RATES_PER_MILLION.get(key)
        if rates is None:
            for candidate, candidate_rates in self._ESTIMATED_RATES_PER_MILLION.items():
                if candidate in key:
                    rates = candidate_rates
                    break
        if rates is None:
            return 0.0
        return (
            (tokens["input"] / 1_000_000.0) * rates["input"]
            + (tokens["output"] / 1_000_000.0) * rates["output"]
            + (tokens["cached_input"] / 1_000_000.0) * rates["cached_input"]
            + (tokens["reasoning"] / 1_000_000.0) * rates["reasoning"]
        )

    def _llm_analytics(self, *, uid: str | None, agent_id: str | None, window: _TimeWindow) -> dict[str, Any]:
        rows = self._llm_rows(uid=uid, agent_id=agent_id, window=window)
        calls = {
            "total": len(rows),
            "successful": 0,
            "failed": 0,
            "cached": 0,
        }
        tokens = {
            "input": 0,
            "output": 0,
            "cached_input": 0,
            "cache_creation": 0,
            "reasoning": 0,
            "audio_input": 0,
            "audio_output": 0,
            "other": 0,
            "total": 0,
        }
        actual_cost = 0.0
        estimated_cost = 0.0
        latency_ms_total = 0
        models: dict[str, dict[str, Any]] = {}

        for row in rows:
            status = str(row.get("status") or "ok").lower()
            if status == "ok":
                calls["successful"] += 1
            else:
                calls["failed"] += 1
            if bool(row.get("cached")):
                calls["cached"] += 1

            breakdown = self._token_breakdown(row)
            for key, value in breakdown.items():
                tokens[key] += value

            model = str(row.get("provider_model") or row.get("model_id") or "unknown")
            bucket = models.setdefault(
                model,
                {
                    "model": model,
                    "calls": 0,
                    "tokens": {k: 0 for k in tokens.keys()},
                    "cost_usd": {"actual": 0.0, "estimated": 0.0, "total": 0.0},
                },
            )
            bucket["calls"] += 1
            for key, value in breakdown.items():
                bucket["tokens"][key] += value

            model_estimated_cost = self._estimate_cost(model, breakdown)
            if row.get("cost_usd") is not None:
                try:
                    actual = float(row.get("cost_usd"))
                except (TypeError, ValueError):
                    actual = 0.0
                actual_cost += actual
                bucket["cost_usd"]["actual"] += actual
            else:
                estimated_cost += model_estimated_cost
                bucket["cost_usd"]["estimated"] += model_estimated_cost

            bucket["cost_usd"]["total"] = bucket["cost_usd"]["actual"] + bucket["cost_usd"]["estimated"]
            latency_ms_total += int(row.get("latency_ms") or 0)

        models_list = sorted(models.values(), key=lambda item: item["calls"], reverse=True)
        return {
            "calls": calls,
            "tokens": tokens,
            "cost_usd": {
                "actual": round(actual_cost, 8),
                "estimated": round(estimated_cost, 8),
                "total": round(actual_cost + estimated_cost, 8),
            },
            "models": models_list,
            "latency_ms_total": latency_ms_total,
            "latest_llm_row": rows[-1] if rows else None,
        }

    def _message_counts(self, *, uid: str | None, agent_id: str | None, window: _TimeWindow) -> dict[str, int]:
        where_sql, params = self._where_scope(uid=uid, agent_id=agent_id, window=window, ts_col="m.created_at")
        where_clause = f"WHERE {where_sql}" if where_sql else ""
        rows = fetch_all(
            f"""
            SELECT m.role, count(*)::int AS n
            FROM messages m
            JOIN agent_cores a ON a.agent_id = m.agent_id
            {where_clause}
            GROUP BY m.role
            """,
            tuple(params),
        )
        result = {"total": 0, "human": 0, "ai": 0, "system": 0, "tool": 0, "other": 0}
        for row in rows:
            role = str(row.get("role") or "").lower()
            count = int(row.get("n") or 0)
            result["total"] += count
            if role in {"human", "user"}:
                result["human"] += count
            elif role in {"ai", "assistant"}:
                result["ai"] += count
            elif role == "system":
                result["system"] += count
            elif role == "tool":
                result["tool"] += count
            else:
                result["other"] += count
        return result

    def _planner_analytics(self, *, uid: str | None, agent_id: str | None, window: _TimeWindow) -> dict[str, Any]:
        where_sql, params = self._where_scope(uid=uid, agent_id=agent_id, window=window, ts_col="m.created_at")
        where_clause = f"WHERE {where_sql}" if where_sql else ""
        rows = fetch_all(
            f"""
            SELECT m.plan_summary
            FROM messages m
            JOIN agent_cores a ON a.agent_id = m.agent_id
            {where_clause}
            """,
            tuple(params),
        )
        plans_created = 0
        steps_created = 0
        steps_completed = 0
        steps_failed = 0
        retries = 0
        latest_plan_overhead = {
            "total_tokens": 0,
            "tool_definitions": 0,
            "completed_steps": 0,
            "current_steps": 0,
            "remaining_steps": 0,
            "other": 0,
        }

        for row in rows:
            plan = row.get("plan_summary")
            if not isinstance(plan, dict):
                continue
            plans_created += 1
            steps = plan.get("steps")
            if isinstance(steps, list):
                steps_created += len(steps)
                for step in steps:
                    if not isinstance(step, dict):
                        continue
                    status = str(step.get("status") or "").lower()
                    if status in {"done", "completed", "success"}:
                        steps_completed += 1
                    if status in {"failed", "error"}:
                        steps_failed += 1
            retries += int(plan.get("retry_count") or 0) if isinstance(plan.get("retry_count"), (int, float)) else 0

            candidate_overhead = plan.get("token_overhead")
            if isinstance(candidate_overhead, dict):
                latest_plan_overhead = {
                    "total_tokens": int(candidate_overhead.get("total_tokens") or 0),
                    "tool_definitions": int(candidate_overhead.get("tool_definitions") or 0),
                    "completed_steps": int(candidate_overhead.get("completed_steps") or 0),
                    "current_steps": int(candidate_overhead.get("current_steps") or 0),
                    "remaining_steps": int(candidate_overhead.get("remaining_steps") or 0),
                    "other": int(candidate_overhead.get("other") or 0),
                }

        return {
            "invocations": plans_created,
            "plans_created": plans_created,
            "steps_created": steps_created,
            "steps_completed": steps_completed,
            "steps_failed": steps_failed,
            "retries": retries,
            "tokens": {"input": 0, "output": 0, "overhead": latest_plan_overhead["total_tokens"]},
            "current_plan_overhead": latest_plan_overhead,
        }

    @staticmethod
    def _resource_enabled(items: list[dict[str, Any]] | None) -> int:
        if not items:
            return 0
        return sum(1 for item in items if isinstance(item, dict) and item.get("enabled", True))

    def _armory_analytics(self, *, uid: str | None, agent_id: str | None) -> dict[str, Any]:
        where = ["a.parent_agent_id IS NULL", "a.owner_type = 'user'"]
        params: list[Any] = []
        if uid is not None:
            where.append("a.owner_id::text = %s")
            params.append(uid)
        if agent_id is not None:
            where.append("a.agent_id::text = %s")
            params.append(agent_id)
        rows = fetch_all(
            f"SELECT a.agent_id::text AS agent_id, a.policy FROM agent_cores a WHERE {' AND '.join(where)}",
            tuple(params),
        )

        tools_count = 0
        mcp_servers_count = 0
        subagents_count = 0
        for row in rows:
            policy = row.get("policy") if isinstance(row.get("policy"), dict) else {}
            armory = policy.get("armory") if isinstance(policy.get("armory"), dict) else {}
            resources = armory.get("resources") if isinstance(armory.get("resources"), dict) else {}
            tools_count += self._resource_enabled(resources.get("tools") if isinstance(resources.get("tools"), list) else [])
            mcp_servers_count += self._resource_enabled(resources.get("mcp_servers") if isinstance(resources.get("mcp_servers"), list) else [])
            subagents_count += self._resource_enabled(resources.get("subagents") if isinstance(resources.get("subagents"), list) else [])

        return {
            "configured": {
                "tools": tools_count,
                "mcp_servers": mcp_servers_count,
                "mcp_tools": 0,
                "subagents": subagents_count,
            },
            "invocations": {"tools": 0, "subagents": 0},
            "failures": {"tools": 0, "subagents": 0, "authorization": 0, "mcp_connection": 0},
            "by_resource": [],
        }

    def _memory_analytics(self, *, uid: str | None, agent_id: str | None, window: _TimeWindow) -> dict[str, int]:
        where = ["1=1"]
        params: list[Any] = []
        if uid is not None:
            where.append("owner_id::text = %s")
            params.append(uid)
        if agent_id is not None:
            where.append("agent_id::text = %s")
            params.append(agent_id)
        if window.start:
            where.append("created_at >= %s")
            params.append(window.start)
        if window.end:
            where.append("created_at < %s")
            params.append(window.end)
        row = fetch_one(
            f"""
            SELECT
                count(*)::int AS attempts,
                sum(CASE WHEN state IN ('REJECTED') THEN 1 ELSE 0 END)::int AS failures,
                sum(CASE WHEN state IN ('COMPLETED') THEN 1 ELSE 0 END)::int AS completed,
                sum(CASE WHEN state IN ('APPROVED') THEN 1 ELSE 0 END)::int AS promoted
            FROM memory_extraction_requests
            WHERE {' AND '.join(where)}
            """,
            tuple(params),
        ) or {}
        return {
            "extraction_attempts": int(row.get("attempts") or 0),
            "extraction_failures": int(row.get("failures") or 0),
            "chunks_extracted": int(row.get("completed") or 0),
            "chunks_promoted": int(row.get("promoted") or 0),
            "reads": 0,
            "writes": 0,
        }

    def _runtime_analytics(
        self,
        *,
        uid: str | None,
        agent_id: str | None,
        window: _TimeWindow,
        llm_ms: int,
    ) -> dict[str, Any]:
        where_sql, params = self._where_scope(uid=uid, agent_id=agent_id, window=window, ts_col="e.started_at")
        where_clause = f"WHERE {where_sql}" if where_sql else ""
        row = fetch_one(
            f"""
            SELECT
                count(*)::int AS runs,
                sum(CASE WHEN e.state = 'completed' THEN 1 ELSE 0 END)::int AS completed,
                sum(CASE WHEN e.state = 'failed' THEN 1 ELSE 0 END)::int AS failed,
                sum(CASE WHEN e.state = 'cancelled' THEN 1 ELSE 0 END)::int AS cancelled,
                sum(EXTRACT(EPOCH FROM (COALESCE(e.ended_at, now()) - e.started_at)) * 1000)::bigint AS total_ms,
                avg(EXTRACT(EPOCH FROM (COALESCE(e.ended_at, now()) - e.started_at)) * 1000)::bigint AS average_ms,
                max(EXTRACT(EPOCH FROM (COALESCE(e.ended_at, now()) - e.started_at)) * 1000)::bigint AS maximum_ms
            FROM agent_executions e
            JOIN agent_cores a ON a.agent_id = e.agent_id
            {where_clause}
            """,
            tuple(params),
        ) or {}
        total_ms = int(row.get("total_ms") or 0)
        llm_split = max(llm_ms, 0)
        other_ms = max(total_ms - llm_split, 0)
        return {
            "runs": int(row.get("runs") or 0),
            "successful_runs": int(row.get("completed") or 0),
            "failed_runs": int(row.get("failed") or 0),
            "cancelled_runs": int(row.get("cancelled") or 0),
            "total_ms": total_ms,
            "average_ms": int(row.get("average_ms") or 0),
            "maximum_ms": int(row.get("maximum_ms") or 0),
            "splits": {
                "planning_ms": 0,
                "llm_ms": llm_split,
                "tool_ms": 0,
                "subagent_ms": 0,
                "memory_ms": 0,
                "checkpoint_ms": 0,
                "other_ms": other_ms,
            },
        }

    def _context_analytics(self, *, uid: str | None, agent_id: str | None, window: _TimeWindow) -> dict[str, Any]:
        rows = self._llm_rows(uid=uid, agent_id=agent_id, window=window)
        prompt_tokens = [int(row.get("prompt_tokens") or 0) for row in rows]
        latest = rows[-1] if rows else None
        latest_total = int((latest or {}).get("prompt_tokens") or 0)

        latest_components = {
            "system": 0,
            "previous_messages": 0,
            "plan": 0,
            "armory": 0,
            "memory": 0,
            "tool_results": 0,
            "current_request": 0,
            "other": latest_total,
        }
        latest_composed = {
            key: {
                "tokens": value,
                "percentage": round((value / latest_total) * 100.0, 4) if latest_total else 0.0,
            }
            for key, value in latest_components.items()
        }
        sample_count = len(prompt_tokens)
        aggregate_total = sum(prompt_tokens)
        avg_tokens = int(aggregate_total / sample_count) if sample_count else 0
        component_percentages = {key: (100.0 if key == "other" and aggregate_total else 0.0) for key in latest_components.keys()}
        component_tokens = {key: (aggregate_total if key == "other" else 0) for key in latest_components.keys()}

        return {
            "latest": {"total_tokens": latest_total, "components": latest_composed},
            "aggregate": {
                "samples": sample_count,
                "average_tokens": avg_tokens,
                "maximum_tokens": max(prompt_tokens) if prompt_tokens else 0,
                "component_tokens": component_tokens,
                "component_percentages": component_percentages,
            },
        }

    def _agent_counts(self, *, uid: str | None) -> dict[str, int]:
        where = ["parent_agent_id IS NULL", "owner_type = 'user'"]
        params: list[Any] = []
        if uid is not None:
            where.append("owner_id::text = %s")
            params.append(uid)
        row = fetch_one(
            f"""
            SELECT
                count(*)::int AS total,
                sum(CASE WHEN state = 'open' THEN 1 ELSE 0 END)::int AS active,
                sum(CASE WHEN state = 'closed' THEN 1 ELSE 0 END)::int AS deleted,
                sum(CASE WHEN latest_session_id IS NOT NULL THEN 1 ELSE 0 END)::int AS with_runs
            FROM agent_cores
            WHERE {' AND '.join(where)}
            """,
            tuple(params),
        ) or {}
        return {
            "total": int(row.get("total") or 0),
            "active": int(row.get("active") or 0),
            "deleted": int(row.get("deleted") or 0),
            "with_runs": int(row.get("with_runs") or 0),
        }
