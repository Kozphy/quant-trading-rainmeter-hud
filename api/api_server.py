"""Local FastAPI server for the Quant Trading Rainmeter HUD.

The API is monitoring-only. It reads Binance public market data, calculates
educational indicators, stores local SQLite history, and never places trades.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from time import perf_counter
from typing import Any

from fastapi import FastAPI, HTTPException, Query

from calendar_data import get_calendar_payload
from config import SYMBOL_LABELS, AppConfig, load_config, normalize_symbol
from indicators import build_indicator_payload
from market_data import PriceHistory, fetch_market_histories
from risk import build_risk_payload
from storage import get_symbol_history, init_db, save_market_snapshots


CONFIG = load_config()
STORAGE_STARTUP_WARNING: str | None = None


def get_local_now() -> datetime:
    """Return the current local datetime.

    Returns:
        The current local datetime from the Windows host.
    """

    return datetime.now()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize local storage during FastAPI startup.

    Args:
        _: FastAPI application instance supplied by the framework.

    Yields:
        None while the application is running.
    """

    global STORAGE_STARTUP_WARNING

    try:
        init_db(CONFIG.database_path)
    except Exception as exc:
        STORAGE_STARTUP_WARNING = f"SQLite startup warning: {exc}"

    yield


app = FastAPI(
    title="Quant Trading Rainmeter HUD API",
    description="Local monitoring API powered by Binance public market data.",
    version="2.0.0",
    lifespan=lifespan,
)


def round_metric(value: float, digits: int = 2) -> float:
    """Round a numeric metric for stable HUD display.

    Args:
        value: Raw numeric value.
        digits: Number of decimal places to keep.

    Returns:
        Rounded numeric value.
    """

    return round(float(value), digits)


def get_bot_status(warnings: list[str], storage_warning: str | None = None) -> str:
    """Convert warning state into a HUD bot status.

    Args:
        warnings: Market-data warning messages.
        storage_warning: Optional SQLite warning message.

    Returns:
        RUNNING when no warnings exist, otherwise WARNING.
    """

    return "WARNING" if warnings or storage_warning else "RUNNING"


def build_symbol_snapshot(history: PriceHistory) -> dict[str, Any]:
    """Build one symbol's indicator and risk snapshot.

    Args:
        history: Recent close-price history for the symbol.

    Returns:
        Dictionary containing display-ready symbol metrics.
    """

    indicator_payload = build_indicator_payload(history.closes)
    risk_payload = build_risk_payload(history.closes)

    return {
        "symbol": history.symbol,
        "price": round_metric(float(indicator_payload["price"])),
        "price_change_percent": round_metric(float(indicator_payload["price_change_percent"])),
        "rsi": round_metric(float(indicator_payload["rsi"])),
        "sma20": round_metric(float(indicator_payload["sma20"])),
        "sma50": round_metric(float(indicator_payload["sma50"])),
        "signal": str(indicator_payload["signal"]),
        "confidence": round_metric(float(indicator_payload["confidence"]), 4),
        "regime": str(indicator_payload["regime"]),
        "volatility": round_metric(risk_payload["volatility"]),
        "drawdown": round_metric(risk_payload["drawdown"]),
        "sharpe": round_metric(risk_payload["sharpe"]),
        "exposure": round_metric(risk_payload["exposure"]),
        "source": history.source,
    }


def validate_symbol(symbol: str, config: AppConfig = CONFIG) -> str:
    """Validate that a symbol is configured for the API.

    Args:
        symbol: Symbol to validate.
        config: Runtime configuration containing supported symbols.

    Returns:
        Normalized symbol when it is configured.

    Raises:
        HTTPException: If the symbol is not configured.
    """

    normalized = normalize_symbol(symbol)
    if normalized not in config.symbols:
        raise HTTPException(status_code=400, detail=f"Unsupported symbol: {normalized}")
    return normalized


def build_flat_data_response(
    selected: dict[str, Any],
    snapshots_by_symbol: dict[str, dict[str, Any]],
    bot_status: str,
    latency_ms: int,
    now: datetime,
    warnings: list[str],
) -> dict[str, Any]:
    """Build the Rainmeter-friendly /data response.

    Args:
        selected: Snapshot for the selected symbol.
        snapshots_by_symbol: Snapshot mapping for all configured symbols.
        bot_status: Overall status value.
        latency_ms: Request latency in milliseconds.
        now: Current local datetime.
        warnings: Warning messages from data and storage layers.

    Returns:
        A dictionary with stable top-level fields plus nested symbol details.
    """

    return {
        "selected_symbol": selected["symbol"],
        "btc_price": snapshots_by_symbol.get("BTCUSDT", {}).get("price", 0.0),
        "eth_price": snapshots_by_symbol.get("ETHUSDT", {}).get("price", 0.0),
        "sol_price": snapshots_by_symbol.get("SOLUSDT", {}).get("price", 0.0),
        "bnb_price": snapshots_by_symbol.get("BNBUSDT", {}).get("price", 0.0),
        "price": selected["price"],
        "price_change_percent": selected["price_change_percent"],
        "signal": selected["signal"],
        "confidence": selected["confidence"],
        "regime": selected["regime"],
        "rsi": selected["rsi"],
        "sma20": selected["sma20"],
        "sma50": selected["sma50"],
        "volatility": selected["volatility"],
        "drawdown": selected["drawdown"],
        "sharpe": selected["sharpe"],
        "exposure": selected["exposure"],
        "bot_status": bot_status,
        "latency_ms": latency_ms,
        "date": now.strftime("%Y-%m-%d"),
        "day": now.strftime("%A"),
        "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "symbols": snapshots_by_symbol,
        "warnings": warnings,
    }


