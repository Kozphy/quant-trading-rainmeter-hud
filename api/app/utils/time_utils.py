"""Time helpers for consistent timezone-aware timestamps."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC datetime.

    Returns:
        A timezone-aware datetime in UTC.
    """

    return datetime.now(timezone.utc)


def to_iso8601(value: datetime) -> str:
    """Convert datetime into an ISO 8601 string.

    Args:
        value: Datetime value to format.

    Returns:
        ISO 8601 formatted timestamp.
    """

    return value.isoformat()

