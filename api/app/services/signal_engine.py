"""Placeholder monitoring signal engine."""

from __future__ import annotations

from app.schemas import MarketSnapshot, SignalSnapshot


def build_signal_snapshot(market: MarketSnapshot) -> SignalSnapshot:
    """Generate placeholder signal output from market snapshot.

    Args:
        market: Market snapshot with BTC/ETH fields.

    Returns:
        Signal snapshot for monitoring-only display.
    """

    change = market.btc_change_24h
    if change >= 1.0:
        return SignalSnapshot(
            action="LONG",
            confidence=0.72,
            regime="Trending",
            reason="BTC 24h change is greater than or equal to +1%.",
            rules_triggered=["btc_change_24h >= 1.0"],
        )
    if change <= -1.0:
        return SignalSnapshot(
            action="SHORT",
            confidence=0.68,
            regime="Risk-Off",
            reason="BTC 24h change is less than or equal to -1%.",
            rules_triggered=["btc_change_24h <= -1.0"],
        )
    return SignalSnapshot(
        action="WAIT",
        confidence=0.51,
        regime="Sideways",
        reason="BTC 24h change is between -1% and +1%.",
        rules_triggered=["-1.0 < btc_change_24h < 1.0"],
    )

