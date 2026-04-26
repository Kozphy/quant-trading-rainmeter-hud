# Troubleshooting

## Rainmeter shows blank

Check that the API is running:

```text
http://127.0.0.1:8000/data
```

If the browser cannot open the URL, start:

```text
api\start_api.bat
```

Then open Rainmeter, click **Manage**, and click **Refresh all**.

## API not running

Run the batch file from File Explorer:

```text
api\start_api.bat
```

If it closes immediately, open PowerShell in the project folder and run:

```powershell
cd api
python -m pip install -r requirements.txt
python -m uvicorn api_server:app --host 127.0.0.1 --port 8000
```

The terminal must stay open while the API is running.

## Binance API error

The server handles Binance failures by returning fallback values and setting:

```json
{"bot_status": "WARNING"}
```

Common causes:

- No internet connection
- Corporate firewall
- Regional network restrictions
- Temporary Binance outage

When Binance recovers, refresh the Rainmeter skin or wait for the next update.

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

The startup script tries `py -3` first and then `python`. If both commands fail,
reinstall Python and enable **Add python.exe to PATH**.

## Port 8000 already in use

Another process is using the local API port.

Find it:

```powershell
netstat -ano | findstr :8000
```

Stop the process from Task Manager, or change the port in both places:

- `api\start_api.bat`
- `rainmeter\QuantTradingHUD\QuantTradingHUD.ini`

If you change the port to `8001`, the Rainmeter URL should become:

```text
http://127.0.0.1:8001/data
```
