"""Monitoring-safe risk calculations without account exposure assumptions."""

from __future__ import annotations

import statistics
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.schemas import MarketSnapshot, RiskSnapshot, SignalSnapshot


@dataclass(frozen=True)
class SignalEvent:
    """Signal action event for flip counting."""

    action: str
    timestamp: datetime


class SignalFlipTracker:
    """Track signal transitions over a rolling one-hour window."""

    def __init__(self) -> None:
        """Initialize an empty signal event queue."""

        self._events: deque[SignalEvent] = deque()

    def record(self, action: str, now: datetime) -> None:
        """Record a signal action and evict old samples.

        Args:
            action: Signal action string.
            now: Current UTC timestamp.
        """

        self._events.append(SignalEvent(action=action, timestamp=now))
        self._evict_old(now)

    def flips_last_hour(self, now: datetime) -> int:
        """Calculate action flips in the last hour.

        Args:
            now: Current UTC timestamp.

        Returns:
            Number of action transitions.
        """

        self._evict_old(now)
        flips = 0
        previous: str | None = None
        for event in self._events:
            if previous is not None and previous != event.action:
                flips += 1
            previous = event.action
        return flips

    def _evict_old(self, now: datetime) -> None:
        """Drop events older than one hour.

        Args:
            now: Current UTC timestamp.
        """

        cutoff = now - timedelta(hours=1)
        while self._events and self._events[0].timestamp < cutoff:
            self._events.popleft()


def _realized_volatility_from_changes(change_percent: float) -> float:
    """Estimate 24h realized volatility from latest daily change.

    Args:
        change_percent: 24h percentage change.

    Returns:
        Monitoring placeholder volatility percent.
    """

    return round(abs(change_percent), 4)


def _drawdown_from_recent_high(price: float, recent_high: float) -> float:
    """Compute drawdown percent from recent high.

    Args:
        price: Current price.
        recent_high: Recent high watermark.

    Returns:
        Non-positive drawdown percentage.
    """

    if recent_high <= 0:
        return 0.0
    return round(((price - recent_high) / recent_high) * 100.0, 4)


def build_risk_snapshot(
    market: MarketSnapshot,
    signal: SignalSnapshot,
    staleness_seconds: int,
    flip_tracker: SignalFlipTracker,
    now: datetime,
) -> RiskSnapshot:
    """Build monitoring-safe risk metrics for HUD.

    Args:
        market: Market snapshot values.
        signal: Current signal decision.
        staleness_seconds: Current data age in seconds.
        flip_tracker: Signal flip tracker state.
        now: Current UTC timestamp.

    Returns:
        Risk snapshot metrics.
    """

    flip_tracker.record(signal.action, now)
    recent_high = max(market.btc_price, market.eth_price, 0.0)
    volatility = statistics.mean(
        [
            _realized_volatility_from_changes(market.btc_change_24h),
            _realized_volatility_from_changes(market.eth_change_24h),
        ]
    )
    return RiskSnapshot(
        realized_volatility_24h=round(volatility, 4),
        price_drawdown_from_recent_high=_drawdown_from_recent_high(market.btc_price, recent_high),
        signal_flip_count_1h=flip_tracker.flips_last_hour(now),
        data_staleness_seconds=max(0, staleness_seconds),
    )

