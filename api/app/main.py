"""FastAPI application for local-first market observability."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from fastapi import FastAPI

from app.config import AppConfig, load_config
from app.schemas import CalendarResponse, CalendarTask, HUDDataResponse, SystemStatus
from app.services.binance_client import BinanceClient
from app.services.health_service import is_ready
from app.services.market_data_service import MarketDataService
from app.services.risk_engine import SignalFlipTracker, build_risk_snapshot
from app.services.signal_engine import build_signal_snapshot
from app.storage.cache import LastKnownGoodCache
from app.storage.jsonl_logger import JsonlLogger
from app.utils.time_utils import to_iso8601, utc_now


@dataclass
class ApiMetrics:
    """In-memory metrics for observability endpoints."""

    request_count: int = 0
    binance_error_count: int = 0
    last_success_at: str | None = None
    last_latency_ms: int = 0
    last_data_age_seconds: int = 0


CONFIG: AppConfig = load_config()
CACHE = LastKnownGoodCache()
FLIP_TRACKER = SignalFlipTracker()
MARKET_DATA = MarketDataService(
    binance_client=BinanceClient(CONFIG.binance_base_url, CONFIG.request_timeout_seconds),
    cache=CACHE,
)
METRICS = ApiMetrics()
MARKET_LOG = JsonlLogger(CONFIG.logs_dir / "market_snapshots.jsonl")
SIGNAL_LOG = JsonlLogger(CONFIG.logs_dir / "signal_decisions.jsonl")
EVENT_LOG = JsonlLogger(CONFIG.logs_dir / "system_events.jsonl")

CALENDAR_TASKS = [
    CalendarTask(time="09:00", name="Risk Review"),
    CalendarTask(time="14:30", name="Backtest Batch"),
    CalendarTask(time="20:30", name="US Macro Watch"),
    CalendarTask(time="23:00", name="Execution Log Audit"),
]

app = FastAPI(
    title="Quant Trading Rainmeter HUD API",
    description="Monitoring-only API for local market observability.",
    version="3.0.0",
)


def _build_data_response() -> HUDDataResponse:
    """Build full /data contract from live or cached market state.

    Returns:
        Typed HUD data response.
    """

    started = perf_counter()
    now = utc_now()
    result = MARKET_DATA.fetch_market_snapshot(CONFIG.market_symbols, now)
    signal = build_signal_snapshot(result.market)
    risk = build_risk_snapshot(result.market, signal, result.staleness_seconds, FLIP_TRACKER, now)
    latency_ms = int((perf_counter() - started) * 1000)

    METRICS.request_count += 1
    METRICS.last_latency_ms = latency_ms
    METRICS.last_data_age_seconds = result.staleness_seconds
    if result.last_success_at is not None:
        METRICS.last_success_at = to_iso8601(result.last_success_at)
    if result.error:
        METRICS.binance_error_count += 1

    response = HUDDataResponse(
        market=result.market,
        signal=signal,
        risk=risk,
        system=SystemStatus(
            bot_status=result.bot_status,
            data_status=result.data_status,
            latency_ms=latency_ms,
            last_success_at=to_iso8601(result.last_success_at) if result.last_success_at else None,
            updated_at=to_iso8601(now),
        ),
    )

    MARKET_LOG.append(
        {
            "timestamp": to_iso8601(now),
            "data_status": response.system.data_status,
            "btc_price": response.market.btc_price,
            "btc_change_24h": response.market.btc_change_24h,
            "eth_price": response.market.eth_price,
            "eth_change_24h": response.market.eth_change_24h,
        }
    )
    SIGNAL_LOG.append(
        {
            "timestamp": to_iso8601(now),
            "input_features": {
                "btc_change_24h": response.market.btc_change_24h,
                "eth_change_24h": response.market.eth_change_24h,
            },
            "decision": response.signal.action,
            "confidence": response.signal.confidence,
            "regime": response.signal.regime,
            "reason": response.signal.reason,
            "rules_triggered": response.signal.rules_triggered,
        }
    )
    if result.error:
        EVENT_LOG.append(
            {
                "timestamp": to_iso8601(now),
                "event": "binance_fetch_failed",
                "message": result.error,
                "data_status": response.system.data_status,
            }
        )
    return response


@app.get("/")
def get_root() -> dict[str, str]:
    """Return basic process liveness details.

    Returns:
        Root endpoint response.
    """

    return {"service": "quant-trading-rainmeter-hud", "status": "ok", "mode": "monitoring-only"}


@app.get("/health")
def get_health() -> dict[str, str]:
    """Return process health without external dependencies.

    Returns:
        Health endpoint payload.
    """

    return {"status": "ok", "mode": "monitoring-only"}


@app.get("/ready")
def get_ready() -> dict[str, str | bool]:
    """Return readiness based on market-data freshness.

    Returns:
        Readiness status payload.
    """

    payload = _build_data_response()
    ready = is_ready(payload.system.data_status, payload.risk.data_staleness_seconds, CONFIG.stale_after_seconds)
    return {"ready": ready, "data_status": payload.system.data_status, "bot_status": payload.system.bot_status}


@app.get("/data", response_model=HUDDataResponse)
def get_data() -> HUDDataResponse:
    """Return typed HUD data contract.

    Returns:
        Full HUD data response.
    """

    return _build_data_response()


@app.get("/calendar", response_model=CalendarResponse)
def get_calendar() -> CalendarResponse:
    """Return static daily operations calendar.

    Returns:
        Calendar response.
    """

    return CalendarResponse(date=utc_now().date().isoformat(), tasks=CALENDAR_TASKS)


@app.get("/metrics")
def get_metrics() -> dict[str, int | str | None]:
    """Return basic system and data quality metrics.

    Returns:
        Metrics response payload.
    """

    return {
        "request_count": METRICS.request_count,
        "binance_error_count": METRICS.binance_error_count,
        "last_success_at": METRICS.last_success_at,
        "last_latency_ms": METRICS.last_latency_ms,
        "data_age_seconds": METRICS.last_data_age_seconds,
    }

