# Windows Setup

This project runs a local FastAPI server and a Rainmeter skin in monitoring-only mode.

## 1. Install dependencies

1. Install Python from [python.org](https://www.python.org/downloads/windows/) and enable `Add python.exe to PATH`.
2. Install Rainmeter from [rainmeter.net](https://www.rainmeter.net/).

## 2. Start the API

Double-click:

```text
api\start_api.bat
```

The script creates `api\.venv`, installs requirements, and runs the API on:

```text
http://127.0.0.1:8000
```

## 3. Verify endpoints

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/ready`
- `http://127.0.0.1:8000/data`
- `http://127.0.0.1:8000/calendar`
- `http://127.0.0.1:8000/metrics`

If Binance fails:
- data uses last known good cache when available
- `data_status` becomes `STALE`
- `bot_status` becomes `WARNING`

## 4. Install Rainmeter skin

Copy:

```text
rainmeter\QuantTradingHUD
```

to:

```text
Documents\Rainmeter\Skins
```

Then refresh Rainmeter and load `QuantTradingHUD.ini`.

## 5. Environment variables

Copy `.env.example` and adjust values:

```text
APP_HOST=127.0.0.1
APP_PORT=8000
BINANCE_BASE_URL=https://api.binance.com
MARKET_SYMBOLS=BTCUSDT,ETHUSDT
REQUEST_TIMEOUT_SECONDS=5
STALE_AFTER_SECONDS=60
LOG_LEVEL=INFO
```

Restart the API after changing environment variables.

## 6. Run tests

```powershell
python -m pip install -r api\requirements.txt
python -m pip install -r api\requirements-dev.txt
python -m pytest -q
```
