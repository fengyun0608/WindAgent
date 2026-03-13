@echo off
setlocal enabledelayedexpansion
title WindAgent Setup

echo.
echo ========================================================
echo          WindAgent - AI Agent Framework Setup
echo ========================================================
echo.

net session >nul 2>&1
if !errorlevel! neq 0 (
    echo [Info] Run as Administrator for auto-start setup
    echo.
)

set "INSTALL_DIR=%~dp0"
cd /d "%INSTALL_DIR%"

echo [1/6] Checking system...
echo.

python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [Error] Python not found!
    echo.
    echo Download: https://www.python.org/downloads/
    echo.
    set /p INSTALL_PYTHON="Auto install Python? (Y/N): "
    if /i "!INSTALL_PYTHON!"=="Y" (
        echo Installing Python...
        winget install Python.Python.3.11 --accept-source-agreements --accept-package-agreements
        if !errorlevel! neq 0 (
            echo [Error] Auto install failed
            pause
            exit /b 1
        )
        echo [OK] Python installed. Restart script.
        pause
        exit /b 0
    )
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python: %PYTHON_VERSION%

pip --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [Error] pip not found
    pause
    exit /b 1
)
echo [OK] pip installed

echo.
echo [2/6] Creating virtual environment...
echo.

if not exist "venv" (
    python -m venv venv
    echo [OK] venv created
) else (
    echo [OK] venv exists
)

echo.
echo [3/6] Installing dependencies...
echo.

call venv\Scripts\activate.bat
python -m pip install --upgrade pip -q 2>nul

if exist "requirements.txt" (
    pip install -r requirements.txt -q 2>nul
    if !errorlevel! neq 0 (
        echo [Warning] Retrying...
        pip install -r requirements.txt -q 2>nul
    )
    echo [OK] Dependencies installed
) else (
    echo [Error] requirements.txt not found
    pause
    exit /b 1
)

echo.
echo [4/6] Checking config...
echo.

set "CONFIG_DIR=%LOCALAPPDATA%\WindAgent"
if not exist "%CONFIG_DIR%" (
    mkdir "%CONFIG_DIR%"
    echo [OK] Config dir created
) else (
    echo [OK] Config dir exists
)

echo.
echo [5/6] Creating scripts...
echo.

echo @echo off > start.bat
echo cd /d "%INSTALL_DIR%" >> start.bat
echo call venv\Scripts\activate.bat >> start.bat
echo python main.py >> start.bat
echo pause >> start.bat
echo [OK] start.bat created

echo @echo off > start_silent.bat
echo cd /d "%INSTALL_DIR%" >> start_silent.bat
echo start /b cmd /c "venv\Scripts\pythonw.exe main.py" >> start_silent.bat
echo [OK] start_silent.bat created

echo @echo off > stop.bat
echo taskkill /F /IM pythonw.exe 2^>nul >> stop.bat
echo taskkill /F /IM python.exe /FI "WINDOWTITLE eq WindAgent*" 2^>nul >> stop.bat
echo echo WindAgent stopped >> stop.bat
echo pause >> stop.bat
echo [OK] stop.bat created

echo.
echo [6/6] Setting up auto-start...
echo.

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

echo Set oWS = WScript.CreateObject("WScript.Shell") > create_shortcut.vbs
echo sLinkFile = "%STARTUP_FOLDER%\WindAgent.lnk" >> create_shortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> create_shortcut.vbs
echo oLink.TargetPath = "%INSTALL_DIR%start_silent.bat" >> create_shortcut.vbs
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> create_shortcut.vbs
echo oLink.Description = "WindAgent" >> create_shortcut.vbs
echo oLink.Save >> create_shortcut.vbs

cscript //nologo create_shortcut.vbs >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] Auto-start configured
) else (
    echo [Warning] Auto-start setup failed
)
del create_shortcut.vbs >nul 2>&1

echo.
echo ========================================================
echo                   Setup Complete!
echo ========================================================
echo.
echo   Start: start.bat (console) or start_silent.bat (background)
echo   Stop:  stop.bat
echo   URL:   http://127.0.0.1:8765
echo   Config: %LOCALAPPDATA%\WindAgent\config.json
echo.
echo ========================================================
echo.

set /p START_NOW="Start WindAgent now? (Y/N): "
if /i "!START_NOW!"=="Y" (
    echo Starting WindAgent...
    start "" "%INSTALL_DIR%start.bat"
)

echo.
pause
