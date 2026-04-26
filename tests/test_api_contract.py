"""Contract tests for the Quant Trading Rainmeter HUD backend."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
API_DIR = REPO_ROOT / "api"
RAINMETER_INI = REPO_ROOT / "rainmeter" / "QuantTradingHUD" / "QuantTradingHUD.ini"
TEST_RUNTIME_DIR = REPO_ROOT / ".test-runtime"

if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

import api_server  # noqa: E402
from config import AppConfig  # noqa: E402
from market_data import PriceHistory  # noqa: E402
from storage import get_symbol_history  # noqa: E402


def build_test_config(database_name: str) -> AppConfig:
    """Build isolated runtime config for tests.

    Args:
        database_name: SQLite file name to create under the test runtime folder.

    Returns:
        AppConfig with an isolated SQLite database.
    """

    TEST_RUNTIME_DIR.mkdir(exist_ok=True)
    database_path = TEST_RUNTIME_DIR / database_name
    if database_path.exists():
        database_path.unlink()

    return AppConfig(
        symbols=("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"),
        primary_symbol="BTCUSDT",
        database_path=database_path,
        kline_interval="1h",
        kline_limit=80,
        request_timeout_seconds=1.0,
        history_limit_per_symbol=20,
    )


def build_price_series(base_price: float, count: int = 80) -> list[float]:
    """Build deterministic close prices for test indicators.

    Args:
        base_price: Starting price level.
        count: Number of close prices to generate.

    Returns:
        Ordered close prices from oldest to newest.
    """

    prices: list[float] = []
    for index in range(count):
        cycle = (index % 6) - 2
        prices.append(round(base_price + (index * 1.5) + cycle, 4))
    return prices


def fake_market_histories(config: AppConfig) -> tuple[dict[str, PriceHistory], list[str]]:
    """Return deterministic market history without network access.

    Args:
        config: Runtime configuration requested by the API layer.

    Returns:
        Symbol-to-history mapping and no warnings.
    """

    bases = {
        "BTCUSDT": 65000.0,
        "ETHUSDT": 3200.0,
        "SOLUSDT": 145.0,
        "BNBUSDT": 590.0,
    }
    histories = {
        symbol: PriceHistory(symbol=symbol, closes=build_price_series(bases[symbol]), source="test")
        for symbol in config.symbols
    }
    return histories, []


def extract_rainmeter_regex(section_name: str) -> str:
    """Extract a WebParser regular expression from the Rainmeter skin.

    Args:
        section_name: Rainmeter section name, without square brackets.

    Returns:
        Regular expression string with Rainmeter flags removed.
    """

    current_section = ""
    for raw_line in RAINMETER_INI.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("[") and line.endswith("]"):
            current_section = line.strip("[]")
            continue
        if current_section == section_name and line.startswith("RegExp="):
            return line.removeprefix("RegExp=").removeprefix("(?siU)")

    raise AssertionError(f"Missing RegExp for section {section_name}")


def test_static_api_endpoints_return_expected_contract(monkeypatch) -> None:
    """Verify static endpoints do not need Binance network access.

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        None.
    """

    monkeypatch.setattr(api_server, "CONFIG", build_test_config("static_endpoints.db"))

    with TestClient(api_server.app) as client:
        health = client.get("/health")
        symbols = client.get("/symbols")
        calendar = client.get("/calendar")

    assert health.status_code == 200
    assert health.json()["mode"] == "monitoring-only"
    assert symbols.status_code == 200
    assert [item["symbol"] for item in symbols.json()["symbols"]] == [
        "BTCUSDT",
        "ETHUSDT",
        "SOLUSDT",
        "BNBUSDT",
    ]
    assert calendar.status_code == 200
    assert len(calendar.json()["tasks"]) == 4


def test_data_response_calculates_indicators_and_writes_history(monkeypatch) -> None:
    """Verify /data service logic calculates metrics and persists history.

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        None.
    """

    config = build_test_config("data_response.db")
    monkeypatch.setattr(api_server, "fetch_market_histories", fake_market_histories)

    payload = api_server.build_data_response(config=config)

    assert payload["selected_symbol"] == "BTCUSDT"
    assert payload["btc_price"] > 0
    assert payload["eth_price"] > 0
    assert payload["signal"] in {"LONG", "SHORT", "WAIT"}
    assert payload["bot_status"] == "RUNNING"
    assert 0 <= payload["rsi"] <= 100
    assert payload["sma20"] > 0
    assert payload["sma50"] > 0
    assert payload["exposure"] == 0.0
    assert set(payload["symbols"].keys()) == set(config.symbols)

    history = get_symbol_history(config.database_path, "BTCUSDT", 5)
    assert len(history) == 1
    assert history[0]["symbol"] == "BTCUSDT"


def test_selected_symbol_can_change_without_trading(monkeypatch) -> None:
    """Verify selected symbol query behavior remains monitoring-only.

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        None.
    """

    config = build_test_config("selected_symbol.db")
    monkeypatch.setattr(api_server, "fetch_market_histories", fake_market_histories)

    payload = api_server.build_data_response(selected_symbol="SOLUSDT", config=config)

    assert payload["selected_symbol"] == "SOLUSDT"
    assert payload["price"] == payload["symbols"]["SOLUSDT"]["price"]
    assert payload["exposure"] == 0.0


def test_rainmeter_regex_matches_api_payload(monkeypatch) -> None:
    """Verify Rainmeter WebParser regex still matches API JSON fields.

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        None.
    """

    config = build_test_config("rainmeter_contract.db")
    monkeypatch.setattr(api_server, "fetch_market_histories", fake_market_histories)
    payload = api_server.build_data_response(config=config)
    calendar = api_server.get_calendar()
    compact_data = json.dumps(payload, separators=(",", ":"))
    compact_calendar = json.dumps(calendar, separators=(",", ":"))

    assert re.search(extract_rainmeter_regex("MeasureData"), compact_data, re.IGNORECASE | re.DOTALL)
    assert re.search(extract_rainmeter_regex("MeasureCalendar"), compact_calendar, re.IGNORECASE | re.DOTALL)


def test_backend_does_not_include_private_trading_calls() -> None:
    """Verify backend source avoids private exchange and order-placement APIs.

    Returns:
        None.
    """

    forbidden_patterns = (
        "x-mbx-apikey",
        "create_order",
        "new_order",
        "signed",
        "futures",
        "margin",
        "leverage",
    )

    for path in API_DIR.glob("*.py"):
        source = path.read_text(encoding="utf-8").lower()
        for pattern in forbidden_patterns:
            assert pattern not in source, f"Forbidden trading/API-key pattern {pattern!r} found in {path}"
