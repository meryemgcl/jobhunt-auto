$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
$pythonArgs = @()
$pythonVersion = $null

if ($pythonLauncher) {
    foreach ($candidate in @("3.13", "3.12", "3.11")) {
        & $pythonLauncher.Source "-$candidate" --version *> $null
        if ($LASTEXITCODE -eq 0) {
            $pythonArgs = @("-$candidate")
            $pythonVersion = $candidate
            break
        }
    }
}

if (-not $pythonVersion -and $pythonCommand) {
    $versionOutput = & $pythonCommand.Source --version
    if ($versionOutput -match "Python 3\.(11|12|13)\.") {
        $pythonVersion = "3.$($Matches[1])"
    }
}

if (-not $pythonVersion) {
    throw "Python 3.11, 3.12, or 3.13 is required. Install one and rerun this script."
}

if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
    if ($pythonLauncher) {
        & $pythonLauncher.Source @pythonArgs -m venv .venv
    }
    else {
        & $pythonCommand.Source -m venv .venv
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the .venv virtual environment."
    }
}

$venvPython = Join-Path $root ".venv\Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upgrade pip in .venv."
}

& $venvPython -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install local runtime and development dependencies."
}

if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
    Write-Output "Created .env from .env.example. No secrets are required for preview mode."
}
else {
    Write-Output "Existing .env preserved."
}

New-Item -ItemType Directory -Path "data" -Force | Out-Null
Write-Output "Local setup ready with Python $pythonVersion."
Write-Output "No generative AI or LLM packages are installed by this setup."
Write-Output "Next: .\.venv\Scripts\python.exe main.py --dry-run"
