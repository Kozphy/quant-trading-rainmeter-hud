"""Binance public REST adapter with safe error handling."""

from __future__ import annotations

from dataclasses import dataclass

import httpx


class BinanceClientError(Exception):
    """Raised when Binance market data cannot be fetched or parsed."""


@dataclass(frozen=True)
class SymbolTicker:
    """Normalized symbol ticker output for internal service usage."""

    symbol: str
    last_price: float
    price_change_percent: float


class BinanceClient:
    """HTTP client wrapper for Binance public ticker endpoints."""

    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        """Create a Binance client.

        Args:
            base_url: Binance API base URL.
            timeout_seconds: HTTP timeout for requests.
        """

        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def fetch_24h_tickers(self, symbols: tuple[str, ...]) -> dict[str, SymbolTicker]:
        """Fetch 24h ticker values for requested symbols.

        Args:
            symbols: Symbols to fetch, such as BTCUSDT and ETHUSDT.

        Returns:
            Mapping of symbol to normalized ticker.

        Raises:
            BinanceClientError: If network, status, payload, or schema fails.
        """

        results: dict[str, SymbolTicker] = {}
        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout_seconds) as client:
                for symbol in symbols:
                    response = client.get("/api/v3/ticker/24hr", params={"symbol": symbol})
                    response.raise_for_status()
                    payload = response.json()
                    if not isinstance(payload, dict):
                        raise BinanceClientError(f"Invalid ticker payload for {symbol}.")
                    try:
                        results[symbol] = SymbolTicker(
                            symbol=symbol,
                            last_price=float(payload["lastPrice"]),
                            price_change_percent=float(payload["priceChangePercent"]),
                        )
                    except (KeyError, TypeError, ValueError) as exc:
                        raise BinanceClientError(f"Malformed ticker fields for {symbol}.") from exc
        except httpx.TimeoutException as exc:
            raise BinanceClientError("Binance request timed out.") from exc
        except httpx.HTTPError as exc:
            raise BinanceClientError("Binance request failed.") from exc
        except ValueError as exc:
            raise BinanceClientError("Binance returned invalid JSON.") from exc
        return results

