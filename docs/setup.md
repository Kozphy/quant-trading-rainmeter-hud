# Windows Setup

This project runs a local FastAPI server and a Rainmeter skin. It is
monitoring-only: no account connection, no API keys, and no real trading.

## 1. Install Python

1. Download Python from https://www.python.org/downloads/windows/
2. During installation, enable **Add python.exe to PATH**.
3. Open a new PowerShell window and verify:

```powershell
python --version
py -3 --version
```

At least one of those commands should work.

## 2. Install Rainmeter

1. Download Rainmeter from https://www.rainmeter.net/
2. Install it using the standard Windows installer.
3. Start Rainmeter once so it creates:

```text
Documents\Rainmeter\Skins
```

## 3. Start the local API

Double-click:

```text
api\start_api.bat
```

The script will:

1. Find Python with `py -3` or `python`.
2. Create a local virtual environment at `api\.venv` if missing.
3. Install requirements.
4. Start FastAPI at:

```text
http://127.0.0.1:8000
```

Keep the terminal open while using the HUD.

## 4. Test the API

Open these URLs:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/symbols
http://127.0.0.1:8000/data
http://127.0.0.1:8000/history?symbol=BTCUSDT
```

If Binance is blocked or offline, `/data` still returns fallback history with
`bot_status` set to `WARNING`.

## 5. Install the Rainmeter skin

Copy:

```text
rainmeter\QuantTradingHUD
```

into:

```text
Documents\Rainmeter\Skins
```

Then:

1. Open Rainmeter.
2. Click **Manage**.
3. Click **Refresh all**.
4. Open `QuantTradingHUD`.
5. Load `QuantTradingHUD.ini`.

## 6. Optional symbol configuration

Set environment variables before starting the API:

```powershell
setx HUD_SYMBOLS "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT"
setx HUD_PRIMARY_SYMBOL "BTCUSDT"
```

Open a new terminal or restart Windows after `setx`, then run
`api\start_api.bat` again.

## 7. Daily use

1. Start `api\start_api.bat`.
2. Load or refresh the Rainmeter skin.
3. Keep the API terminal open.

Press `Ctrl+C` in the terminal to stop the local API.

## 8. Developer validation

Install developer test requirements:

```powershell
python -m pip install -r api\requirements.txt
python -m pip install -r api\requirements-dev.txt
```

Run the same checks used by GitHub Actions:

```powershell
python -m compileall api
python -m pytest -q
python scripts\generate_build_manifest.py --output docs\build-manifest.json
```
