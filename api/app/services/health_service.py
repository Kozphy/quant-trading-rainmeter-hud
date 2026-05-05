"""Health and readiness helpers for API endpoints."""

from __future__ import annotations


def is_ready(data_status: str, staleness_seconds: int, stale_after_seconds: int) -> bool:
    """Evaluate readiness from freshness and data status.

    Args:
        data_status: Current data status string.
        staleness_seconds: Current data age in seconds.
        stale_after_seconds: Freshness threshold.

    Returns:
        True when data can be considered live enough for serving.
    """

    return data_status == "LIVE" and staleness_seconds <= stale_after_seconds

