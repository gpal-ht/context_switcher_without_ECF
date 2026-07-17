<#
.SYNOPSIS
    Run exactly ONE ECF task against an initialized run (offline fixture executor
    by default). Correctly resolves the bundled ECF root.

.DESCRIPTION
    Consumer-side thin wrapper over the bundled task_runner. It resolves the ECF
    root as this repository's vendor/ecf via $PSScriptRoot — NOT via
    `git rev-parse --show-toplevel`, which would wrongly return the outer Context
    Switcher root (ECF is vendored inside this git tree). The outer git root is
    used only for the optional post-run repository-change report.

    The default executor is the offline 'fixture' executor (no AI). The live
    Claude executor requires BOTH -Executor claude-code AND the explicit
    -AllowLiveClaude opt-in; automated checks never pass it.

.PARAMETER Run
    Existing, initialized run directory (see initialize-ecf-run.ps1).

.PARAMETER Task
    Task ID to run (default TASK-CLASSIFY-0001). Exactly one task runs.

.PARAMETER Executor
    'fixture' (default, offline) or 'claude-code' (live; requires -AllowLiveClaude).

.PARAMETER Fixture
    Candidate-output fixture file (required for the fixture executor).

.PARAMETER AllowLiveClaude
    Explicit opt-in required before the live Claude executor may run.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $Run,
    [string] $Task = "TASK-CLASSIFY-0001",
    [ValidateSet("fixture", "claude-code")] [string] $Executor = "fixture",
    [string] $Fixture,
    [string] $Workflow,
    [switch] $AllowLiveClaude,
    [string] $ClaudeCommand = "claude",
    [double] $Timeout = 180,
    [ValidateSet("text", "json")] [string] $Format = "text"
)
$ErrorActionPreference = "Stop"

# Do not write .pyc into the vendored (read-only) ECF tree.
$env:PYTHONDONTWRITEBYTECODE = "1"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

# ECF adapter boundary (ADR-0007): ecf backend only; standalone refuses.
. (Join-Path $PSScriptRoot "lib\Resolve-EngineeringBackend.ps1")
Assert-EcfBackend -RepoRoot $RepoRoot -Operation "ECF task execution (run-ecf-task.ps1)"

$EcfRoot  = Join-Path $RepoRoot "vendor\ecf"
$RunTask  = Join-Path $EcfRoot "tools\task_runner\run_task.py"
if (-not $Workflow) {
    $Workflow = Join-Path $EcfRoot "workflows\reasoning\WF-REASON-0001-engineering-recommendation.md"
}
foreach ($p in @($RunTask, $Workflow)) {
    if (-not (Test-Path $p)) { throw "Required ECF path missing: $p  (refresh the bundle)." }
}
if (-not (Test-Path $Run)) { throw "Run directory not found: $Run" }
if (-not (Test-Path (Join-Path $Run "inputs\work-request.md"))) {
    throw "Run '$Run' is missing inputs\work-request.md. Initialize it with initialize-ecf-run.ps1 first."
}
$Python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Python) { throw "Python 3 was not found on PATH." }

$runAbs = (Resolve-Path $Run).Path
$argsList = @($RunTask, $Workflow, "--run", $runAbs, "--task", $Task, "--executor", $Executor, "--format", $Format)

if ($Executor -eq "fixture") {
    if (-not $Fixture) { throw "-Fixture <file> is required for the fixture executor." }
    $argsList += @("--fixture", (Resolve-Path $Fixture).Path)
}
elseif ($Executor -eq "claude-code") {
    if (-not $AllowLiveClaude) {
        throw "Refusing to run the LIVE Claude executor without -AllowLiveClaude (explicit AI opt-in)."
    }
    $argsList += @("--allow-ai-executor", "--claude-command", $ClaudeCommand, "--timeout", $Timeout)
}

& $Python @argsList
$rc = $LASTEXITCODE

# Optional repository-change report (outer git root, never ECF).
try {
    $outer = (& git -C $RepoRoot rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -eq 0 -and $outer) {
        Write-Host ""
        Write-Host "Repository change check (vendor must be unchanged):" -ForegroundColor Yellow
        & git -C $outer status --short -- vendor
    }
} catch { }

exit $rc
