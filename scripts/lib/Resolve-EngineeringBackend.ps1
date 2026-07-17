<#
.SYNOPSIS
    Engineering-backend resolver — PowerShell binding of the Port-1 contract.

.DESCRIPTION
    Canonical contract: scripts/engineering_backend.py (ADR-0007). The bindings
    are kept in agreement by acceptance_tests/check_backend_boundary.sh.

    Resolution order: CONTEXT_SWITCHER_ENGINEERING_BACKEND environment variable
    -> config/engineering-backend.yaml -> default "standalone".

    Resolve-EngineeringBackend -RepoRoot <root> returns "standalone" or "ecf".
    Selecting ecf validates bundle availability and compatibility; a missing or
    incompatible bundle THROWS (hard configuration failure — never a silent
    fallback to standalone). Unknown values throw a validation error.

    Assert-EcfBackend -RepoRoot <root> -Operation <name> is the guard used by
    the ECF adapter scripts: it throws a typed UNSUPPORTED_CAPABILITY error
    when the active backend is standalone.
#>

Set-StrictMode -Version 2

$script:CsBackendEnvVar = "CONTEXT_SWITCHER_ENGINEERING_BACKEND"
$script:CsBackendConfig = "config\engineering-backend.yaml"
$script:CsSupportedEcfSchemaLine = "0.1"

function Get-CsMetadataValue {
    # LF/CRLF-safe `key: value` reader; $null when file or key is absent.
    param([string] $Key, [string] $File)
    if (-not (Test-Path $File)) { return $null }
    foreach ($line in Get-Content $File) {
        $t = $line.Trim()
        if ($t -eq "" -or $t.StartsWith("#")) { continue }
        if ($t -match ("^" + [regex]::Escape($Key) + ":\s*(.*)$")) {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $null
}

function Test-CsEcfBundle {
    # Throws unless vendor/ecf satisfies the compatibility policy (ADR-0007).
    param([Parameter(Mandatory = $true)][string] $RepoRoot)
    $ecf = Join-Path $RepoRoot "vendor\ecf"
    if (-not (Test-Path $ecf -PathType Container)) {
        throw ("engineering_backend=ecf was requested but vendor\ecf is missing. " +
               "Refresh the bundle (scripts\bundle-ecf.ps1 -Source <ecf-repo>) or select " +
               "the standalone backend ($script:CsBackendEnvVar=standalone or $script:CsBackendConfig).")
    }
    $schema = Get-CsMetadataValue -Key "schema_version" -File (Join-Path $ecf "ecf-version.yaml")
    $line = $script:CsSupportedEcfSchemaLine
    if (-not $schema -or -not ($schema -eq $line -or $schema.StartsWith("$line."))) {
        $shown = if ($schema) { $schema } else { "missing" }
        throw ("engineering_backend=ecf: bundled ECF schema_version '$shown' is not on the " +
               "supported line '$line' (release/COMPATIBILITY.md).")
    }
    $commit = Get-CsMetadataValue -Key "source_commit" -File (Join-Path $ecf "VERSION")
    if (-not $commit -or $commit -notmatch '^[0-9a-f]{40}$') {
        throw ("engineering_backend=ecf: vendor\ecf\VERSION has no valid 40-hex source_commit " +
               "- bundle identity is unverifiable. Refresh the bundle (scripts\bundle-ecf.ps1).")
    }
}

function Resolve-EngineeringBackend {
    param([Parameter(Mandatory = $true)][string] $RepoRoot)
    $value = [Environment]::GetEnvironmentVariable($script:CsBackendEnvVar)
    $source = "environment variable $script:CsBackendEnvVar"
    if (-not $value) {
        $value = Get-CsMetadataValue -Key "engineering_backend" `
                                     -File (Join-Path $RepoRoot $script:CsBackendConfig)
        $source = $script:CsBackendConfig
    }
    if (-not $value) { return "standalone" }
    switch ($value) {
        "standalone" { return "standalone" }
        "ecf" {
            Test-CsEcfBundle -RepoRoot $RepoRoot
            return "ecf"
        }
        default {
            throw ("invalid engineering_backend '$value' (from $source); " +
                   "allowed values: standalone, ecf")
        }
    }
}

function Assert-EcfBackend {
    # Guard for the ECF adapter scripts (Port 2). Standalone -> typed refusal.
    param(
        [Parameter(Mandatory = $true)][string] $RepoRoot,
        [Parameter(Mandatory = $true)][string] $Operation
    )
    $backend = Resolve-EngineeringBackend -RepoRoot $RepoRoot
    if ($backend -ne "ecf") {
        throw ("UNSUPPORTED_CAPABILITY: '$Operation' requires the ecf engineering backend; " +
               "the active backend is '$backend'. Context Switcher makes no ECF guarantees in " +
               "standalone mode. To enable: set engineering_backend: ecf in " +
               "$script:CsBackendConfig (or $script:CsBackendEnvVar=ecf) with a valid " +
               "vendor\ecf bundle. See docs/engineering/ENGINEERING_BACKENDS.md.")
    }
}
