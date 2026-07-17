<#
.SYNOPSIS
    Thin Context Switcher adapter over the canonical ECF run initializer.

.DESCRIPTION
    Run initialization is owned entirely by canonical ECF
    (`vendor/ecf/tools/run_initializer/`, exposed via
    `vendor/ecf/scripts/initialize-run.ps1`). This adapter only:
      * resolves Context Switcher paths (ECF root, bundled workflow, runtime root);
      * supplies consumer-friendly defaults (WF-REASON-0001; runs under the
        project's gitignored `runtime/runs/`);
      * forwards the Work Request / Run identity;
      * preserves the canonical initializer's exit code.

    It does NOT construct state.yaml or manifest.yaml, import runtime-state models,
    duplicate schema logic, or derive task states. There is exactly one
    initialization implementation, and it lives in canonical ECF.

.PARAMETER RunId
    Conservative Run ID (RUN-...). The final run is <RunRoot>/<RunId>.

.PARAMETER WorkRequest
    Path to the Work Request (.md), staged as the run's read-only input.

.PARAMETER Workflow
    Optional workflow path; defaults to the bundled WF-REASON-0001.

.PARAMETER RunRoot
    Optional run root; defaults to the project's runtime/runs.

.PARAMETER Force
    Replace an existing run of the same Run ID.

.EXAMPLE
    .\scripts\initialize-ecf-run.ps1 -RunId RUN-VERIFY-WR0001-0001 `
        -WorkRequest work_requests\WR-0001-repository-integration-subsystem.md
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $RunId,
    [Parameter(Mandatory = $true)] [string] $WorkRequest,
    [string] $Workflow,
    [string] $RunRoot,
    [ValidateSet("required", "legacy")] [string] $ProvenanceMode = "required",
    [switch] $Force,
    [ValidateSet("text", "json")] [string] $Format = "text"
)
$ErrorActionPreference = "Stop"

# scripts/ lives at the Context Switcher root; ".." from here is that root.
$RepoRoot  = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

# ECF adapter boundary (ADR-0007): this operation exists only on the ecf
# backend. Standalone mode gets a typed UNSUPPORTED_CAPABILITY refusal; an
# explicitly configured but invalid ecf backend fails here, before any work.
. (Join-Path $PSScriptRoot "lib\Resolve-EngineeringBackend.ps1")
Assert-EcfBackend -RepoRoot $RepoRoot -Operation "ECF run initialization (initialize-ecf-run.ps1)"

$EcfRoot   = Join-Path $RepoRoot "vendor\ecf"
$Canonical = Join-Path $EcfRoot "scripts\initialize-run.ps1"
if (-not (Test-Path $Canonical)) {
    throw "Canonical ECF initializer not found: $Canonical. Refresh the bundle (scripts\bundle-ecf.ps1) first."
}

# Consumer-friendly defaults.
if (-not $RunRoot)  { $RunRoot  = Join-Path $RepoRoot "runtime\runs" }
if (-not $Workflow) { $Workflow = Join-Path $EcfRoot "workflows\reasoning\WF-REASON-0001-engineering-recommendation.md" }

# Delegate to the canonical initializer. Context Switcher constructs no runtime state.
$forward = @{
    Workflow       = $Workflow
    WorkRequest    = $WorkRequest
    RunId          = $RunId
    RunRoot        = $RunRoot
    ProvenanceMode = $ProvenanceMode
    Format         = $Format
}
if ($Force) { $forward.Force = $true }

& $Canonical @forward
exit $LASTEXITCODE
