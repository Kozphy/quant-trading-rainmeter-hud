@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_CMD="
set "VENV_DIR=%~dp0.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

echo.
echo Quant Trading Rainmeter HUD - Local API
echo --------------------------------------
echo Mode: monitoring only. No trading execution. No API keys.
echo.

py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
)

if not defined PYTHON_CMD (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=python"
    )
)

if not defined PYTHON_CMD goto python_error

echo Using Python command: %PYTHON_CMD%
echo.

if not exist "%VENV_PYTHON%" (
    echo Creating local virtual environment in api\.venv ...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 goto venv_error
)

echo Checking pip...
"%VENV_PYTHON%" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo pip was not found in the virtual environment. Trying ensurepip...
    "%VENV_PYTHON%" -m ensurepip --upgrade
    if errorlevel 1 goto pip_error
)

echo Installing Python requirements...
"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto install_error

"%VENV_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 goto install_error

echo.
echo API will run at: http://127.0.0.1:8000
echo Health check:    http://127.0.0.1:8000/health
echo HUD data:        http://127.0.0.1:8000/data
echo.
echo Keep this window open while using the Rainmeter HUD.
echo Press Ctrl+C to stop the server.
echo.

"%VENV_PYTHON%" -m uvicorn api_server:app --host 127.0.0.1 --port 8000
if errorlevel 1 goto run_error

goto done

:python_error
echo.
echo Python was not found.
echo Install Python from https://www.python.org/downloads/windows/
echo During setup, enable "Add python.exe to PATH".
pause
goto done

:venv_error
echo.
echo The virtual environment could not be created.
echo Try reinstalling Python and make sure the "venv" feature is enabled.
pause
goto done

:pip_error
echo.
echo pip could not be started inside api\.venv.
echo Delete api\.venv and run this file again, or reinstall Python with pip enabled.
pause
goto done

:install_error
echo.
echo Requirements could not be installed.
echo Check your internet connection and try again.
pause
goto done

:run_error
echo.
echo The API could not be started.
echo Check that port 8000 is not already in use.
pause

:done
endlocal
