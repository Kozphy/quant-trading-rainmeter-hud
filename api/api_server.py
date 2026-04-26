"""Local FastAPI server for the Quant Trading Rainmeter HUD.

This service only reads Binance public market data. It does not place orders,
manage accounts, or require exchange API keys.
"""

from __future__ import annotations

from datetime import datetime
from time import perf_counter
from typing import Any

import httpx
from fastapi import FastAPI


BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"
BINANCE_TIMEOUT_SECONDS = 5.0
SYMBOLS = ("BTCUSDT", "ETHUSDT")

FALLBACK_QUOTES = {
    "BTCUSDT": {"price": 0.0, "change": 0.0},
    "ETHUSDT": {"price": 0.0, "change": 0.0},
}

CALENDAR_TASKS = [
    {"time": "09:00", "name": "Risk Review"},
    {"time": "14:30", "name": "Backtest Batch"},
    {"time": "20:30", "name": "US Macro Watch"},
    {"time": "23:00", "name": "Execution Log Audit"},
]

app = FastAPI(
    title="Quant Trading Rainmeter HUD API",
    description="Local monitoring API powered by Binance public market data.",
    version="1.0.0",
)


class MarketDataError(Exception):
    """Raised when public market data cannot be loaded or parsed."""


def get_local_now() -> datetime:
    """Return the current local datetime.

    Returns:
        The current local datetime from the Windows host.
    """

    return datetime.now()


def parse_ticker_payload(payload: dict[str, Any], symbol: str) -> dict[str, float]:
    """Parse Binance ticker JSON into the HUD quote format.

    Args:
        payload: JSON object returned by the Binance 24 hour ticker endpoint.
        symbol: Market symbol being parsed, such as BTCUSDT.

    Returns:
        A dictionary with numeric price and 24 hour percentage change fields.

    Raises:
        MarketDataError: If required fields are missing or not numeric.
    """

    try:
        price = float(payload["lastPrice"])
        change = float(payload["priceChangePercent"])
    except (KeyError, TypeError, ValueError) as exc:
        raise MarketDataError(f"Invalid Binance payload for {symbol}.") from exc

    return {"price": round(price, 2), "change": round(change, 2)}


def fetch_symbol_quote(client: httpx.Client, symbol: str) -> dict[str, float]:
    """Fetch one public Binance ticker quote.

    Args:
        client: Configured HTTP client used for the Binance request.
        symbol: Binance market symbol, such as BTCUSDT or ETHUSDT.

    Returns:
        A dictionary with numeric price and 24 hour percentage change fields.

    Raises:
        MarketDataError: If Binance is unreachable, returns a bad status, or
            sends data that cannot be parsed.
    """

    try:
        response = client.get(BINANCE_TICKER_URL, params={"symbol": symbol})
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise MarketDataError(f"Binance request failed for {symbol}.") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise MarketDataError(f"Binance returned invalid JSON for {symbol}.") from exc

    return parse_ticker_payload(payload, symbol)


def fetch_market_quotes() -> tuple[dict[str, dict[str, float]], list[str]]:
    """Fetch BTCUSDT and ETHUSDT quotes from Binance public REST.

    Returns:
        A tuple containing a quote dictionary and a list of warning messages.
        Symbols that fail are replaced with numeric fallback values.
    """

    quotes: dict[str, dict[str, float]] = {}
    warnings: list[str] = []

    with httpx.Client(timeout=BINANCE_TIMEOUT_SECONDS) as client:
        for symbol in SYMBOLS:
            try:
                quotes[symbol] = fetch_symbol_quote(client, symbol)
            except MarketDataError as exc:
                quotes[symbol] = FALLBACK_QUOTES[symbol].copy()
                warnings.append(str(exc))

    return quotes, warnings


def build_signal(btc_change: float) -> dict[str, float | str]:
    """Build a simple placeholder signal from BTC 24 hour change.

    Args:
        btc_change: BTCUSDT 24 hour percentage change from Binance.

    Returns:
        A dictionary containing signal, confidence, and market regime values.
    """

    # Placeholder only: this is not a trading strategy and must be replaced by
    # a tested strategy engine before anyone uses it for real decision support.
    if btc_change >= 1.0:
        return {"signal": "LONG", "confidence": 0.72, "regime": "Trending"}
    if btc_change <= -1.0:
        return {"signal": "SHORT", "confidence": 0.68, "regime": "Risk-Off"}
    return {"signal": "WAIT", "confidence": 0.51, "regime": "Sideways"}


def build_placeholder_risk_metrics(signal: str) -> dict[str, float]:
    """Build non-trading placeholder risk metrics for the HUD.

    Args:
        signal: Placeholder signal name returned by build_signal.

    Returns:
        A dictionary with exposure percentage, drawdown percentage, and Sharpe
        ratio values for display only.
    """

    if signal == "LONG":
        return {"exposure": 35.0, "drawdown": -1.8, "sharpe": 1.21}
    if signal == "SHORT":
        return {"exposure": 25.0, "drawdown": -2.2, "sharpe": 0.98}
    return {"exposure": 0.0, "drawdown": 0.0, "sharpe": 0.0}


def build_data_response() -> dict[str, float | int | str]:
    """Build the full JSON payload for the Rainmeter HUD.

    Returns:
        A dictionary matching the /data endpoint schema requested by the
        project brief.
    """

    started_at = perf_counter()
    now = get_local_now()

    try:
        quotes, warnings = fetch_market_quotes()
        bot_status = "WARNING" if warnings else "RUNNING"
    except Exception:
        quotes = {symbol: FALLBACK_QUOTES[symbol].copy() for symbol in SYMBOLS}
        bot_status = "ERROR"

    btc_quote = quotes["BTCUSDT"]
    eth_quote = quotes["ETHUSDT"]
    signal_data = build_signal(btc_quote["change"])
    risk_metrics = build_placeholder_risk_metrics(str(signal_data["signal"]))
    latency_ms = int((perf_counter() - started_at) * 1000)

    return {
        "btc_price": btc_quote["price"],
        "btc_change": btc_quote["change"],
        "eth_price": eth_quote["price"],
        "eth_change": eth_quote["change"],
        "signal": signal_data["signal"],
        "confidence": signal_data["confidence"],
        "regime": signal_data["regime"],
        "bot_status": bot_status,
        "latency_ms": latency_ms,
        "exposure": risk_metrics["exposure"],
        "drawdown": risk_metrics["drawdown"],
        "sharpe": risk_metrics["sharpe"],
        "date": now.strftime("%Y-%m-%d"),
        "day": now.strftime("%A"),
        "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
    }


@app.get("/")
def health_check() -> dict[str, str]:
    """Return a simple health check response.

    Returns:
        A dictionary showing that the local API is running.
    """

    return {"status": "ok", "service": "quant-trading-rainmeter-hud"}


@app.get("/data")
def get_data() -> dict[str, float | int | str]:
    """Return the latest market and monitoring data for Rainmeter.

    Returns:
        A dictionary containing prices, placeholder signal values, placeholder
        risk metrics, and local timestamps.
    """

    return build_data_response()


@app.get("/calendar")
def get_calendar() -> dict[str, str | list[dict[str, str]]]:
    """Return the static trading operations calendar.

    Returns:
        A dictionary containing today's date and the static task list.
    """

    return {"date": get_local_now().strftime("%Y-%m-%d"), "tasks": CALENDAR_TASKS}
