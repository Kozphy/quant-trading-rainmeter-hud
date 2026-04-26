"""Configuration helpers for the local Quant Trading HUD API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT")
SYMBOL_LABELS = {
    "BTCUSDT": "Bitcoin / USDT",
    "ETHUSDT": "Ethereum / USDT",
    "SOLUSDT": "Solana / USDT",
    "BNBUSDT": "BNB / USDT",
}


@dataclass(frozen=True)
class AppConfig:
    """Runtime settings for the local API."""

    symbols: tuple[str, ...]
    primary_symbol: str
    database_path: Path
    kline_interval: str
    kline_limit: int
    request_timeout_seconds: float
    history_limit_per_symbol: int


def normalize_symbol(symbol: str) -> str:
    """Normalize a market symbol for consistent lookup.

    Args:
        symbol: Raw symbol text supplied by config or query parameters.

    Returns:
        Uppercase symbol text with surrounding whitespace removed.
    """

    return symbol.strip().upper()


def parse_symbols(raw_symbols: str | None) -> tuple[str, ...]:
    """Parse a comma-separated symbol list.

    Args:
        raw_symbols: Optional comma-separated symbol string.

    Returns:
        A tuple of normalized symbols, falling back to the default symbols when
        no valid values are supplied.
    """

    if not raw_symbols:
        return DEFAULT_SYMBOLS

    symbols = tuple(
        symbol for symbol in (normalize_symbol(item) for item in raw_symbols.split(",")) if symbol
    )
    return symbols or DEFAULT_SYMBOLS


def get_int_env(name: str, default: int) -> int:
    """Read a positive integer environment variable.

    Args:
        name: Environment variable name.
        default: Value used when the variable is missing or invalid.

    Returns:
        A positive integer value.
    """

    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        parsed = int(raw_value)
    except ValueError:
        return default

    return parsed if parsed > 0 else default


def get_float_env(name: str, default: float) -> float:
    """Read a positive float environment variable.

    Args:
        name: Environment variable name.
        default: Value used when the variable is missing or invalid.

    Returns:
        A positive float value.
    """

    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        parsed = float(raw_value)
    except ValueError:
        return default

    return parsed if parsed > 0 else default


def load_config() -> AppConfig:
    """Load API configuration from environment variables.

    Returns:
        An AppConfig instance with normalized symbols and safe defaults.
    """

    symbols = parse_symbols(os.getenv("HUD_SYMBOLS"))
    primary_symbol = normalize_symbol(os.getenv("HUD_PRIMARY_SYMBOL", symbols[0]))
    if primary_symbol not in symbols:
        primary_symbol = symbols[0]

    api_dir = Path(__file__).resolve().parent
    database_path = Path(os.getenv("HUD_DATABASE_PATH", api_dir / "market_history.db"))

    return AppConfig(
        symbols=symbols,
        primary_symbol=primary_symbol,
        database_path=database_path,
        kline_interval=os.getenv("HUD_KLINE_INTERVAL", "1h"),
        kline_limit=max(60, get_int_env("HUD_KLINE_LIMIT", 120)),
        request_timeout_seconds=get_float_env("HUD_REQUEST_TIMEOUT_SECONDS", 6.0),
        history_limit_per_symbol=get_int_env("HUD_HISTORY_LIMIT_PER_SYMBOL", 500),
    )
