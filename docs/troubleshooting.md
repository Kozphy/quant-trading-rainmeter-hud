# Troubleshooting

## Rainmeter shows blank

Check that the API is running:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/data
```

If the browser cannot open those URLs, start:

```text
api\start_api.bat
```

Then open Rainmeter, click **Manage**, and click **Refresh all**.

## API not running

Run the batch file from File Explorer:

```text
api\start_api.bat
```

If it fails, open PowerShell in the project folder and run:

```powershell
cd api
.\.venv\Scripts\python.exe -m uvicorn api_server:app --host 127.0.0.1 --port 8000
```

The terminal must stay open while the API is running.

## Python not found

Install Python from:

```text
https://www.python.org/downloads/windows/
```

During installation, enable:

```text
Add python.exe to PATH
```

After installation, open a new PowerShell window and verify:

```powershell
python --version
py -3 --version
```

The startup script tries `py -3` first and then `python`.

## Virtual environment problems

The startup script creates:

```text
api\.venv
```

If package installation gets corrupted:

1. Close the API terminal.
2. Delete `api\.venv`.
3. Run `api\start_api.bat` again.

## Binance API error

The server handles Binance public API failures by returning fallback history and
setting:

```json
{"bot_status": "WARNING"}
```

Common causes:

- No internet connection
- Corporate firewall
- Regional network restrictions
- Temporary Binance outage

The HUD should still render. Values are fallback demo values until Binance
public data becomes available again.

## Port 8000 already in use

Another process is using the local API port.

Find it:

```powershell
netstat -ano | findstr :8000
```

Stop the process from Task Manager, or change the port in both places:

- `api\start_api.bat`
- `rainmeter\QuantTradingHUD\QuantTradingHUD.ini`

If you change the port to `8001`, the Rainmeter URLs should become:

```text
http://127.0.0.1:8001/data
http://127.0.0.1:8001/calendar
```

## SQLite history looks empty

Call `/data` once first:

```text
http://127.0.0.1:8000/data
```

Then open:

```text
http://127.0.0.1:8000/history?symbol=BTCUSDT
```

The API stores snapshots when `/data` is requested.

## Signal seems too simple

That is intentional. The signal logic is educational:

```text
LONG  if price > SMA20 > SMA50 and RSI is between 50 and 70
SHORT if price < SMA20 < SMA50 and RSI is below 45
WAIT  otherwise
```

It is not financial advice and should not be treated as a production strategy.

## GitHub Actions fails

Run the local equivalent first:

```powershell
python -m pip install -r api\requirements.txt
python -m pip install -r api\requirements-dev.txt
python -m compileall api
python -m pytest -q
```

The CI tests use deterministic local data and should not fail because Binance is
down or blocked. If CI fails, check the API contract, Rainmeter regex, or safety
boundary test output.

## Auto-commit workflow does not push

Check repository settings in GitHub:

1. Open **Settings**.
2. Open **Actions**.
3. Open **General**.
4. Under **Workflow permissions**, allow **Read and write permissions**.

The auto-commit workflow uses GitHub's built-in `GITHUB_TOKEN`; it does not need
personal access tokens or exchange API keys.
