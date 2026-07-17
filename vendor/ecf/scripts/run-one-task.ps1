<#
.SYNOPSIS
    Execute exactly one planner-approved ECF task and stop.

.DESCRIPTION
    Wraps tools/task_runner/run_task.py. It performs NO implicit looping: one
    invocation runs at most one task. The only executor is the safe local
    fixture executor (no Claude, no arbitrary shell, no network).

    Exit codes: 0 committed, 1 rejected/failed, 2 config/infra, 3 recovery required.

.EXAMPLE
    .\scripts\run-one-task.ps1 -Workflow workflows\reasoning\WF-REASON-0001-engineering-recommendation.md `
        -Run runtime\runs\RUN-REASON-0001 -Task TASK-CLASSIFY-0001 `
        -Executor fixture -Fixture acceptance_tests\fixtures\task_runner\engineering-intent.yaml
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $Workflow,
    [Parameter(Mandatory = $true)] [string] $Run,
    [string] $Task,
    [switch] $Next,
    [ValidateSet("fixture")] [string] $Executor = "fixture",
    [string] $Fixture,
    [switch] $ForceRerun,
    [ValidateSet("text", "json")] [string] $Format = "text"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot '_ecf-common.ps1')
$env:PYTHONDONTWRITEBYTECODE = "1"

$EcfRoot = Get-EcfRoot
$Python  = Get-PythonExe
$RunTask = Join-Path $EcfRoot "tools/task_runner/run_task.py"
if (-not (Test-Path $RunTask)) { throw "Runner not found: $RunTask" }

if (-not $Task -and -not $Next) { throw "Specify -Task <ID> or -Next." }

$cliArgs = @($RunTask, $Workflow, "--run", $Run, "--executor", $Executor, "--format", $Format)
if ($Task) { $cliArgs += @("--task", $Task) }
if ($Next) { $cliArgs += "--next" }
if ($Fixture) { $cliArgs += @("--fixture", $Fixture) }
if ($ForceRerun) { $cliArgs += "--force-rerun" }

& $Python @cliArgs
exit $LASTEXITCODE
