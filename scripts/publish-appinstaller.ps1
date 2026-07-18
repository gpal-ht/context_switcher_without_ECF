<#
.SYNOPSIS
    Publishes the packaged MSIX + .appinstaller (+ public dev cert) to the
    GitHub Pages `gh-pages` branch for App Installer auto-update (ADR-0023).

.DESCRIPTION
    `scripts/package-msix.ps1` produces a signed `.msix` and an `.appinstaller`
    whose URIs point at a hosted location. This script takes the most recent
    such artifacts and stages them onto the `gh-pages` branch so GitHub Pages
    serves them at exactly those URIs.

    It works in an isolated worktree under the gitignored `.local/gh-pages`
    directory, so the current `develop` working tree is never touched. The
    `gh-pages` branch is created as an orphan (no source history) the first
    time; afterwards it is reused. Older `.msix` versions already on the branch
    are preserved (so previously-installed clients keep resolving), while the
    `.appinstaller` and landing page are refreshed to the latest build.

    SAFETY: publishing is public. By default this only prepares a LOCAL commit
    on `gh-pages` and prints the push command. Pass -Push to actually push.

    Only the PUBLIC certificate (.cer) is published - never the .pfx.

.PARAMETER Configuration
    Which build output to publish from (Release default, matching package-msix).

.PARAMETER Branch
    Target branch for GitHub Pages (default: gh-pages).

.PARAMETER Push
    Push the prepared commit to origin/<Branch>. Omitted = prepare locally only.
#>
[CmdletBinding()]
param(
    [ValidateSet("Release", "Debug")] [string] $Configuration = "Release",
    [string] $Branch = "gh-pages",
    [switch] $Push
)
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

# --- 1. Locate the newest packaged artifacts --------------------------------
$AppBin = Join-Path $RepoRoot "src\App\ContextSwitcher.App\bin\x64\$Configuration"
if (-not (Test-Path $AppBin)) {
    throw "No $Configuration build output found. Run scripts/package-msix.ps1 first."
}
$AppInstaller = Get-ChildItem -Path $AppBin -Recurse -Filter *.appinstaller -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime | Select-Object -Last 1
if (-not $AppInstaller) {
    throw "No .appinstaller found under $AppBin. Run scripts/package-msix.ps1 (with -AppInstallerBaseUrl) first."
}
$PkgDir = $AppInstaller.DirectoryName
$Msix = Get-ChildItem -Path $PkgDir -Filter *.msix | Sort-Object LastWriteTime | Select-Object -Last 1
if (-not $Msix) { throw "No .msix alongside the .appinstaller in $PkgDir." }

$Cer = Join-Path $RepoRoot ".local\certs\ContextSwitcher-Dev.cer"
if (-not (Test-Path $Cer)) {
    throw "Public dev cert not found: $Cer. Run scripts/package-msix.ps1 first."
}

# Read identity + hosting URI straight from the .appinstaller so the published
# site and the package never disagree.
[xml]$Ai = Get-Content $AppInstaller.FullName
$SelfUri = $Ai.AppInstaller.Uri
$Version = $Ai.AppInstaller.MainPackage.Version
if ($SelfUri -like "*REPLACE-WITH-YOUR-HOST*") {
    throw "The .appinstaller still uses the PLACEHOLDER host URL. Repackage first: " +
          "scripts/package-msix.ps1 -AppInstallerBaseUrl https://<user>.github.io/<repo>"
}
$BaseUrl = ($SelfUri -replace "/[^/]+$", "")   # strip the trailing /ContextSwitcher.appinstaller

Write-Host "Publishing Context Switcher $Version" -ForegroundColor Cyan
Write-Host "  msix:         $($Msix.Name)"
Write-Host "  appinstaller: $($AppInstaller.Name)  ->  $SelfUri"
Write-Host "  base URL:     $BaseUrl"

# --- 2. Prepare the gh-pages worktree ---------------------------------------
$Wt = Join-Path $RepoRoot ".local\gh-pages"
git -C $RepoRoot worktree prune
if (Test-Path $Wt) {
    git -C $RepoRoot worktree remove --force $Wt 2>$null
    if (Test-Path $Wt) { Remove-Item -Recurse -Force $Wt }
}

$ExistsLocal = [bool](git -C $RepoRoot branch --list $Branch)
$ExistsRemote = $false
try { $ExistsRemote = [bool](git -C $RepoRoot ls-remote --heads origin $Branch 2>$null) } catch { }

