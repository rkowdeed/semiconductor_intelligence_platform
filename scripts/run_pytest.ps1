param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot '.venv/Scripts/python.exe'

if (-not (Test-Path $venvPython)) {
    Write-Error "Virtual environment Python was not found at $venvPython. Create the environment first using '.venv/Scripts/python -m pip install -r requirements.txt'."
    exit 1
}

Push-Location $repoRoot
try {
    & $venvPython -m pytest @PytestArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