def build_data_response(selected_symbol: str | None = None, config: AppConfig = CONFIG) -> dict[str, Any]:
    """Build the full market, indicator, risk, and history response.

    Args:
        selected_symbol: Optional symbol to promote to top-level HUD fields.
        config: Runtime configuration.

    Returns:
        Dictionary for the /data endpoint.
    """

    started_at = perf_counter()
    now = get_local_now()
    selected = validate_symbol(selected_symbol or config.primary_symbol, config)
    histories, warnings = fetch_market_histories(config)
    if STORAGE_STARTUP_WARNING:
        warnings.append(STORAGE_STARTUP_WARNING)

    snapshots = [build_symbol_snapshot(histories[symbol]) for symbol in config.symbols]
    snapshots_by_symbol = {snapshot["symbol"]: snapshot for snapshot in snapshots}

    storage_warning: str | None = None
    bot_status = get_bot_status(warnings)
    try:
        save_market_snapshots(
            config.database_path,
            snapshots,
            bot_status,
            now.strftime("%Y-%m-%d %H:%M:%S"),
            config.history_limit_per_symbol,
        )
    except Exception as exc:
        storage_warning = f"SQLite storage warning: {exc}"

    if storage_warning:
        warnings.append(storage_warning)
        bot_status = get_bot_status(warnings, storage_warning)

    latency_ms = int((perf_counter() - started_at) * 1000)
    return build_flat_data_response(snapshots_by_symbol[selected], snapshots_by_symbol, bot_status, latency_ms, now, warnings)


def build_symbols_response(config: AppConfig = CONFIG) -> dict[str, Any]:
    """Build configured symbol metadata.

    Args:
        config: Runtime configuration.

    Returns:
        Dictionary containing primary symbol and supported symbol metadata.
    """

    return {
        "primary_symbol": config.primary_symbol,
        "symbols": [
            {
                "symbol": symbol,
                "label": SYMBOL_LABELS.get(symbol, symbol),
                "selected": symbol == config.primary_symbol,
            }
            for symbol in config.symbols
        ],
    }


@app.get("/")
def root() -> dict[str, Any]:
    """Return the same payload as /health for beginner-friendly testing.

    Returns:
        Health payload for the local API.
    """

    return get_health()


@app.get("/health")
def get_health() -> dict[str, Any]:
    """Return local API health without calling Binance.

    Returns:
        Dictionary showing local service status and configured symbols.
    """

    return {
        "status": "ok",
        "service": "quant-trading-rainmeter-hud",
        "mode": "monitoring-only",
        "symbols": list(CONFIG.symbols),
        "database": str(CONFIG.database_path),
        "storage_status": "warning" if STORAGE_STARTUP_WARNING else "ok",
        "storage_warning": STORAGE_STARTUP_WARNING,
    }


@app.get("/data")
def get_data(symbol: str | None = Query(default=None, description="Optional selected symbol, such as BTCUSDT.")) -> dict[str, Any]:
    """Return market data, indicators, risk metrics, and symbol snapshots.

    Args:
        symbol: Optional configured symbol to promote to top-level HUD fields.

    Returns:
        Dictionary containing Rainmeter-friendly top-level fields and nested
        per-symbol data.
    """

    return build_data_response(symbol)


@app.get("/symbols")
def get_symbols() -> dict[str, Any]:
    """Return configured symbol metadata.

    Returns:
        Dictionary containing supported symbols and the primary selected symbol.
    """

    return build_symbols_response()


@app.get("/calendar")
def get_calendar() -> dict[str, str | list[dict[str, str]]]:
    """Return the static trading operations calendar.

    Returns:
        Dictionary containing today's date and the static task list.
    """

    return get_calendar_payload(get_local_now())


@app.get("/history")
def get_history(
    symbol: str = Query(default="BTCUSDT", description="Configured symbol to load history for."),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of rows to return."),
) -> dict[str, Any]:
    """Return recent SQLite snapshot history for one symbol.

    Args:
        symbol: Configured symbol to query.
        limit: Maximum number of rows to return.

    Returns:
        Dictionary containing symbol and recent history rows.
    """

    normalized = validate_symbol(symbol)
    try:
        rows = get_symbol_history(CONFIG.database_path, normalized, limit)
    except Exception as exc:
        return {"symbol": normalized, "count": 0, "history": [], "warning": f"SQLite history warning: {exc}"}

    return {"symbol": normalized, "count": len(rows), "history": rows}