if ($ExistsLocal) {
    Write-Host "Reusing existing local '$Branch' branch."
    git -C $RepoRoot worktree add $Wt $Branch | Out-Null
} elseif ($ExistsRemote) {
    Write-Host "Checking out existing origin/$Branch."
    git -C $RepoRoot worktree add -B $Branch $Wt "origin/$Branch" | Out-Null
} else {
    Write-Host "Creating a fresh orphan '$Branch' branch."
    git -C $RepoRoot worktree add --detach $Wt HEAD | Out-Null
    git -C $Wt checkout --orphan $Branch | Out-Null
    git -C $Wt rm -rfq --ignore-unmatch . 2>$null
    git -C $Wt clean -fdxq
}

# --- 3. Stage the artifacts + a landing page --------------------------------
Copy-Item $AppInstaller.FullName (Join-Path $Wt $AppInstaller.Name) -Force
Copy-Item $Msix.FullName        (Join-Path $Wt $Msix.Name)        -Force
Copy-Item $Cer                  (Join-Path $Wt "ContextSwitcher-Dev.cer") -Force
# Disable Jekyll so GitHub Pages serves .msix/.appinstaller verbatim.
Set-Content -Path (Join-Path $Wt ".nojekyll") -Value "" -NoNewline -Encoding ascii

$Html = @"
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Context Switcher - install</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 40rem; margin: 3rem auto; padding: 0 1rem; line-height: 1.5; }
    code { background: #f2f2f2; padding: .1rem .3rem; border-radius: 3px; }
    .btn { display: inline-block; margin: 1rem 0; padding: .6rem 1rem; background: #2B2D7A; color: #fff; text-decoration: none; border-radius: 6px; }
    small { color: #666; }
  </style>
</head>
<body>
  <h1>Context Switcher <small>$Version</small></h1>
  <p>An AI-assisted personal work-context application for Windows (development / sideload build).</p>
  <p><a class="btn" href="./$($AppInstaller.Name)">Install / subscribe (App Installer)</a></p>
  <h2>First time - trust the signing certificate</h2>
  <p>This is a self-signed <em>development</em> build. Download
     <a href="./ContextSwitcher-Dev.cer">ContextSwitcher-Dev.cer</a> and import it once
     (elevated PowerShell):</p>
  <pre><code>Import-Certificate -FilePath ContextSwitcher-Dev.cer -CertStoreLocation Cert:\LocalMachine\TrustedPeople</code></pre>
  <p>Then open the Install button above. App Installer checks this page on launch and
     in the background, and offers new versions automatically.</p>
  <p><small>Direct package: <a href="./$($Msix.Name)">$($Msix.Name)</a></small></p>
</body>
</html>
"@
[System.IO.File]::WriteAllText((Join-Path $Wt "index.html"), $Html, (New-Object System.Text.UTF8Encoding($false)))

# --- 4. Commit --------------------------------------------------------------
$Changes = git -C $Wt status --porcelain
if ([string]::IsNullOrWhiteSpace($Changes)) {
    Write-Host "Nothing to publish - the branch already matches these artifacts." -ForegroundColor Yellow
} else {
    git -C $Wt add -A
    git -C $Wt commit -m "Publish Context Switcher $Version ($($Msix.Name))" | Out-Null
    Write-Host "Committed $Version to '$Branch'." -ForegroundColor Green
}

# --- 5. Push (opt-in) -------------------------------------------------------
if ($Push) {
    Write-Host "== Push =="
    git -C $Wt push -u origin "HEAD:$Branch"
    Write-Host ""
    Write-Host "Published. Ensure GitHub Pages is enabled (Settings / Pages) serving the" -ForegroundColor Green
    Write-Host "'$Branch' branch at root. Live in a minute or two at:"
    Write-Host "  $BaseUrl/"
    Write-Host "  $SelfUri"
} else {
    Write-Host ""
    Write-Host "Prepared locally on '$Branch' (worktree: $Wt). NOT pushed." -ForegroundColor Yellow
    Write-Host "Review, then publish with either:"
    Write-Host "  scripts/publish-appinstaller.ps1 -Push"
    Write-Host "  git -C $Wt push -u origin HEAD:$Branch"
    Write-Host ""
    Write-Host "One-time GitHub setup: Settings / Pages / Source = '$Branch' branch, root."
}
