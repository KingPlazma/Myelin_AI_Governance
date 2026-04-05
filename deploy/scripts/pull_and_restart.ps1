param(
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$VenvPath = Join-Path $RepoRoot ".venv"
$PythonExe = Join-Path $VenvPath "Scripts\\python.exe"
$AgentDir = Join-Path $RepoRoot "agent"

git -C $RepoRoot fetch --all
git -C $RepoRoot checkout $Branch
git -C $RepoRoot pull origin $Branch

& $PythonExe -m pip install -r (Join-Path $RepoRoot "requirements.txt")

Get-Process | Where-Object { $_.ProcessName -like "python*" } | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Process $PythonExe -ArgumentList "run_agent.py" -WorkingDirectory $AgentDir

Write-Host "Myelin agent updated from Git and restarted."
