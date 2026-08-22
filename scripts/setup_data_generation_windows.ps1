[CmdletBinding()]
param(
    [string]$PythonCommand = "python",
    [switch]$SkipSmokeTest
)

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptRoot "..")).Path
$codeRoot = Join-Path $repoRoot "Code"
$venvRoot = Join-Path $codeRoot ".venv-generation"
$venvPython = Join-Path $venvRoot "Scripts\python.exe"

Write-Host "Setting up synthetic data generation in $codeRoot"

if (-not (Test-Path -LiteralPath $venvPython)) {
    & $PythonCommand -m venv $venvRoot
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $codeRoot "requirements-generation.txt")

$envPath = Join-Path $codeRoot ".env"
if (-not (Test-Path -LiteralPath $envPath)) {
    Copy-Item -LiteralPath (Join-Path $codeRoot ".env.example") -Destination $envPath
    Write-Host "Created Code\.env from .env.example. Add provider API keys before live calls."
} else {
    Write-Host "Preserved existing Code\.env. Copy missing generation variables from .env.example."
}

Push-Location $codeRoot
try {
    & $venvPython -m pytest tests/data_generation -q
    & $venvPython run_data_generation.py plan --families 100 --seed 42
    if (-not $SkipSmokeTest) {
        $runId = "setup-smoke-" + (Get-Date -Format "yyyyMMdd-HHmmss")
        & $venvPython run_data_generation.py dry-run --families 12 --seed 42 --run-id $runId
    }
} finally {
    Pop-Location
}

Write-Host "Setup complete. Run Code\.venv-generation\Scripts\python.exe Code\run_data_generation.py check-env"
