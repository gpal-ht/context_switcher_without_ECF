# Bundles the canonical ECF dependency into Context Switcher's vendor/ecf tree.
#
# Source of truth: the canonical ECF repository (read-only for this project).
# This script performs a CLEAN copy — it wipes vendor/ecf and re-copies from the
# source — so re-running is semantically idempotent (only the VERSION bundle_date
# changes between runs).
#
# Do NOT hand-edit files under vendor/ecf; always refresh via this script.
#
# ECF adapter boundary (ADR-0007): the ECF checkout location is operator
# input — never a hardcoded sibling path. Supply -Source (or set the
# CONTEXT_SWITCHER_ECF_SOURCE environment variable). The source is validated
# as an ECF repository root BEFORE the existing bundle is touched. This script
# is deliberately NOT gated on engineering_backend=ecf: refreshing the bundle
# is how the ecf backend is installed in the first place.

[CmdletBinding()]
param(
    [string] $Source = $env:CONTEXT_SWITCHER_ECF_SOURCE
)
$ErrorActionPreference = "Stop"

if (-not $Source) {
    throw ("No ECF source specified. Pass -Source <path-to-ecf-checkout> or set " +
           "CONTEXT_SWITCHER_ECF_SOURCE. The ECF checkout location is machine-specific " +
           "and is never hardcoded (ADR-0007).")
}
if (!(Test-Path $Source -PathType Container)) {
    throw "ECF source not found or not a directory: $Source"
}
# Validate the source is genuinely an ECF repository root before wiping the
# existing bundle (guards against a mistyped path destroying vendor/ecf).
$Source = (Resolve-Path $Source).Path
if (!(Test-Path (Join-Path $Source "ecf-version.yaml"))) {
    throw ("'$Source' does not look like an ECF repository root " +
           "(missing ecf-version.yaml). Refusing to bundle from it.")
}

# scripts/ lives at the Context Switcher root; the target is always this
# repository's own vendor/ecf tree.
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Target   = Join-Path $RepoRoot "vendor\ecf"

# --- Hygiene: excluded development / transient artifacts -----------------------
# Excluded DIRECTORIES, matched by EXACT folder name at any depth. These are build
# or tooling byproducts, never canonical framework assets. Because matching is by
# exact name, canonical directories whose names merely resemble generated output
# (e.g. 'runtime_schemas') are NOT affected by 'runtime'.
$ExcludeDirs = @(
    ".git",             # VCS metadata
    ".claude",          # Claude configuration — never a canonical framework asset
    ".vs", ".vscode",   # IDE settings
    "__pycache__",      # Python bytecode cache
    ".pytest_cache",    # pytest cache
    ".mypy_cache",      # mypy cache
    "htmlcov",          # coverage HTML report
    ".venv", "venv",    # virtual environments
    "build", "dist",    # packaging output
    "generated",        # generated output
    "runtime",          # runtime state output
    "cache",            # transient cache
    "logs"              # log output
)

# Excluded FILES, matched by pattern. Transient artifacts only.
$ExcludeFiles = @("*.tmp", "*.log", "*.pyc", "*.pyo", ".coverage")

# Canonical assets intentionally PRESERVED (never excluded): acceptance_tests/ and
# their committed fixtures, deterministic reports, tasks/, workflows/,
# runtime_schemas/, tools/, consumer-facing scripts/, and the nested bundled EKB
# under vendor/engineering_kb/ (including its canonical decision_guide reports).

Remove-Item $Target -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $Target | Out-Null

robocopy $Source $Target /E /XD $ExcludeDirs /XF $ExcludeFiles | Out-Null

# --- Provenance metadata (NO local machine paths) -----------------------------
# 'source' records the canonical repository URL, never the local clone path.
$EcfRemote = (git -C $Source remote get-url origin 2>$null)
if (-not $EcfRemote) { $EcfRemote = "unknown" }
$EcfCommit = (git -C $Source rev-parse HEAD 2>$null)

# Canonical ECF release (package) version — authoritative source is the ECF
# repo's own package.json version (mirrored in VERSION). No hardcoded stub.
$EcfVersion = "unknown"
$EcfPkg = Join-Path $Source "package.json"
if (Test-Path $EcfPkg) {
    try { $EcfVersion = (Get-Content $EcfPkg -Raw | ConvertFrom-Json).version } catch { }
}
if ($EcfVersion -eq "unknown") {
    $EcfVersionFile = Join-Path $Source "VERSION"
    if (Test-Path $EcfVersionFile) { $EcfVersion = (Get-Content $EcfVersionFile -TotalCount 1).Trim() }
}

# Released tag pointing at the bundled ECF commit (exact-pin provenance), if any.
$EcfTag = ""
try { $EcfTag = (git -C $Source describe --tags --exact-match HEAD 2>$null); if (-not $EcfTag) { $EcfTag = "" } } catch { }

# Nested EKB identity, read from the source's bundled EKB VERSION so the project
# can determine both ECF and EKB versions from vendor/ecf/VERSION alone.
$EkbRemote = ""; $EkbCommit = ""; $EkbVersion = ""; $EkbTag = ""
$EkbVersionFile = Join-Path $Source "vendor\engineering_kb\VERSION"
if (Test-Path $EkbVersionFile) {
    foreach ($line in Get-Content $EkbVersionFile) {
        if     ($line -match '^\s*source:\s*(.+)$')        { $EkbRemote  = $Matches[1].Trim() }
        elseif ($line -match '^\s*source_commit:\s*(.+)$') { $EkbCommit  = $Matches[1].Trim() }
        elseif ($line -match '^\s*source_tag:\s*(.+)$')    { $EkbTag     = $Matches[1].Trim() }
        elseif ($line -match '^\s*version:\s*(.+)$')       { $EkbVersion = $Matches[1].Trim() }
    }
}

$Date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

@"
dependency: ecf
version: $EcfVersion
source: $EcfRemote
source_commit: $EcfCommit
source_tag: $EcfTag
bundle_date: $Date
status: released
ekb_source: $EkbRemote
ekb_version: $EkbVersion
ekb_commit: $EkbCommit
ekb_tag: $EkbTag
"@ | Set-Content "$Target\VERSION"

Write-Host "Bundled ECF into Context Switcher."
Write-Host "  ECF version: $EcfVersion  tag: $EcfTag"
Write-Host "  ECF commit:  $EcfCommit"
Write-Host "  EKB version: $EkbVersion  tag: $EkbTag"
Write-Host "  EKB commit:  $EkbCommit"
