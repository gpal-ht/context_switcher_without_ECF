<#
.SYNOPSIS
    Builds a signed MSIX package for the Context Switcher WinUI 3 app (ADR-0020).

.DESCRIPTION
    Produces an installable **sideload / development** MSIX, signed with a
    self-signed development certificate. The certificate (and its .pfx) are
    generated on demand under the gitignored `.local/certs/` directory and are
    NEVER committed. Store/production distribution requires a real code-signing
    identity and is out of scope here.

    Steps:
      1. Resolve Visual Studio MSBuild (WinUI PRI/MSIX tasks need it).
      2. Ensure a self-signed dev cert (CN=ContextSwitcher Dev, matching the
         manifest Publisher) exists; export a password-protected .pfx + a public
         .cer for trust import.
      3. Restore, then build the app as a packaged MSIX (BuildMsix=true) and sign
         it with the dev cert.
      4. Report the produced .msix and how to install it.

    The unpackaged dev-run path (scripts/build-gui.ps1) is unaffected.

.PARAMETER Configuration
    Release (default) or Debug.

.PARAMETER MSBuildPath
    Explicit MSBuild.exe path (else vswhere / well-known locations).

.PARAMETER Install
    After building, import the dev cert into the Trusted People store and
    install the MSIX (requires an elevated/allowed session).
#>
[CmdletBinding()]
param(
    [ValidateSet("Release", "Debug")] [string] $Configuration = "Release",
    [string] $MSBuildPath,
    [switch] $Install
)
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Project  = Join-Path $RepoRoot "src\App\ContextSwitcher.App\ContextSwitcher.App.csproj"
if (-not (Test-Path $Project)) { throw "App project not found: $Project" }

# Dev signing material lives in a gitignored local directory — never committed.
$CertDir  = Join-Path $RepoRoot ".local\certs"
$PfxPath  = Join-Path $CertDir "ContextSwitcher-Dev.pfx"
$CerPath  = Join-Path $CertDir "ContextSwitcher-Dev.cer"
$Subject  = "CN=ContextSwitcher Dev"           # must match Package.appxmanifest Publisher
$PfxPassword = "contextswitcher-dev"           # throwaway dev-only password (not a secret)
New-Item -ItemType Directory -Force -Path $CertDir | Out-Null

