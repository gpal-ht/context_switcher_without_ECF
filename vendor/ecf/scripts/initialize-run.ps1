<#
.SYNOPSIS
    Initialize a schema-valid, planner-ready ECF runtime run (no task execution).

.DESCRIPTION
    Thin wrapper around tools/run_initializer/initialize_run.py. It converts a
    validated workflow + a Work Request + a Run identity into a runtime run that
    the validator, planner, runtime-state layer, recovery inspector, single-task
    runner, and provenance subsystem can consume without manual YAML authoring.

    It does NOT execute any task, invoke AI, or create task outputs / provenance
    records for unexecuted tasks.

    ECF root is resolved from this script's location (works canonical or
    vendored, from any working directory), never from the outer Git root.

.PARAMETER Workflow
    Path to the workflow specification (.md). Defaults to WF-REASON-0001.

.PARAMETER WorkRequest
    Path to the Work Request (.md). Required.

.PARAMETER RunId
    Conservative Run ID (RUN-...). Required.

.PARAMETER RunRoot
    Run root; the final run is <RunRoot>/<RunId>. Defaults to runtime/runs.

.PARAMETER RunDir
    Explicit final run directory (its leaf must equal -RunId). Alternative to -RunRoot.

.EXAMPLE
    .\scripts\initialize-run.ps1 -WorkRequest work_requests\WR-0001.md `
        -RunId RUN-REASON-WR0001-0001
#>
[CmdletBinding()]
param(
    [string] $Workflow,
    [Parameter(Mandatory = $true)] [string] $WorkRequest,
    [Parameter(Mandatory = $true)] [string] $RunId,
    [string] $RunRoot,
    [string] $RunDir,
    [ValidateSet("required", "legacy")] [string] $ProvenanceMode = "required",
    [string] $WorkRequestId,
    [switch] $Force,
    [ValidateSet("text", "json")] [string] $Format = "text"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot '_ecf-common.ps1')

# Do not write .pyc files into the (possibly read-only / vendored) tool tree.
$env:PYTHONDONTWRITEBYTECODE = "1"

$EcfRoot = Get-EcfRoot
$Python  = Get-PythonExe
$Init    = Join-Path $EcfRoot "tools/run_initializer/initialize_run.py"
if (-not (Test-Path $Init)) { throw "Initializer not found: $Init" }

if (-not $Workflow) {
    $Workflow = Join-Path $EcfRoot "workflows/reasoning/WF-REASON-0001-engineering-recommendation.md"
}
if (-not $RunRoot -and -not $RunDir) {
    $RunRoot = Join-Path $EcfRoot "runtime/runs"
}

$cliArgs = @($Init, $Workflow, "--work-request", $WorkRequest, "--run-id", $RunId,
             "--provenance-mode", $ProvenanceMode, "--format", $Format)
if ($RunRoot)       { $cliArgs += @("--run-root", $RunRoot) }
if ($RunDir)        { $cliArgs += @("--run-dir", $RunDir) }
if ($WorkRequestId) { $cliArgs += @("--work-request-id", $WorkRequestId) }
if ($Force)         { $cliArgs += "--force" }

& $Python @cliArgs
exit $LASTEXITCODE
