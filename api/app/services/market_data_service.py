"""Market data service that applies last-known-good fallback behavior."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.schemas import MarketSnapshot
from app.services.binance_client import BinanceClient, BinanceClientError
from app.storage.cache import LastKnownGoodCache


@dataclass(frozen=True)
class MarketFetchResult:
    """Result of one market fetch cycle."""

    market: MarketSnapshot
    data_status: Literal["LIVE", "STALE", "ERROR"]
    bot_status: Literal["RUNNING", "WARNING", "ERROR"]
    last_success_at: datetime | None
    staleness_seconds: int
    error: str | None = None


class MarketDataService:
    """Fetch and normalize market data with cache-backed stale fallback."""

    def __init__(self, binance_client: BinanceClient, cache: LastKnownGoodCache) -> None:
        """Initialize market data service.

        Args:
            binance_client: Public Binance adapter.
            cache: Last-known-good in-memory cache.
        """

        self.binance_client = binance_client
        self.cache = cache

    def fetch_market_snapshot(self, symbols: tuple[str, ...], now: datetime) -> MarketFetchResult:
        """Fetch latest market snapshot with stale fallback.

        Args:
            symbols: Symbols to fetch.
            now: Current UTC timestamp.

        Returns:
            Structured fetch result with status metadata.
        """

        try:
            tickers = self.binance_client.fetch_24h_tickers(symbols)
            market = MarketSnapshot(
                btc_price=tickers.get("BTCUSDT").last_price if tickers.get("BTCUSDT") else 0.0,
                btc_change_24h=tickers.get("BTCUSDT").price_change_percent if tickers.get("BTCUSDT") else 0.0,
                eth_price=tickers.get("ETHUSDT").last_price if tickers.get("ETHUSDT") else 0.0,
                eth_change_24h=tickers.get("ETHUSDT").price_change_percent if tickers.get("ETHUSDT") else 0.0,
            )
            self.cache.update(market, now)
            return MarketFetchResult(
                market=market,
                data_status="LIVE",
                bot_status="RUNNING",
                last_success_at=now,
                staleness_seconds=0,
            )
        except BinanceClientError as exc:
            cached = self.cache.get()
            if cached is not None:
                age = int((now - cached.fetched_at).total_seconds())
                return MarketFetchResult(
                    market=cached.market,
                    data_status="STALE",
                    bot_status="WARNING",
                    last_success_at=cached.fetched_at,
                    staleness_seconds=max(0, age),
                    error=str(exc),
                )
            return MarketFetchResult(
                market=MarketSnapshot(),
                data_status="ERROR",
                bot_status="ERROR",
                last_success_at=None,
                staleness_seconds=0,
                error=str(exc),
            )

