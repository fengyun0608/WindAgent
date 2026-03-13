# WindAgent Setup Script

$Host.UI.RawUI.WindowTitle = "WindAgent Setup"

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "          WindAgent - AI Agent Framework Setup" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[Info] Run as Administrator for auto-start setup" -ForegroundColor Yellow
    Write-Host ""
}

$InstallDir = $PSScriptRoot
Set-Location $InstallDir

Write-Host "[1/6] Checking system..." -ForegroundColor Green
Write-Host ""

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[Error] Python not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Download: https://www.python.org/downloads/"
    Write-Host ""
    $installPython = Read-Host "Auto install Python? (Y/N)"
    if ($installPython -eq "Y" -or $installPython -eq "y") {
        Write-Host "Installing Python..." -ForegroundColor Yellow
        winget install Python.Python.3.11 --accept-source-agreements --accept-package-agreements
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[Error] Auto install failed" -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
        Write-Host "[OK] Python installed. Restart script." -ForegroundColor Green
        Read-Host "Press Enter to exit"
        exit 0
    }
    Read-Host "Press Enter to exit"
    exit 1
}

$pythonVersion = (python --version 2>&1).ToString().Split()[1]
Write-Host "[OK] Python: $pythonVersion" -ForegroundColor Green

$pipCmd = Get-Command pip -ErrorAction SilentlyContinue
if (-not $pipCmd) {
    Write-Host "[Error] pip not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] pip installed" -ForegroundColor Green

Write-Host ""
Write-Host "[2/6] Creating virtual environment..." -ForegroundColor Green
Write-Host ""

if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "[OK] venv created" -ForegroundColor Green
} else {
    Write-Host "[OK] venv exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "[3/6] Installing dependencies..." -ForegroundColor Green
Write-Host ""

& ".\venv\Scripts\Activate.ps1"

python -m pip install --upgrade pip -q 2>$null

if (Test-Path "requirements.txt") {
    pip install -r requirements.txt -q 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[Warning] Retrying..." -ForegroundColor Yellow
        pip install -r requirements.txt -q 2>$null
    }
    Write-Host "[OK] Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "[Error] requirements.txt not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[4/6] Checking config..." -ForegroundColor Green
Write-Host ""

$ConfigDir = "$env:LOCALAPPDATA\WindAgent"
if (-not (Test-Path $ConfigDir)) {
    New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
    Write-Host "[OK] Config dir created" -ForegroundColor Green
} else {
    Write-Host "[OK] Config dir exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "[5/6] Creating scripts..." -ForegroundColor Green
Write-Host ""

$startBatContent = "@echo off`nchcp 65001 >nul 2>&1`ncd /d `"$InstallDir`"`ncall venv\Scripts\activate.bat`npython main.py`npause"
[System.IO.File]::WriteAllText("$InstallDir\start.bat", $startBatContent, [System.Text.Encoding]::GetEncoding("gb2312"))
Write-Host "[OK] start.bat created" -ForegroundColor Green

$startSilentContent = "@echo off`ncd /d `"$InstallDir`"`nstart /b cmd /c `"venv\Scripts\pythonw.exe main.py`""
[System.IO.File]::WriteAllText("$InstallDir\start_silent.bat", $startSilentContent, [System.Text.Encoding]::GetEncoding("gb2312"))
Write-Host "[OK] start_silent.bat created" -ForegroundColor Green

$stopContent = "@echo off`ntaskkill /F /IM pythonw.exe 2>nul`ntaskkill /F /IM python.exe /FI `"WINDOWTITLE eq WindAgent*`" 2>nul`necho WindAgent stopped`npause"
[System.IO.File]::WriteAllText("$InstallDir\stop.bat", $stopContent, [System.Text.Encoding]::GetEncoding("gb2312"))
Write-Host "[OK] stop.bat created" -ForegroundColor Green

Write-Host ""
Write-Host "[6/6] Setting up auto-start..." -ForegroundColor Green
Write-Host ""

$StartupFolder = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$ShortcutPath = "$StartupFolder\WindAgent.lnk"

try {
    $WScriptShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "$InstallDir\start_silent.bat"
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.Description = "WindAgent"
    $Shortcut.Save()
    Write-Host "[OK] Auto-start configured" -ForegroundColor Green
} catch {
    Write-Host "[Warning] Auto-start setup failed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "                   Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Start: start.bat (console) or start_silent.bat (background)" -ForegroundColor White
Write-Host "  Stop:  stop.bat" -ForegroundColor White
Write-Host "  URL:   http://127.0.0.1:8765" -ForegroundColor Yellow
Write-Host "  Config: $env:LOCALAPPDATA\WindAgent\config.json" -ForegroundColor White
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$startNow = Read-Host "Start WindAgent now? (Y/N)"
if ($startNow -eq "Y" -or $startNow -eq "y") {
    Write-Host "Starting WindAgent..." -ForegroundColor Yellow
    Start-Process "$InstallDir\start.bat"
}

Write-Host ""
Read-Host "Press Enter to exit"
