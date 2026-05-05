"""API contract tests for HUD and health endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_data_contract_shape() -> None:
    """Ensure /data returns stable typed fields."""

    with TestClient(app) as client:
        payload = client.get("/data").json()
    assert "market" in payload
    assert "signal" in payload
    assert "risk" in payload
    assert "system" in payload
    assert {"btc_price", "btc_change_24h", "eth_price", "eth_change_24h"} <= set(payload["market"].keys())
    assert {"action", "confidence", "regime", "reason", "rules_triggered"} <= set(payload["signal"].keys())
    assert {"bot_status", "data_status", "latency_ms", "last_success_at", "updated_at"} <= set(payload["system"].keys())


def test_health_and_metrics_endpoints() -> None:
    """Ensure health, ready, and metrics endpoints return expected fields."""

    with TestClient(app) as client:
        health = client.get("/health").json()
        ready = client.get("/ready").json()
        metrics = client.get("/metrics").json()
    assert health["status"] == "ok"
    assert "ready" in ready
    assert "request_count" in metrics

