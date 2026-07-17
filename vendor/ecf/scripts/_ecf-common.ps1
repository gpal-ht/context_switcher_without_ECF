<#
.SYNOPSIS
    Shared helpers for ECF PowerShell wrappers.

.DESCRIPTION
    Dot-source this file from a wrapper:

        . (Join-Path $PSScriptRoot '_ecf-common.ps1')

    It provides ECF-root resolution that works identically whether ECF is the
    canonical repository or is vendored inside another repository, and from any
    current working directory.

    IMPORTANT: the ECF root is resolved from $PSScriptRoot (the location of the
    scripts/ directory that owns these wrappers), NEVER from the outer Git
    repository root. When ECF is vendored, `git rev-parse --show-toplevel` would
    return the HOST repository's root, not ECF's — using it to locate ECF-owned
    files is the defect this helper fixes. The outer Git root is used only for
    optional, best-effort status reporting.
#>

Set-StrictMode -Version Latest

function Get-EcfRoot {
    <#
        Resolve the ECF root by walking up from this helper's own directory
        ($PSScriptRoot = <ECF>/scripts) until a directory containing both
        'tools/' and 'workflows/' is found. Independent of the current working
        directory and of any enclosing Git repository.
    #>
    $dir = $PSScriptRoot
    while ($dir) {
        if ((Test-Path (Join-Path $dir 'tools')) -and (Test-Path (Join-Path $dir 'workflows'))) {
            return (Resolve-Path $dir).Path
        }
        $parent = Split-Path -Parent $dir
        if (-not $parent -or $parent -eq $dir) { break }
        $dir = $parent
    }
    throw "Could not locate the ECF root from '$PSScriptRoot' (expected 'tools/' and 'workflows/')."
}

function Get-PythonExe {
    foreach ($name in @('python', 'python3', 'py')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    throw "Python 3 was not found on PATH."
}

function Get-OuterGitRoot {
    <#
        Best-effort outer Git repository root for OPTIONAL status reporting only.
        Never used to locate ECF-owned files. Returns $null when unavailable.
    #>
    param([string] $StartDir)
    if (-not $StartDir) { $StartDir = (Get-Location).Path }
    try {
        $root = (& git -C $StartDir rev-parse --show-toplevel 2>$null)
        if ($LASTEXITCODE -eq 0 -and $root) { return (Resolve-Path $root).Path }
    } catch { }
    return $null
}
