<#
.SYNOPSIS
    Compute an ECF execution plan for a workflow (read-only).

.DESCRIPTION
    Thin wrapper around tools/workflow_planner/plan_workflow.py. It answers a
    single question: which task(s) are runnable right now?

    It validates the workflow, inspects an optional runtime directory, and prints
    the plan. It does not execute tasks, invoke AI, or modify any file.

.PARAMETER Workflow
    Path to the workflow specification. Defaults to WF-REASON-0001.

.PARAMETER Run
    Optional runtime run directory (runtime/runs/<RUN_ID>).

.PARAMETER Format
    Output format: text (default) or json.

.EXAMPLE
    .\scripts\plan-workflow.ps1

.EXAMPLE
    .\scripts\plan-workflow.ps1 -Run runtime\runs\RUN-REASON-20260710-0001 -Format json
#>
[CmdletBinding()]
param(
    [string] $Workflow,
    [string] $Run,
    [ValidateSet("text", "json")]
    [string] $Format = "text"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot '_ecf-common.ps1')
$env:PYTHONDONTWRITEBYTECODE = "1"

$EcfRoot = Get-EcfRoot
$Python  = Get-PythonExe
$Planner = Join-Path $EcfRoot "tools/workflow_planner/plan_workflow.py"

if (-not (Test-Path $Planner)) { throw "Planner not found: $Planner" }

if (-not $Workflow) {
    $Workflow = Join-Path $EcfRoot "workflows/reasoning/WF-REASON-0001-engineering-recommendation.md"
}

$plannerArgs = @($Planner, $Workflow, "--format", $Format)
if ($Run) { $plannerArgs += @("--run", $Run) }

& $Python @plannerArgs
$rc = $LASTEXITCODE
exit $rc
