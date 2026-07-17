<#
.SYNOPSIS
    Inspect an ECF runtime run directory for consistency (read-only by default).

.DESCRIPTION
    Wraps tools/runtime_state/recovery.py. It inspects run state, manifest, lock,
    staging, and recovery conditions and prints a concise consistency summary.

    Default behavior is READ-ONLY: no repair is performed. Repairs happen only
    when -Apply is passed (and stale-lock removal only with -AllowLockRemoval).

    Exit codes: 0 consistent, 1 inconsistent, 2 unrecoverable / cannot inspect.

.PARAMETER RunDir
    Path to the runtime run directory (runtime/runs/<RUN_ID> or a fixture).

.EXAMPLE
    .\scripts\inspect-runtime-state.ps1 -RunDir runtime\runs\RUN-REASON-20260710-0001

.EXAMPLE
    .\scripts\inspect-runtime-state.ps1 -RunDir <dir> -Apply
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $RunDir,
    [ValidateSet("text", "json")]
    [string] $Format = "text",
    [double] $Ttl = 3600,
    [switch] $Apply,
    [switch] $AllowLockRemoval
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot '_ecf-common.ps1')
$env:PYTHONDONTWRITEBYTECODE = "1"

$EcfRoot  = Get-EcfRoot
$Python   = Get-PythonExe
$Recovery = Join-Path $EcfRoot "tools/runtime_state/recovery.py"
if (-not (Test-Path $Recovery)) { throw "Inspector not found: $Recovery" }

$cliArgs = @($Recovery, $RunDir, "--format", $Format, "--ttl", $Ttl)
if ($Apply) { $cliArgs += "--apply" }
if ($AllowLockRemoval) { $cliArgs += "--allow-lock-removal" }

& $Python @cliArgs
exit $LASTEXITCODE
