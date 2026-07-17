<#
.SYNOPSIS
    MANUAL acceptance test: run ONE real Claude-backed engineering-intent
    classification (TASK-CLASSIFY-0001) and stop.

.DESCRIPTION
    This script invokes a REAL Claude Code process. It is deliberately separate
    from the automated test suite (which mocks Claude). Run it only intentionally.

    It:
      * executes only TASK-CLASSIFY-0001;
      * requires an existing run directory containing state.yaml, manifest.yaml,
        and inputs/work-request.md (use a temporary or gitignored run under
        runtime/runs/<RUN_ID>/);
      * commits the output through the runtime transaction layer;
      * stops immediately afterward (one task only).

    It performs NO implicit looping and grants NO approval. Claude Code's own
    permissions govern what Claude may access.

.PARAMETER Run
    Existing run directory (e.g. runtime\runs\RUN-REASON-MANUAL-0001).

.PARAMETER ClaudeCommand
    The Claude executable (default: 'claude').

.EXAMPLE
    # 1) plan BEFORE
    .\scripts\plan-workflow.ps1 -Run runtime\runs\RUN-REASON-MANUAL-0001
    # 2) run one real Claude classification
    .\scripts\run-intent-task-with-claude.ps1 -Run runtime\runs\RUN-REASON-MANUAL-0001
    # 3) plan AFTER + show provenance
    .\scripts\plan-workflow.ps1 -Run runtime\runs\RUN-REASON-MANUAL-0001
    Get-Content runtime\runs\RUN-REASON-MANUAL-0001\provenance\TASK-CLASSIFY-0001.yaml
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $Run,
    [string] $ClaudeCommand = "claude",
    [double] $Timeout = 180,
    [ValidateSet("text", "json")] [string] $Format = "text"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot '_ecf-common.ps1')
$env:PYTHONDONTWRITEBYTECODE = "1"

$EcfRoot = Get-EcfRoot
$Python  = Get-PythonExe
$RunTask = Join-Path $EcfRoot "tools/task_runner/run_task.py"
$WF = Join-Path $EcfRoot "workflows/reasoning/WF-REASON-0001-engineering-recommendation.md"

if (-not (Test-Path (Join-Path $Run "inputs\work-request.md"))) {
    throw "Expected a Work Request at $Run\inputs\work-request.md (read-only input)."
}

Write-Host "MANUAL: running ONE real Claude classification (TASK-CLASSIFY-0001)..." -ForegroundColor Yellow
& $Python $RunTask $WF --run $Run --task TASK-CLASSIFY-0001 `
    --executor claude-code --allow-ai-executor `
    --claude-command $ClaudeCommand --timeout $Timeout --format $Format
$rc = $LASTEXITCODE

Write-Host ""
Write-Host "Verify no canonical/vendor file changed:" -ForegroundColor Yellow
# Optional, best-effort diagnostic only: report status via whichever Git repo
# actually tracks the ECF files (canonical or host). Never used to locate ECF.
$GitRoot = Get-OuterGitRoot -StartDir $EcfRoot
if ($GitRoot) {
    & git -C $GitRoot status --short -- vendor tasks workflows execution knowledge principles
} else {
    Write-Host "  (no Git repository detected; skipping status report)"
}
exit $rc
