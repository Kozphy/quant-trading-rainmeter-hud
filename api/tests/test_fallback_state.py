"""Fallback behavior tests for stale and error status handling."""

from __future__ import annotations

from datetime import timedelta

from app.schemas import MarketSnapshot
from app.main import CACHE, MARKET_DATA
from app.services.binance_client import BinanceClientError
from app.utils.time_utils import utc_now


def test_fallback_uses_last_known_good_when_binance_fails(monkeypatch) -> None:
    """Use cached snapshot and STALE status after fetch failure."""

    now = utc_now()
    CACHE.update(
        MarketSnapshot(btc_price=65000.0, btc_change_24h=0.4, eth_price=3200.0, eth_change_24h=0.3),
        now - timedelta(seconds=45),
    )

    def _raise_error(symbols):  # type: ignore[no-untyped-def]
        raise BinanceClientError("network failure")

    monkeypatch.setattr(MARKET_DATA.binance_client, "fetch_24h_tickers", _raise_error)
    fallback = MARKET_DATA.fetch_market_snapshot(("BTCUSDT", "ETHUSDT"), utc_now())
    assert fallback.data_status == "STALE"
    assert fallback.bot_status == "WARNING"
    assert fallback.staleness_seconds >= 45


def test_no_fake_live_status_when_data_is_stale(monkeypatch) -> None:
    """Never report LIVE while serving cached stale data."""

    def _raise_error(symbols):  # type: ignore[no-untyped-def]
        raise BinanceClientError("still failing")

    monkeypatch.setattr(MARKET_DATA.binance_client, "fetch_24h_tickers", _raise_error)
    result = MARKET_DATA.fetch_market_snapshot(("BTCUSDT", "ETHUSDT"), utc_now())
    assert result.data_status != "LIVE"

