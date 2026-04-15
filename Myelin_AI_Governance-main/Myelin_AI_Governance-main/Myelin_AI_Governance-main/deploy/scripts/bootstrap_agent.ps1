$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$VenvPath = Join-Path $RepoRoot ".venv"
$PythonExe = Join-Path $VenvPath "Scripts\\python.exe"

if (-not (Test-Path $VenvPath)) {
    python -m venv $VenvPath
}

& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r (Join-Path $RepoRoot "requirements.txt")

Write-Host "Bootstrap complete."
Write-Host "Activate with: $VenvPath\\Scripts\\Activate.ps1"
Write-Host "Run agent with: cd $RepoRoot\\agent; $PythonExe run_agent.py"
