"""Backward-compatible contract tests for the Quant Trading HUD backend."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
API_DIR = REPO_ROOT / "api"

if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

import api_server  # noqa: E402


def test_static_api_endpoints_return_expected_contract() -> None:
    """Verify static endpoints expose monitoring-only liveness contract."""
    with TestClient(api_server.app) as client:
        health = client.get("/health")
        calendar = client.get("/calendar")

    assert health.status_code == 200
    assert health.json()["mode"] == "monitoring-only"
    assert calendar.status_code == 200
    assert len(calendar.json()["tasks"]) == 4


def test_data_response_has_typed_contract() -> None:
    """Verify /data has required nested fields."""
    with TestClient(api_server.app) as client:
        payload = client.get("/data").json()
    assert "market" in payload
    assert "signal" in payload
    assert "risk" in payload
    assert "system" in payload


def test_backend_does_not_include_private_trading_calls() -> None:
    """Verify backend source avoids private exchange and order-placement APIs.

    Returns:
        None.
    """

    forbidden_patterns = (
        "x-mbx-apikey",
        "create_order",
        "new_order",
        "signed",
        "futures",
        "margin",
        "leverage",
    )

    for path in API_DIR.rglob("*.py"):
        source = path.read_text(encoding="utf-8").lower()
        for pattern in forbidden_patterns:
            assert pattern not in source, f"Forbidden trading/API-key pattern {pattern!r} found in {path}"
