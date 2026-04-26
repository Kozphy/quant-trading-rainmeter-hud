# quant-trading-rainmeter-hud

A Windows-friendly Quant Trading Desktop HUD built with Rainmeter and a local
FastAPI backend.

This project is monitoring only. It does not place trades, does not connect to
an exchange account, does not require API keys, and does not provide financial
advice. The signal logic is educational and should not be used as a live trading
strategy.

## Architecture

```text
Binance Public API
    |
    v
FastAPI Local Server
    |------------------.
    v                  v
Rainmeter Desktop HUD  SQLite Local History
```

The local API runs at:

```text
http://127.0.0.1:8000
```

## Features

- FastAPI local server
- Binance public REST kline data
- Multi-symbol support:
  - `BTCUSDT`
  - `ETHUSDT`
  - `SOLUSDT`
  - `BNBUSDT`
- Configurable symbols through environment variables
- RSI, SMA 20, SMA 50, price change, and trend classification
- Educational signal engine: `LONG`, `SHORT`, or `WAIT`
- Real calculated monitoring metrics from recent price history:
  - volatility
  - max drawdown
  - Sharpe-like score
  - exposure fixed at `0.0`
- SQLite storage for recent market snapshots
- Rainmeter WebParser HUD
- One-file Windows startup script that creates `api\.venv`
- Windows GitHub Actions CI with contract tests and packaging artifact
- Manual auto-commit workflow for validated build manifest updates

## Quick Start

1. Install Python from https://www.python.org/downloads/windows/
   - During setup, enable **Add python.exe to PATH**.
2. Install Rainmeter from https://www.rainmeter.net/
3. Double-click:

```text
api\start_api.bat
```

Keep this terminal window open while using the HUD.

4. Open these URLs in your browser:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/data
http://127.0.0.1:8000/symbols
```

5. Copy this folder:

```text
rainmeter\QuantTradingHUD
```

to:

```text
Documents\Rainmeter\Skins
```

6. In Rainmeter, go to **Manage**, click **Refresh all**, then load:

```text
QuantTradingHUD.ini
```

## API Endpoints

### `GET /`

Same as `/health`, kept for simple browser checks.

### `GET /health`

Returns local API status, configured symbols, and SQLite storage status.

### `GET /symbols`

Returns configured symbol metadata and the primary selected symbol.

### `GET /data`

Returns Rainmeter-friendly top-level fields plus nested per-symbol data.

Optional query:

```text
http://127.0.0.1:8000/data?symbol=SOLUSDT
```

Key fields:

```json
{
  "selected_symbol": "BTCUSDT",
  "btc_price": 65000.0,
  "eth_price": 3200.0,
  "sol_price": 145.0,
  "bnb_price": 590.0,
  "signal": "WAIT",
  "confidence": 0.5,
  "regime": "Sideways",
  "rsi": 52.1,
  "sma20": 64950.0,
  "sma50": 64750.0,
  "volatility": 0.45,
  "drawdown": -1.2,
  "sharpe": 0.8,
  "exposure": 0.0,
  "bot_status": "RUNNING",
  "updated_at": "2026-04-26 12:00:00"
}
```

If Binance public data is unavailable, the API returns deterministic fallback
history and sets `bot_status` to `WARNING`.

### `GET /calendar`

Returns today's operating tasks:

```json
{
  "date": "2026-04-26",
  "tasks": [
    {"time": "09:00", "name": "Risk Review"},
    {"time": "14:30", "name": "Backtest Batch"},
    {"time": "20:30", "name": "US Macro Watch"},
    {"time": "23:00", "name": "Execution Log Audit"}
  ]
}
```

### `GET /history?symbol=BTCUSDT`

Returns recent SQLite snapshots for a configured symbol.

Optional query:

```text
http://127.0.0.1:8000/history?symbol=BTCUSDT&limit=50
```

## Signal Logic

The educational signal engine uses recent close-price history:

```text
LONG  if price > SMA20 > SMA50 and RSI is between 50 and 70
SHORT if price < SMA20 < SMA50 and RSI is below 45
WAIT  otherwise
```

This is not financial advice and is not a production strategy.

## Configuration

The default symbols are:

```text
BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT
```

Optional Windows environment variables:

```text
HUD_SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT
HUD_PRIMARY_SYMBOL=BTCUSDT
HUD_KLINE_INTERVAL=1h
HUD_KLINE_LIMIT=120
HUD_DATABASE_PATH=C:\path\to\market_history.db
```

Restart `api\start_api.bat` after changing environment variables.

## Project Structure

```text
quant-trading-rainmeter-hud/
|- api/
|  |- api_server.py
|  |- calendar_data.py
|  |- config.py
|  |- indicators.py
|  |- market_data.py
|  |- risk.py
|  |- storage.py
|  |- requirements.txt
|  `- start_api.bat
|- rainmeter/
|  `- QuantTradingHUD/
|     `- QuantTradingHUD.ini
|- docs/
|  |- setup.md
|  |- architecture.md
|  |- ci-cd.md
|  |- build-manifest.json
|  `- troubleshooting.md
|- tests/
|  `- test_api_contract.py
|- scripts/
|  `- generate_build_manifest.py
|- .github/
|  `- workflows/
|     |- ci.yml
|     `- auto-commit.yml
|- README.md
|- AGENTS.md
`- .gitignore
```

## Documentation

- [Windows setup](docs/setup.md)
- [Architecture](docs/architecture.md)
- [CI/CD](docs/ci-cd.md)
- [Troubleshooting](docs/troubleshooting.md)

## Limitations

- No trading execution
- No account connection
- No private Binance API usage
- No API keys
- Educational signal logic only
- Fallback data is for offline display continuity only
- Rainmeter must be refreshed if the API URL or port changes
