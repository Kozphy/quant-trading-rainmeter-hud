# quant-trading-rainmeter-hud

## What This Project Does

`quant-trading-rainmeter-hud` is a Windows-friendly, local-first market observability platform for quantitative trading workflows.  
It uses Binance public market data, a local FastAPI backend, and a Rainmeter desktop HUD.

## Safety Model

This project is intentionally read-only.

It does not:
- place trades
- connect to exchange accounts
- store private API keys
- store Binance API keys
- make portfolio allocation decisions

The HUD is designed for observability, not automated execution.

## Architecture

```text
Binance Public API
    ↓
Market Data Adapter
    ↓
Data Normalizer
    ↓
Signal Engine
    ↓
Risk Engine
    ↓
Local Cache / Last Known Good State
    ↓
FastAPI Read API
    ↓
Rainmeter HUD
```

## Features

- FastAPI read API with typed Pydantic response models
- Binance public REST client with timeout and parse error handling
- Last-known-good cache with explicit `LIVE`, `STALE`, and `ERROR` states
- Placeholder monitoring signal engine (`LONG`, `SHORT`, `WAIT`) with reasons/rules
- Monitoring-safe risk metrics (no account-level exposure assumptions)
- JSONL logs for market snapshots, signal decisions, and system events
- Rainmeter WebParser HUD mapped to nested `/data` contract
- Beginner-friendly Windows startup script

## Quick Start

1. Install Python and Rainmeter on Windows.
2. Copy `.env.example` to `.env` (optional) and adjust values.
3. Run:

```powershell
api\start_api.bat
```

4. Open:
- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/ready`
- `http://127.0.0.1:8000/data`
- `http://127.0.0.1:8000/calendar`
- `http://127.0.0.1:8000/metrics`

## API Endpoints

- `GET /`: process liveness
- `GET /health`: API alive check
- `GET /ready`: freshness-based readiness
- `GET /data`: typed HUD payload
- `GET /calendar`: static operations tasks
- `GET /metrics`: request/binance/data-age metrics

## Data Contract

`/data` returns:

```json
{
  "market": {
    "btc_price": 0.0,
    "btc_change_24h": 0.0,
    "eth_price": 0.0,
    "eth_change_24h": 0.0
  },
  "signal": {
    "action": "WAIT",
    "confidence": 0.51,
    "regime": "Sideways",
    "reason": "BTC 24h change is between -1% and +1%",
    "rules_triggered": ["-1.0 < btc_change_24h < 1.0"]
  },
  "risk": {
    "realized_volatility_24h": 0.0,
    "price_drawdown_from_recent_high": 0.0,
    "signal_flip_count_1h": 0,
    "data_staleness_seconds": 0
  },
  "system": {
    "bot_status": "RUNNING",
    "data_status": "LIVE",
    "latency_ms": 0,
    "last_success_at": "2026-04-26T12:00:00+08:00",
    "updated_at": "2026-04-26T12:00:00+08:00"
  }
}
```

## Signal Logic

The current signal rules are placeholder monitoring logic:
- `LONG` when BTC 24h change `>= +1%`
- `SHORT` when BTC 24h change `<= -1%`
- `WAIT` otherwise

This is not a production strategy engine.

## Failure Handling

- On successful Binance fetch: cache updates, `data_status=LIVE`.
- On Binance failure with cache: return last known good data, `data_status=STALE`, `bot_status=WARNING`, and expose data staleness seconds.
- On Binance failure without cache: safe zero values, `data_status=ERROR`, `bot_status=ERROR`.

## Logs

Append-only JSONL files under `logs/`:
- `market_snapshots.jsonl`
- `signal_decisions.jsonl`
- `system_events.jsonl`

## Testing

```powershell
python -m pip install -r api\requirements.txt
python -m pip install -r api\requirements-dev.txt
python -m pytest -q
```

## Limitations

- Signal/risk calculations are monitoring placeholders.
- Risk metrics do not represent account-level exposure.
- No historical database yet beyond in-memory cache and logs.
- Rainmeter integration depends on local API availability.

## Roadmap

- Add rolling local time-series persistence for richer risk metrics
- Add optional websocket adapter for lower-latency public data
- Add lightweight dashboard snapshots and alert hooks (still monitoring-only)

## Resume Positioning

This project demonstrates backend/platform engineering for:
- resilient data pipelines with stale-data controls
- typed API contract design with FastAPI + Pydantic
- Windows-first operational UX with Rainmeter integration
- safe quant observability architecture without execution risk

## Disclaimer

This project is for engineering demonstration and market monitoring only.  
It is not financial advice, not a trading bot, and not a production execution system.
