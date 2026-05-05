"""Unit tests for placeholder signal engine behavior."""

from __future__ import annotations

from app.schemas import MarketSnapshot
from app.services.signal_engine import build_signal_snapshot


def test_signal_engine_long_case() -> None:
    """Return LONG when BTC 24h change is >= +1%."""

    snapshot = MarketSnapshot(btc_price=65000.0, btc_change_24h=1.2, eth_price=3200.0, eth_change_24h=0.4)
    signal = build_signal_snapshot(snapshot)
    assert signal.action == "LONG"
    assert signal.regime == "Trending"


def test_signal_engine_short_case() -> None:
    """Return SHORT when BTC 24h change is <= -1%."""

    snapshot = MarketSnapshot(btc_price=65000.0, btc_change_24h=-1.5, eth_price=3200.0, eth_change_24h=-0.7)
    signal = build_signal_snapshot(snapshot)
    assert signal.action == "SHORT"
    assert signal.regime == "Risk-Off"


def test_signal_engine_wait_case() -> None:
    """Return WAIT when BTC 24h change is between +/-1%."""

    snapshot = MarketSnapshot(btc_price=65000.0, btc_change_24h=0.2, eth_price=3200.0, eth_change_24h=0.1)
    signal = build_signal_snapshot(snapshot)
    assert signal.action == "WAIT"
    assert signal.regime == "Sideways"

