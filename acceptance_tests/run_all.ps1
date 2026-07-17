# PowerShell mirror of run_all.sh — delegates to bash (Git Bash ships with Git for Windows).
# Usage: powershell -File acceptance_tests/run_all.ps1   (add -Strict for strict vendor integrity)
param([switch]$Strict)

$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$bash = (Get-Command bash -ErrorAction SilentlyContinue)
if ($null -eq $bash) {
    Write-Error "bash not found. Install Git for Windows (provides Git Bash) or run the .sh tests directly."
    exit 2
}
if ($Strict) { $env:STRICT = "1" }
& $bash.Source (Join-Path $dir "run_all.sh")
exit $LASTEXITCODE
