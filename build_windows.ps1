# Build a Windows executable of WordTool.
# Run from the project root:
#   powershell -ExecutionPolicy Bypass -File .\build_windows.ps1

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
}

Write-Host "Installing dependencies..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

Write-Host "Cleaning previous build output..." -ForegroundColor Cyan
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

Write-Host "Running PyInstaller..." -ForegroundColor Cyan
& .\.venv\Scripts\pyinstaller.exe --clean --noconfirm WordTool.spec

Write-Host ""
Write-Host "Build complete." -ForegroundColor Green
Write-Host "Launch the app with: .\dist\WordTool\WordTool.exe"
