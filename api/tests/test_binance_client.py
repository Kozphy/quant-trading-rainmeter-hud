"""Unit tests for Binance client error handling."""

from __future__ import annotations

import httpx
import pytest

from app.services.binance_client import BinanceClient, BinanceClientError


def test_binance_client_handles_timeout_gracefully(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise BinanceClientError when request times out."""

    def _raise_timeout(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(httpx.Client, "get", _raise_timeout)
    client = BinanceClient(base_url="https://api.binance.com", timeout_seconds=0.1)
    with pytest.raises(BinanceClientError):
        client.fetch_24h_tickers(("BTCUSDT",))


def test_binance_client_handles_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise BinanceClientError when payload is malformed."""

    class DummyResponse:
        """Minimal fake response object."""

        def raise_for_status(self) -> None:
            return

        def json(self) -> list[str]:
            return ["not-a-dict"]

    def _fake_get(*args, **kwargs):  # type: ignore[no-untyped-def]
        return DummyResponse()

    monkeypatch.setattr(httpx.Client, "get", _fake_get)
    client = BinanceClient(base_url="https://api.binance.com", timeout_seconds=0.1)
    with pytest.raises(BinanceClientError):
        client.fetch_24h_tickers(("BTCUSDT",))

