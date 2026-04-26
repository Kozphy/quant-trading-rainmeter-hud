@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_CMD="

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

echo.
echo Quant Trading Rainmeter HUD - Local API
echo --------------------------------------
echo Using Python command: %PYTHON_CMD%
echo.
echo Checking pip...
%PYTHON_CMD% -m pip --version >nul 2>&1
if errorlevel 1 (
    echo pip was not found. Trying to install pip with ensurepip...
    %PYTHON_CMD% -m ensurepip --upgrade
    if errorlevel 1 goto pip_error
)

echo Installing Python requirements...
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 goto error

echo.
echo Starting API at http://127.0.0.1:8000
echo Press Ctrl+C to stop the server.
echo.
%PYTHON_CMD% -m uvicorn api_server:app --host 127.0.0.1 --port 8000
if errorlevel 1 goto error

goto done

:python_error
echo.
echo Python was not found.
echo Install Python from https://www.python.org/downloads/windows/
echo During setup, enable "Add python.exe to PATH".
pause
goto done

:pip_error
echo.
echo pip could not be started for the selected Python installation.
echo Reinstall Python from https://www.python.org/downloads/windows/
echo During setup, enable "pip" and "Add python.exe to PATH".
pause
goto done

:error
echo.
echo The API could not be started.
echo Check that Python is installed and that port 8000 is available.
pause

:done
endlocal