function Resolve-SignTool {
    # signtool ships with Microsoft.Windows.SDK.BuildTools (pulled by WindowsAppSDK).
    $roots = @(
        (Join-Path $env:USERPROFILE ".nuget\packages\microsoft.windows.sdk.buildtools"),
        (Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Shared\NuGetPackages\microsoft.windows.sdk.buildtools")
    )
    foreach ($root in $roots) {
        if (Test-Path $root) {
            $tool = Get-ChildItem -Path $root -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
                    Where-Object { $_.FullName -match "\\x64\\" } |
                    Sort-Object FullName | Select-Object -Last 1
            if ($tool) { return $tool.FullName }
        }
    }
    throw "Could not locate signtool.exe (Microsoft.Windows.SDK.BuildTools). Restore the app project first."
}

function Resolve-MSBuild {
    if ($MSBuildPath -and (Test-Path $MSBuildPath)) { return $MSBuildPath }
    if ($env:CONTEXT_SWITCHER_MSBUILD -and (Test-Path $env:CONTEXT_SWITCHER_MSBUILD)) { return $env:CONTEXT_SWITCHER_MSBUILD }
    $vswhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vswhere) {
        $installPath = & $vswhere -latest -prerelease -products * `
            -requires Microsoft.Component.MSBuild -property installationPath 2>$null | Select-Object -First 1
        if ($installPath) {
            foreach ($rel in @("MSBuild\Current\Bin\amd64\MSBuild.exe", "MSBuild\Current\Bin\MSBuild.exe")) {
                $c = Join-Path $installPath $rel; if (Test-Path $c) { return $c }
            }
        }
    }
    foreach ($edition in @("Enterprise", "Professional", "Community", "BuildTools")) {
        foreach ($ver in @("18", "2022")) {
            foreach ($rel in @("MSBuild\Current\Bin\amd64\MSBuild.exe", "MSBuild\Current\Bin\MSBuild.exe")) {
                $c = Join-Path ${env:ProgramFiles} "Microsoft Visual Studio\$ver\$edition\$rel"
                if (Test-Path $c) { return $c }
            }
        }
    }
    throw "Could not locate Visual Studio MSBuild. Install Visual Studio (Windows App SDK workload) or pass -MSBuildPath."
}

function Ensure-DevCertificate {
    if (Test-Path $PfxPath) { Write-Host "Using existing dev certificate: $PfxPath"; return }
    Write-Host "Generating self-signed development certificate ($Subject)..."
    $cert = New-SelfSignedCertificate `
        -Type CodeSigningCert -Subject $Subject `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -KeyUsage DigitalSignature -FriendlyName "ContextSwitcher Dev" `
        -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
    $securePwd = ConvertTo-SecureString -String $PfxPassword -Force -AsPlainText
    Export-PfxCertificate -Cert $cert -FilePath $PfxPath -Password $securePwd | Out-Null
    Export-Certificate  -Cert $cert -FilePath $CerPath | Out-Null
    # Remove from the personal store; the build reads the .pfx directly.
    Remove-Item ("Cert:\CurrentUser\My\" + $cert.Thumbprint) -Force
    Write-Host "  wrote $PfxPath and $CerPath"
}

$MSBuild = Resolve-MSBuild
Write-Host "Using MSBuild: $MSBuild"
Ensure-DevCertificate

$common = @(
    "-p:Configuration=$Configuration", "-p:Platform=x64", "-p:RuntimeIdentifier=win-x64",
    "-p:BuildMsix=true", "-nologo"
)

Write-Host "== Restore =="
& $MSBuild $Project -t:Restore @common -v:q
if ($LASTEXITCODE -ne 0) { throw "Restore failed ($LASTEXITCODE)." }

# Build the package UNSIGNED, then sign with signtool (which handles a
# password-protected .pfx reliably; MSBuild's in-build signing does not).
Write-Host "== Build + package (unsigned) =="
& $MSBuild $Project -t:Build @common -v:m `
    -p:GenerateAppxPackageOnBuild=true `
    -p:AppxBundle=Never `
    -p:UapAppxPackageBuildMode=SideloadOnly `
    -p:AppxPackageSigningEnabled=false
if ($LASTEXITCODE -ne 0) { throw "Package build failed ($LASTEXITCODE)." }

$msix = Get-ChildItem -Path (Split-Path $Project) -Recurse -Filter *.msix -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime | Select-Object -Last 1
if (-not $msix) { throw "Build reported success but no .msix was found." }

Write-Host "== Sign =="
$SignTool = Resolve-SignTool
Write-Host "Using signtool: $SignTool"
& $SignTool sign /fd SHA256 /f $PfxPath /p $PfxPassword $msix.FullName
if ($LASTEXITCODE -ne 0) { throw "Signing failed ($LASTEXITCODE)." }

Write-Host ""
Write-Host "MSIX built: $($msix.FullName)" -ForegroundColor Green
Write-Host "Public cert (import to Local Machine > Trusted People to trust it): $CerPath"
Write-Host ""
Write-Host "To install (elevated PowerShell):"
Write-Host "  Import-Certificate -FilePath '$CerPath' -CertStoreLocation Cert:\LocalMachine\TrustedPeople"
Write-Host "  Add-AppxPackage -Path '$($msix.FullName)'"

if ($Install) {
    Write-Host "== Installing =="
    Import-Certificate -FilePath $CerPath -CertStoreLocation Cert:\LocalMachine\TrustedPeople | Out-Null
    Add-AppxPackage -Path $msix.FullName
    Write-Host "Installed. Launch 'Context Switcher' from the Start menu."
}
