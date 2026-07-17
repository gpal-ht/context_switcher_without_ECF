<#
.SYNOPSIS
    Flatten the contents of a folder into a single text file.

.DESCRIPTION
    Walks a source folder recursively and concatenates every text file into one
    output file. Each file is preceded by a header banner showing its path
    relative to the source, so the result stays readable and traceable.

    Binary files are detected (via a NUL-byte scan) and skipped by default so the
    output stays clean. The output file is never included in itself.

.PARAMETER Source
    Folder whose contents should be flattened. Defaults to the current directory.

.PARAMETER Output
    Path of the single text file to write. Defaults to ".\flattened.txt".

.PARAMETER Exclude
    Directory names to skip anywhere in the tree (e.g. .git, node_modules).

.PARAMETER Include
    Optional file globs to restrict to (e.g. *.md, *.ps1). Defaults to all files.

.PARAMETER IncludeBinary
    Include binary files as well (their raw bytes are skipped; only a note is written).

.EXAMPLE
    .\scripts\flatten-folder.ps1 -Source .\knowledge -Output .\knowledge.txt

.EXAMPLE
    .\scripts\flatten-folder.ps1 -Source . -Include *.md -Exclude .git,vendor
#>
[CmdletBinding()]
param(
    [string]   $Source        = ".",
    [string]   $Output        = ".\flattened.txt",
    [string[]] $Exclude       = @(".git", ".vs", ".vscode", "node_modules", "__pycache__"),
    [string[]] $Include       = @("*"),
    [switch]   $IncludeBinary
)

$ErrorActionPreference = "Stop"

if (!(Test-Path -LiteralPath $Source -PathType Container)) {
    throw "Source folder not found: $Source"
}

$SourceRoot = (Resolve-Path -LiteralPath $Source).Path
if ([System.IO.Path]::IsPathRooted($Output)) {
    $OutputFull = [System.IO.Path]::GetFullPath($Output)
} else {
    $OutputFull = [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $Output))
}

# Ensure the output directory exists.
$OutputDir = Split-Path -Parent $OutputFull
if ($OutputDir -and !(Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
}

function Test-IsBinary {
    param([string] $Path)
    # Read up to 8000 bytes; a NUL byte is a strong signal of binary content.
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $limit = [Math]::Min($bytes.Length, 8000)
    for ($i = 0; $i -lt $limit; $i++) {
        if ($bytes[$i] -eq 0) { return $true }
    }
    return $false
}

# NOTE: -Include is matched by hand below rather than passed to Get-ChildItem,
# because -Include is silently ignored when combined with -LiteralPath.
$files = Get-ChildItem -LiteralPath $SourceRoot -Recurse -File |
    Where-Object {
        $full = $_.FullName
        # Skip the output file itself.
        if ($full -eq $OutputFull) { return $false }
        # Skip anything under an excluded directory.
        $rel = $full.Substring($SourceRoot.Length).TrimStart('\', '/')
        $segments = $rel -split '[\\/]'
        foreach ($seg in $segments) {
            if ($Exclude -contains $seg) { return $false }
        }
        # Keep only files whose name matches one of the -Include globs.
        foreach ($glob in $Include) {
            if ($_.Name -like $glob) { return $true }
        }
        return $false
    } |
    Sort-Object FullName

$sb        = [System.Text.StringBuilder]::new()
$written   = 0
$skipped   = 0

foreach ($file in $files) {
    $rel = $file.FullName.Substring($SourceRoot.Length).TrimStart('\', '/')

    if (-not $IncludeBinary -and (Test-IsBinary $file.FullName)) {
        $skipped++
        continue
    }

    [void]$sb.AppendLine("===== BEGIN $rel =====")
    if (Test-IsBinary $file.FullName) {
        [void]$sb.AppendLine("[binary file - $($file.Length) bytes - content omitted]")
    } else {
        [void]$sb.AppendLine([System.IO.File]::ReadAllText($file.FullName))
    }
    [void]$sb.AppendLine("===== END $rel =====")
    [void]$sb.AppendLine("")
    $written++
}

Set-Content -LiteralPath $OutputFull -Value $sb.ToString() -Encoding utf8

Write-Host "Flattened $written file(s) into $OutputFull ($skipped binary file(s) skipped)."
