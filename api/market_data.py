"""Public Binance market data layer with safe fallback history."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import httpx

from config import AppConfig


BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
FALLBACK_BASE_PRICES = {
    "BTCUSDT": 65000.0,
    "ETHUSDT": 3200.0,
    "SOLUSDT": 145.0,
    "BNBUSDT": 590.0,
}


class MarketDataError(Exception):
    """Raised when public market data cannot be loaded or parsed."""


@dataclass(frozen=True)
class PriceHistory:
    """Recent close-price history for one symbol."""

    symbol: str
    closes: list[float]
    source: str
    warning: str | None = None


def parse_kline_closes(payload: Any, symbol: str) -> list[float]:
    """Parse Binance kline JSON into close prices.

    Args:
        payload: JSON payload from the Binance klines endpoint.
        symbol: Market symbol being parsed.

    Returns:
        Ordered close prices from oldest to newest.

    Raises:
        MarketDataError: If the payload shape is invalid or lacks prices.
    """

    if not isinstance(payload, list):
        raise MarketDataError(f"Invalid Binance kline payload for {symbol}.")

    closes: list[float] = []
    for row in payload:
        try:
            closes.append(float(row[4]))
        except (IndexError, TypeError, ValueError) as exc:
            raise MarketDataError(f"Invalid kline close value for {symbol}.") from exc

    if len(closes) < 50:
        raise MarketDataError(f"Not enough Binance history for {symbol}.")

    return closes


def fetch_symbol_history(client: httpx.Client, symbol: str, config: AppConfig) -> PriceHistory:
    """Fetch public Binance kline history for one symbol.

    Args:
        client: Configured HTTP client.
        symbol: Binance public market symbol.
        config: Runtime configuration.

    Returns:
        PriceHistory loaded from Binance public REST.

    Raises:
        MarketDataError: If the request fails or data cannot be parsed.
    """

    try:
        response = client.get(
            BINANCE_KLINES_URL,
            params={"symbol": symbol, "interval": config.kline_interval, "limit": config.kline_limit},
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise MarketDataError(f"Binance request failed for {symbol}.") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise MarketDataError(f"Binance returned invalid JSON for {symbol}.") from exc

    return PriceHistory(symbol=symbol, closes=parse_kline_closes(payload, symbol), source="binance")


def build_fallback_history(symbol: str, limit: int) -> PriceHistory:
    """Build deterministic fallback history for offline demos.

    Args:
        symbol: Market symbol that needs fallback values.
        limit: Number of close prices to generate.

    Returns:
        PriceHistory with simulated public-demo values and a warning message.
    """

    base_price = FALLBACK_BASE_PRICES.get(symbol, 100.0)
    safe_limit = max(60, limit)
    closes: list[float] = []

    for index in range(safe_limit):
        drift = (index - safe_limit) / safe_limit * 0.012
        wave = math.sin(index / 4.0) * 0.008
        closes.append(round(base_price * (1.0 + drift + wave), 4))

    return PriceHistory(
        symbol=symbol,
        closes=closes,
        source="fallback",
        warning=f"Using fallback history for {symbol}; Binance public data was unavailable.",
    )


def fetch_market_histories(config: AppConfig) -> tuple[dict[str, PriceHistory], list[str]]:
    """Fetch market history for all configured symbols.

    Args:
        config: Runtime configuration containing symbols and request settings.

    Returns:
        A tuple of symbol-to-history mapping and warning messages. Any failed
        symbol is replaced with deterministic fallback history.
    """

    histories: dict[str, PriceHistory] = {}
    warnings: list[str] = []

    with httpx.Client(timeout=config.request_timeout_seconds) as client:
        for symbol in config.symbols:
            try:
                histories[symbol] = fetch_symbol_history(client, symbol, config)
            except MarketDataError as exc:
                fallback = build_fallback_history(symbol, config.kline_limit)
                histories[symbol] = fallback
                warnings.append(f"{exc} {fallback.warning}")

    return histories, warnings
