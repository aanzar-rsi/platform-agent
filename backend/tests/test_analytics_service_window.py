from __future__ import annotations

from fastapi import HTTPException

from api.services.analytics_service import AnalyticsService


def test_validate_window_accepts_timezone_values():
    start, end = AnalyticsService._validate_window("2026-01-01T00:00:00+00:00", "2026-01-02T00:00:00+00:00")
    assert start is not None
    assert end is not None


def test_validate_window_rejects_invalid_timestamp():
    try:
        AnalyticsService._validate_window("bad", None)
    except HTTPException as exc:
        assert exc.status_code == 422
        assert "Invalid from timestamp" in str(exc.detail)
    else:
        raise AssertionError("expected HTTPException")


def test_validate_window_rejects_naive_timestamp():
    try:
        AnalyticsService._validate_window("2026-01-01T00:00:00", None)
    except HTTPException as exc:
        assert exc.status_code == 422
        assert "from must include timezone" in str(exc.detail)
    else:
        raise AssertionError("expected HTTPException")


def test_validate_window_rejects_reversed_range():
    try:
        AnalyticsService._validate_window("2026-01-02T00:00:00+00:00", "2026-01-01T00:00:00+00:00")
    except HTTPException as exc:
        assert exc.status_code == 422
        assert "from must be <= to" in str(exc.detail)
    else:
        raise AssertionError("expected HTTPException")
