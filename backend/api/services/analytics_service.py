from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import HTTPException

from api.core.deps import CurrentUser, Repositories


class AnalyticsService:
    def __init__(self, repos: Repositories) -> None:
        self.repos = repos

    @staticmethod
    def _validate_window(start: str | None, end: str | None) -> tuple[str | None, str | None]:
        def parse(value: str | None, label: str) -> str | None:
            if value is None:
                return None
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=f"Invalid {label} timestamp") from exc
            if parsed.tzinfo is None:
                raise HTTPException(status_code=422, detail=f"{label} must include timezone")
            return parsed.isoformat()

        parsed_start = parse(start, "from")
        parsed_end = parse(end, "to")
        if parsed_start and parsed_end and parsed_start > parsed_end:
            raise HTTPException(status_code=422, detail="from must be <= to")
        return parsed_start, parsed_end

    def summary(
        self,
        user: CurrentUser,
        agent_id: str | None = None,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> dict[str, Any]:
        # Non-admins only see their own events
        uid = None if user.role == "admin" else user.uid
        parsed_start, parsed_end = self._validate_window(start, end)
        return self.repos.analytics.summary(uid=uid, agent_id=agent_id, start=parsed_start, end=parsed_end)
