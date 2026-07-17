<#
.SYNOPSIS
    Validate every current ECF workflow listed in the Workflow Catalog.

.DESCRIPTION
    Read-only wrapper around tools/workflow_validator/validate_workflow.py.

    It discovers workflows from workflows/WORKFLOW_CATALOG.md whose status is one
    of: draft, review, approved, released. For each, it locates the specification
    file and runs the Python validator. It prints a concise per-workflow summary
    and returns a nonzero exit code if any workflow fails.

    This validates the ECF control plane. It does not execute engineering
    reasoning, invoke any AI, or modify any file.

.EXAMPLE
    .\scripts\validate-workflows.ps1

.EXAMPLE
    .\scripts\validate-workflows.ps1 -Format json
#>
[CmdletBinding()]
param(
    [ValidateSet("text", "json")]
    [string] $Format = "text"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot '_ecf-common.ps1')
$env:PYTHONDONTWRITEBYTECODE = "1"

$EcfRoot   = Get-EcfRoot
$Python    = Get-PythonExe
$Validator = Join-Path $EcfRoot "tools/workflow_validator/validate_workflow.py"
$Catalog   = Join-Path $EcfRoot "workflows/WORKFLOW_CATALOG.md"

if (-not (Test-Path $Validator)) { throw "Validator not found: $Validator" }
if (-not (Test-Path $Catalog))   { throw "Workflow catalog not found: $Catalog" }

$ApplicableStatuses = @("draft", "review", "approved", "released")

# Parse the catalog for '## <WF-ID> - ...' sections and their field tables.
$catalogLines = Get-Content -LiteralPath $Catalog
$workflows = @()
$currentId = $null
$fields = @{}

function Flush-Workflow {
    param($id, $fieldMap)
    if ($null -ne $id -and $fieldMap.ContainsKey("status")) {
        $script:workflows += [pscustomobject]@{
            Id     = $id
            Status = $fieldMap["status"]
            Spec   = $fieldMap["specification"]
        }
    }
}

foreach ($line in $catalogLines) {
    $sec = [regex]::Match($line, '^##\s+(WF-[A-Z]+-\d{4})\b')
    if ($sec.Success) {
        Flush-Workflow $currentId $fields
        $currentId = $sec.Groups[1].Value
        $fields = @{}
        continue
    }
    $row = [regex]::Match($line, '^\|\s*([A-Za-z ]+?)\s*\|\s*(.+?)\s*\|\s*$')
    if ($row.Success -and $currentId) {
        $key = $row.Groups[1].Value.Trim().ToLower()
        $val = $row.Groups[2].Value.Trim()
        $fields[$key] = $val
    }
}
Flush-Workflow $currentId $fields

# Resolve spec paths and filter by applicable status.
$targets = @()
foreach ($wf in $workflows) {
    if ($ApplicableStatuses -notcontains $wf.Status.ToLower()) { continue }
    $specPath = $null
    if ($wf.Spec) {
        # Extract a path from a possible markdown link: [text](path)
        $m = [regex]::Match($wf.Spec, '\(([^)]+\.md)\)')
        $rel = if ($m.Success) { $m.Groups[1].Value } else { $wf.Spec }
        $rel = $rel -replace '\.\./', ''
        $candidate = Join-Path $EcfRoot ("workflows/" + ($rel -replace '^workflows/', ''))
        if (Test-Path $candidate) { $specPath = (Resolve-Path $candidate).Path }
    }
    if (-not $specPath) {
        # Fall back to a recursive search by ID.
        $found = Get-ChildItem -Path (Join-Path $EcfRoot "workflows") -Recurse -Filter "*.md" -ErrorAction SilentlyContinue |
                 Where-Object { (Get-Content -LiteralPath $_.FullName -TotalCount 5) -match [regex]::Escape($wf.Id) } |
                 Select-Object -First 1
        if ($found) { $specPath = $found.FullName }
    }
    if ($specPath) {
        $targets += [pscustomobject]@{ Id = $wf.Id; Status = $wf.Status; Path = $specPath }
    } else {
        Write-Warning "Could not resolve a spec file for $($wf.Id) (status: $($wf.Status))."
    }
}

if ($targets.Count -eq 0) {
    Write-Warning "No applicable workflows found in the catalog."
    exit 0
}

Write-Host "ECF workflow validation - $($targets.Count) applicable workflow(s)"
Write-Host ""

$failures = 0
foreach ($t in $targets) {
    Write-Host ("== {0} ({1}) ==" -f $t.Id, $t.Status)
    & $Python $Validator $t.Path --format $Format
    $rc = $LASTEXITCODE
    if ($rc -eq 0) {
        Write-Host ("  {0}: VALID" -f $t.Id) -ForegroundColor Green
    } elseif ($rc -eq 1) {
        Write-Host ("  {0}: INVALID (validation errors)" -f $t.Id) -ForegroundColor Red
        $failures++
    } else {
        Write-Host ("  {0}: VALIDATOR ERROR (exit {1})" -f $t.Id, $rc) -ForegroundColor Red
        $failures++
    }
    Write-Host ""
}

Write-Host ("Summary: {0} validated, {1} failed." -f $targets.Count, $failures)
if ($failures -gt 0) { exit 1 } else { exit 0 }
