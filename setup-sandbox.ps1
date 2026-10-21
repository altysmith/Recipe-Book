$ErrorActionPreference = 'Stop'
$sandboxPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $sandboxPython)) {
    $candidates = @()
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) { $candidates += @{ Path = $launcher.Source; Prefix = @('-3') } }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) { $candidates += @{ Path = $python.Source; Prefix = @() } }
    $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $bundledPython) {
        $candidates += @{ Path = $bundledPython; Prefix = @() }
    }

    $workingPython = $null
    foreach ($candidate in $candidates) {
        try {
            & $candidate.Path @($candidate.Prefix) -c 'import sys; assert sys.version_info >= (3, 10)' *> $null
            if ($LASTEXITCODE -eq 0) { $workingPython = $candidate; break }
        } catch { }
    }
    if (-not $workingPython) {
        throw 'Python 3 is not installed or available. Run: winget install --id Python.Python.3.12 -e --source winget --scope user. Then open a new PowerShell window and run .\setup-sandbox.ps1 again.'
    }

    & $workingPython.Path @($workingPython.Prefix) -m venv (Join-Path $PSScriptRoot '.venv')
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $sandboxPython)) {
        throw 'Could not create the sandbox Python environment. Check the Python installation, then run setup again.'
    }
}

& $sandboxPython -m pip install --disable-pip-version-check -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
& $sandboxPython -c 'import pdfplumber, PIL, yt_dlp'
if ($LASTEXITCODE -ne 0) { throw 'Python dependency verification failed.' }
Write-Host 'Sandbox Python dependencies are ready.'
