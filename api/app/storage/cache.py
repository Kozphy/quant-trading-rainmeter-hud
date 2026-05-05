"""In-memory last-known-good cache for market observability snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import Lock

from app.schemas import MarketSnapshot


@dataclass(frozen=True)
class CachedMarketState:
    """State stored after successful market fetch."""

    market: MarketSnapshot
    fetched_at: datetime


class LastKnownGoodCache:
    """Thread-safe in-memory cache for the most recent successful market snapshot."""

    def __init__(self) -> None:
        """Initialize an empty cache."""

        self._state: CachedMarketState | None = None
        self._lock = Lock()

    def update(self, market: MarketSnapshot, fetched_at: datetime) -> None:
        """Store the latest successful market snapshot.

        Args:
            market: Normalized market snapshot.
            fetched_at: UTC timestamp of successful fetch.
        """

        with self._lock:
            self._state = CachedMarketState(market=market, fetched_at=fetched_at)

    def get(self) -> CachedMarketState | None:
        """Return the cached snapshot if available.

        Returns:
            Cached state or None.
        """

        with self._lock:
            return self._state

