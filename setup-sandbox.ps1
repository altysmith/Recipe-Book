$ErrorActionPreference = 'Stop'
$sandboxPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $sandboxPython)) {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv (Join-Path $PSScriptRoot '.venv')
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv (Join-Path $PSScriptRoot '.venv')
    } else {
        throw 'Python 3 is required. Install it, then run this setup script again.'
    }
}

& $sandboxPython -m pip install --disable-pip-version-check -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
& $sandboxPython -c 'import pdfplumber, PIL, yt_dlp'
if ($LASTEXITCODE -ne 0) { throw 'Python dependency verification failed.' }
Write-Host 'Sandbox Python dependencies are ready.'
