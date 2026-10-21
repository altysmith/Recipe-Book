$ErrorActionPreference = 'Stop'
$previousDataDir = $env:RECIPE_DATA_DIR
$sandboxDataDir = Join-Path $PSScriptRoot 'sandbox_data'
New-Item -ItemType Directory -Force -Path $sandboxDataDir | Out-Null
$env:RECIPE_DATA_DIR = $sandboxDataDir

try {
    Write-Host 'Weekly menu sandbox: http://127.0.0.1:8783/'
    Write-Host "Test data stays in $sandboxDataDir"
    Write-Host 'Press Ctrl+C to stop.'
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python (Join-Path $PSScriptRoot 'server.py') --port 8783
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 (Join-Path $PSScriptRoot 'server.py') --port 8783
    } else {
        throw 'Python 3 is required to run the Recipe Book sandbox.'
    }
} finally {
    $env:RECIPE_DATA_DIR = $previousDataDir
}
