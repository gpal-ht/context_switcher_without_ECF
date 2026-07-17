# Bundles the canonical Engineering Knowledge Base (EKB) into ECF as a
# read-only vendored dependency under vendor/engineering_kb/.
#
# READ-ONLY toward the canonical source: this script only reads $Source
# (robocopy + git rev-parse). It never writes to the canonical EKB repository.
#
# Determinism: the set of excluded development/generated artifacts below is
# fixed and documented so repeated runs copy the same canonical content. The
# only volatile field written is VERSION's bundle_date (provenance metadata,
# not KB content); KB content is byte-identical across runs of an unchanged
# source commit.

$ErrorActionPreference = "Stop"

$Source = "C:\Dev\engineering_kb"
$Target = "C:\Dev\ecf\vendor\engineering_kb"

if (!(Test-Path $Source)) {
    throw "Source not found: $Source"
}

Remove-Item $Target -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $Target | Out-Null

# ---------------------------------------------------------------------------
# Excluded DIRECTORIES (/XD) — development or generated, never canonical.
# Matched by name at any depth in the source tree.
#
#   .git            version-control metadata
#   generated       transient, non-canonical query outputs (e.g. packages/)
#   runtime         execution/runtime scratch
#   cache, logs     transient tool output
#   .vs, .vscode    editor state
#   __pycache__     CPython bytecode caches
#   .pytest_cache   pytest run cache
#   .mypy_cache     mypy type-check cache
#   htmlcov         coverage.py HTML report (transient tool output)
#   .venv, venv     local virtual environments
#   build, dist     packaging output
#
# DELIBERATELY NOT EXCLUDED: the canonical "coverage" directory. Its Markdown
# reports (knowledge_coverage.md, centrality_report.md) are version-controlled,
# deterministic, committed EKB source per coverage/GENERATED.md. Excluding only
# transient coverage-tool output (htmlcov/, the .coverage data file below)
# preserves those canonical reports.
# ---------------------------------------------------------------------------
$ExcludeDirs = @(
    ".git",
    ".claude",
    "generated",
    "runtime",
    "cache",
    "logs",
    ".vs",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "htmlcov",
    ".venv",
    "venv",
    "build",
    "dist"
)

# ---------------------------------------------------------------------------
# Excluded FILES (/XF) — development or generated, never canonical.
#
#   *.pyc, *.pyo, *.pyd   compiled/optimized Python bytecode
#   .coverage             coverage.py data file (NOT the coverage/ directory)
#   *.tmp, *.log          transient scratch
# ---------------------------------------------------------------------------
$ExcludeFiles = @(
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".coverage",
    "*.tmp",
    "*.log"
)

robocopy $Source $Target /E /XD $ExcludeDirs /XF $ExcludeFiles | Out-Null

# robocopy uses bit-flag exit codes: < 8 is success (files copied / no change);
# >= 8 indicates at least one failure.
if ($LASTEXITCODE -ge 8) {
    throw "robocopy failed with exit code $LASTEXITCODE"
}

$Commit = git -C $Source rev-parse HEAD

# Record a non-machine-specific source identifier. Prefer the canonical repo's
# remote URL; fall back to the logical dependency name when the only "remote"
# is a local filesystem path (which must not be embedded in the bundle).
$SourceRef = "engineering_kb"
try {
    $Remote = (git -C $Source config --get remote.origin.url 2>$null)
    if ($Remote -and $Remote -notmatch '^[A-Za-z]:[\\/]' -and $Remote -notmatch '^[\\/]' -and $Remote -notmatch '^file:') {
        $SourceRef = $Remote
    }
} catch { }

$Date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Record the canonical EKB release version (authoritative source: the EKB
# repo's own package.json version, mirrored in VERSION). No hardcoded stub.
$EkbVersion = "unknown"
$EkbPkg = Join-Path $Source "package.json"
if (Test-Path $EkbPkg) {
    try { $EkbVersion = (Get-Content $EkbPkg -Raw | ConvertFrom-Json).version } catch { }
}
if ($EkbVersion -eq "unknown") {
    $EkbVersionFile = Join-Path $Source "VERSION"
    if (Test-Path $EkbVersionFile) { $EkbVersion = (Get-Content $EkbVersionFile -TotalCount 1).Trim() }
}

# Record the released tag pointing at the bundled commit, when the source is
# checked out exactly at a tag (exact-pin provenance). Empty otherwise.
$SourceTag = ""
try {
    $SourceTag = (git -C $Source describe --tags --exact-match HEAD 2>$null)
    if (-not $SourceTag) { $SourceTag = "" }
} catch { }

@"
dependency: engineering_kb
version: $EkbVersion
source: $SourceRef
source_commit: $Commit
source_tag: $SourceTag
bundle_date: $Date
status: released
"@ | Set-Content "$Target\VERSION"

Write-Host "Bundled engineering_kb into ECF."
Write-Host "  version:       $EkbVersion"
Write-Host "  source_commit: $Commit"
Write-Host "  source_tag:    $SourceTag"
Write-Host "  source:        $SourceRef"
