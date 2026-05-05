"""Runtime configuration for the FastAPI market observability service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _positive_float(name: str, default: float) -> float:
    """Read a positive float from environment variables.

    Args:
        name: Environment variable name.
        default: Fallback value when missing or invalid.

    Returns:
        Positive float value.
    """

    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _positive_int(name: str, default: int) -> int:
    """Read a positive integer from environment variables.

    Args:
        name: Environment variable name.
        default: Fallback value when missing or invalid.

    Returns:
        Positive integer value.
    """

    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _parse_symbols(raw: str | None) -> tuple[str, ...]:
    """Parse and normalize comma-separated market symbols.

    Args:
        raw: Raw symbols environment variable.

    Returns:
        Normalized symbol tuple.
    """

    if not raw:
        return ("BTCUSDT", "ETHUSDT")
    parsed = tuple(symbol.strip().upper() for symbol in raw.split(",") if symbol.strip())
    return parsed or ("BTCUSDT", "ETHUSDT")


@dataclass(frozen=True)
class AppConfig:
    """Application settings loaded from environment variables."""

    app_host: str
    app_port: int
    binance_base_url: str
    market_symbols: tuple[str, ...]
    request_timeout_seconds: float
    stale_after_seconds: int
    log_level: str
    logs_dir: Path


def load_config() -> AppConfig:
    """Load application configuration with safe defaults.

    Returns:
        Parsed immutable configuration object.
    """

    api_dir = Path(__file__).resolve().parents[1]
    repo_root = api_dir.parent
    logs_dir = repo_root / "logs"
    return AppConfig(
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=_positive_int("APP_PORT", 8000),
        binance_base_url=os.getenv("BINANCE_BASE_URL", "https://api.binance.com").rstrip("/"),
        market_symbols=_parse_symbols(os.getenv("MARKET_SYMBOLS", "BTCUSDT,ETHUSDT")),
        request_timeout_seconds=_positive_float("REQUEST_TIMEOUT_SECONDS", 5.0),
        stale_after_seconds=_positive_int("STALE_AFTER_SECONDS", 60),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        logs_dir=logs_dir,
    )

