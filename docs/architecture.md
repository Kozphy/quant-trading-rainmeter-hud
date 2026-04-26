# Architecture

## Final Architecture

```text
Binance Public API
    |
    v
FastAPI Local Server
    |------------------.
    v                  v
Rainmeter Desktop HUD  SQLite Local History
```

## Safety Boundary

This project is monitoring-only.

- No order placement
- No account connection
- No private Binance endpoints
- No API keys
- No real trading execution

The signal logic is educational and not financial advice.

## Data Layer

The data layer uses Binance public REST klines for:

- `BTCUSDT`
- `ETHUSDT`
- `SOLUSDT`
- `BNBUSDT`

Configuration is loaded from environment variables in `api/config.py`.

When Binance is unavailable, the data layer returns deterministic fallback
history so the HUD remains visible. The API marks this state with
`bot_status = WARNING`.

## Indicator Layer

`api/indicators.py` calculates:

- RSI
- SMA 20
- SMA 50
- price change percentage
- simple trend classification

Signal rules:

```text
LONG  if price > SMA20 > SMA50 and RSI is between 50 and 70
SHORT if price < SMA20 < SMA50 and RSI is below 45
WAIT  otherwise
```

## Risk Layer

`api/risk.py` calculates metrics from recent close-price history:

- volatility from simple returns
- max drawdown from the price path
- Sharpe-like score from average return and return volatility
- exposure fixed at `0.0`

Exposure is always zero because this system does not trade.

## Storage Layer

`api/storage.py` stores recent snapshots in SQLite:

```text
api\market_history.db
```

The database is local runtime state and is ignored by Git.

The `/history?symbol=BTCUSDT` endpoint reads from this table.

## API Layer

FastAPI runs locally at:

```text
http://127.0.0.1:8000
```

Endpoints:

- `GET /`
- `GET /health`
- `GET /data`
- `GET /symbols`
- `GET /calendar`
- `GET /history?symbol=BTCUSDT`

`/data` returns stable top-level fields for Rainmeter plus nested per-symbol
details for API users.

## Rainmeter UI Layer

Rainmeter uses `WebParser` to read:

```text
http://127.0.0.1:8000/data
http://127.0.0.1:8000/calendar
```

The HUD displays:

- BTC price
- ETH price
- selected signal
- RSI
- SMA 20
- SMA 50
- volatility
- drawdown
- bot status
- updated time
- today's trading tasks

## Future Upgrade Path

Practical upgrades:

- WebSocket market data for lower latency.
- Per-symbol selection from a Rainmeter variable.
- Telegram or Discord alerts for status changes.
- Strategy versioning and backtest reports.
- Risk-limit dashboards and audit exports.

Execution should stay out of scope unless explicitly approved and isolated
behind separate credentials, permissions, tests, and controls.

## CI/CD Layer

GitHub Actions validates the project on Windows. The workflow compiles the
backend, runs deterministic API contract tests, checks Rainmeter WebParser
compatibility, and uploads a zip artifact after successful push builds.

CI/CD is delivery automation only. It does not deploy a live trading service and
does not introduce API keys or execution permissions.

An optional manual auto-commit workflow can update `docs/build-manifest.json`
after validation and push that one generated file back to GitHub. The commit
message uses `[skip ci]` by default to prevent recursive workflow runs.
