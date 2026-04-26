# Architecture

## Final Architecture

```text
Binance Public API
    |
    v
FastAPI Local Server
    |
    v
Rainmeter Desktop HUD
```

## Data Layer

The data layer uses Binance public REST only:

- `BTCUSDT`
- `ETHUSDT`
- 24 hour ticker endpoint
- No account endpoints
- No API keys
- No order placement

If Binance is unavailable or returns invalid data, the API returns numeric
fallback values and sets `bot_status` to `WARNING`.

## API Layer

The FastAPI app runs locally at:

```text
http://127.0.0.1:8000
```

Endpoints:

- `GET /` returns a health check.
- `GET /data` returns market data, placeholder signal data, placeholder risk
  metrics, and timestamps.
- `GET /calendar` returns a static operating calendar for the HUD.

The signal engine is intentionally simple:

- BTC change >= 1 percent: `LONG`
- BTC change <= -1 percent: `SHORT`
- Otherwise: `WAIT`

This is a placeholder only. It is not a validated trading strategy.

## Rainmeter UI Layer

Rainmeter uses `WebParser` measures to read the local API and render a desktop
HUD. The skin displays:

- BTC and ETH prices
- 24 hour changes
- Placeholder signal and confidence
- Market regime
- Bot status
- Latency
- Placeholder exposure, drawdown, and Sharpe
- Date, day, and calendar tasks

## Future Upgrade Path

Practical upgrades:

- WebSocket market data for lower latency.
- Telegram or Discord alerts for status changes.
- A real signal engine with versioned strategy rules.
- A risk engine with limits, drawdown controls, and audit logs.
- An execution engine only after explicit approval, separate permissions, and
  strong safety controls.

Execution should remain out of scope until the monitoring layer is reliable,
observable, and tested.
