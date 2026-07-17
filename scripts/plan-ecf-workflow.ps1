<#
.SYNOPSIS
    Read-only ECF planner: which tasks are runnable now? Resolves the bundled ECF
    root correctly (vendor/ecf), not the outer Context Switcher git root.

.PARAMETER Run
    Optional initialized run directory. Without it, shows the fresh frontier.
#>
[CmdletBinding()]
param(
    [string] $Run,
    [string] $Workflow,
    [ValidateSet("text", "json")] [string] $Format = "text"
)
$ErrorActionPreference = "Stop"

# Do not write .pyc into the vendored (read-only) ECF tree.
$env:PYTHONDONTWRITEBYTECODE = "1"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

# ECF adapter boundary (ADR-0007): ecf backend only; standalone refuses.
. (Join-Path $PSScriptRoot "lib\Resolve-EngineeringBackend.ps1")
Assert-EcfBackend -RepoRoot $RepoRoot -Operation "ECF workflow planning (plan-ecf-workflow.ps1)"

$EcfRoot  = Join-Path $RepoRoot "vendor\ecf"
$Planner  = Join-Path $EcfRoot "tools\workflow_planner\plan_workflow.py"
if (-not $Workflow) {
    $Workflow = Join-Path $EcfRoot "workflows\reasoning\WF-REASON-0001-engineering-recommendation.md"
}
foreach ($p in @($Planner, $Workflow)) {
    if (-not (Test-Path $p)) { throw "Required ECF path missing: $p  (refresh the bundle)." }
}
$Python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Python) { throw "Python 3 was not found on PATH." }

$argsList = @($Planner, $Workflow, "--format", $Format)
if ($Run) {
    if (-not (Test-Path $Run)) { throw "Run directory not found: $Run" }
    $argsList += @("--run", (Resolve-Path $Run).Path)
}
& $Python @argsList
exit $LASTEXITCODE
