$ErrorActionPreference = 'Stop'
$recipeUrl = 'http://127.0.0.1:8771'
try {
    $recipeHealth = Invoke-RestMethod "$recipeUrl/health" -TimeoutSec 2
    if ($recipeHealth.app -eq 'little-recipe-box' -and $recipeHealth.version -eq 1) { Start-Process $recipeUrl; exit 0 }
    throw 'Port 8771 belongs to another application.'
} catch {
    if ($recipeHealth) { throw }
}
$recipePython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (!(Test-Path -LiteralPath $recipePython)) { $recipePython = (Get-Command python -ErrorAction Stop).Source }
$recipeServer = Join-Path $PSScriptRoot 'server.py'
$recipeProcess = Start-Process -FilePath $recipePython -ArgumentList @('"' + $recipeServer + '"') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru
for ($recipeAttempt = 0; $recipeAttempt -lt 30; $recipeAttempt++) {
    Start-Sleep -Milliseconds 300
    if ($recipeProcess.HasExited) { throw 'Recipe server could not start. Port 8771 may be occupied.' }
    try { $recipeHealth = Invoke-RestMethod "$recipeUrl/health" -TimeoutSec 1 } catch { continue }
    if ($recipeHealth.app -eq 'little-recipe-box' -and $recipeHealth.version -eq 1) { Start-Process $recipeUrl; exit 0 }
}
throw 'Recipe Book did not respond. Run server.py to see the startup error.'
