# Windows Setup

This project runs a local FastAPI server and a Rainmeter skin. It does not
connect to a trading account and does not need exchange API keys.

## 1. Install Python

1. Download Python from https://www.python.org/downloads/windows/
2. During installation, enable **Add python.exe to PATH**.
3. Open PowerShell and verify:

```powershell
python --version
python -m pip --version
```

## 2. Install Rainmeter

1. Download Rainmeter from https://www.rainmeter.net/
2. Install it using the standard Windows installer.
3. Start Rainmeter once so it creates the `Documents\Rainmeter\Skins` folder.

## 3. Start the local API

Double-click:

```text
api\start_api.bat
```

The script uses `py -3` when available, falls back to `python`, installs Python
requirements, and starts:

```text
http://127.0.0.1:8000
```

Test the API in a browser:

```text
http://127.0.0.1:8000/data
```

## 4. Install the Rainmeter skin

1. Copy `rainmeter\QuantTradingHUD` into:

```text
Documents\Rainmeter\Skins
```

2. Open Rainmeter.
3. Click **Manage**.
4. Click **Refresh all**.
5. Open `QuantTradingHUD`.
6. Load `QuantTradingHUD.ini`.

## 5. Daily use

1. Start `api\start_api.bat`.
2. Load or refresh the Rainmeter skin.
3. Keep the API terminal open while using the HUD.

Close the terminal or press `Ctrl+C` to stop the local API.
