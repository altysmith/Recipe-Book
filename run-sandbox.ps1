$ErrorActionPreference = 'Stop'
$previousDataDir = $env:RECIPE_DATA_DIR
$sandboxDataDir = Join-Path $PSScriptRoot 'sandbox_data'
$sandboxPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $sandboxPython)) {
    throw 'Sandbox dependencies are not installed. Run .\setup-sandbox.ps1 first.'
}
New-Item -ItemType Directory -Force -Path $sandboxDataDir | Out-Null
$env:RECIPE_DATA_DIR = $sandboxDataDir

try {
    Write-Host 'Weekly menu sandbox: http://127.0.0.1:8783/'
    Write-Host "Test data stays in $sandboxDataDir"
    Write-Host 'Press Ctrl+C to stop.'
    & $sandboxPython (Join-Path $PSScriptRoot 'server.py') --port 8783
} finally {
    $env:RECIPE_DATA_DIR = $previousDataDir
}
