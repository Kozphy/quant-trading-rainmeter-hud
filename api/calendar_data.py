"""Static calendar data for the Rainmeter HUD."""

from __future__ import annotations

from datetime import datetime


CALENDAR_TASKS = [
    {"time": "09:00", "name": "Risk Review"},
    {"time": "14:30", "name": "Backtest Batch"},
    {"time": "20:30", "name": "US Macro Watch"},
    {"time": "23:00", "name": "Execution Log Audit"},
]


def get_calendar_payload(now: datetime) -> dict[str, str | list[dict[str, str]]]:
    """Build the static trading operations calendar payload.

    Args:
        now: Current local datetime.

    Returns:
        A dictionary containing today's date and the task list.
    """

    return {"date": now.strftime("%Y-%m-%d"), "tasks": CALENDAR_TASKS}
