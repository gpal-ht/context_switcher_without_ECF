<#
.SYNOPSIS
    Builds the Context Switcher WinUI 3 GUI shell (ADR-0011).

.DESCRIPTION
    WinUI 3 resource (PRI) generation needs MSBuild tasks that ship with Visual
    Studio, not the bare .NET SDK, so `dotnet build` fails on the GUI project.
    This script locates the Visual Studio MSBuild and runs Restore then Build as
    SEPARATE invocations (a combined -t:Restore,Build evaluates the XAML targets
    with stale imports and fails).

    MSBuild resolution order:
      1. -MSBuildPath parameter
      2. CONTEXT_SWITCHER_MSBUILD environment variable
      3. vswhere (-latest -requires ...MSBuild)
      4. a small set of well-known install paths

.PARAMETER Configuration
    Debug (default) or Release.

.PARAMETER Run
    Launch the built executable after a successful build.
#>
[CmdletBinding()]
param(
    [ValidateSet("Debug", "Release")] [string] $Configuration = "Debug",
    [string] $MSBuildPath,
    [switch] $Run
)
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Project  = Join-Path $RepoRoot "src\App\ContextSwitcher.App\ContextSwitcher.App.csproj"
if (-not (Test-Path $Project)) { throw "GUI project not found: $Project" }

function Resolve-MSBuild {
    if ($MSBuildPath -and (Test-Path $MSBuildPath)) { return $MSBuildPath }
    if ($env:CONTEXT_SWITCHER_MSBUILD -and (Test-Path $env:CONTEXT_SWITCHER_MSBUILD)) { return $env:CONTEXT_SWITCHER_MSBUILD }

    $vswhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vswhere) {
        $installPath = & $vswhere -latest -prerelease -products * `
            -requires Microsoft.Component.MSBuild -property installationPath 2>$null | Select-Object -First 1
        if ($installPath) {
            foreach ($rel in @("MSBuild\Current\Bin\amd64\MSBuild.exe", "MSBuild\Current\Bin\MSBuild.exe")) {
                $candidate = Join-Path $installPath $rel
                if (Test-Path $candidate) { return $candidate }
            }
        }
    }
    foreach ($edition in @("Enterprise", "Professional", "Community", "BuildTools")) {
        foreach ($ver in @("18", "2022")) {
            foreach ($rel in @("MSBuild\Current\Bin\amd64\MSBuild.exe", "MSBuild\Current\Bin\MSBuild.exe")) {
                $candidate = Join-Path ${env:ProgramFiles} "Microsoft Visual Studio\$ver\$edition\$rel"
                if (Test-Path $candidate) { return $candidate }
            }
        }
    }
    throw "Could not locate Visual Studio MSBuild. Install Visual Studio (with the .NET Desktop / Windows App SDK workload) or pass -MSBuildPath. WinUI 3 cannot be built with 'dotnet build' alone (ADR-0011)."
}

$MSBuild = Resolve-MSBuild
Write-Host "Using MSBuild: $MSBuild"

$common = @("-p:Configuration=$Configuration", "-p:Platform=x64", "-p:RuntimeIdentifier=win-x64", "-nologo")

Write-Host "== Restore =="
& $MSBuild $Project -t:Restore @common -v:q
if ($LASTEXITCODE -ne 0) { throw "Restore failed ($LASTEXITCODE)." }

Write-Host "== Build =="
& $MSBuild $Project -t:Build @common -v:m
if ($LASTEXITCODE -ne 0) { throw "Build failed ($LASTEXITCODE)." }

$exe = Join-Path $RepoRoot "src\App\ContextSwitcher.App\bin\x64\$Configuration\net10.0-windows10.0.19041.0\win-x64\ContextSwitcher.App.exe"
if (Test-Path $exe) {
    Write-Host "Built: $exe" -ForegroundColor Green
} else {
    Write-Warning "Build reported success but the expected exe was not found at: $exe"
}

if ($Run -and (Test-Path $exe)) {
    Write-Host "Launching..."
    & $exe
}
