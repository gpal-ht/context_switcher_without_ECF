<#
.SYNOPSIS
    Generates the Context Switcher branded app-icon set (ADR-0021).

.DESCRIPTION
    Renders the brand mark - two overlapping rounded "context" panels in white
    on a diagonal indigo->teal gradient - into the app's Assets folder at every
    size the MSIX manifest uses, including scale and target-size variants. This
    script is the source of truth for the branding; the PNGs it writes are
    committed generated artifacts.

    Deterministic (GDI+/System.Drawing); no external tools required.
#>
[CmdletBinding()]
param(
    [string] $OutDir
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $OutDir) { $OutDir = Join-Path $RepoRoot "src\App\ContextSwitcher.App\Assets" }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Indigo = [System.Drawing.Color]::FromArgb(255, 43, 45, 122)   # #2B2D7A
$Teal   = [System.Drawing.Color]::FromArgb(255, 28, 160, 184)  # #1CA0B8
$White  = [System.Drawing.Color]::White

function New-RoundedPath([double]$x, [double]$y, [double]$w, [double]$h, [double]$r) {
    $r = [Math]::Min($r, [Math]::Min($w, $h) / 2)
    $d = $r * 2
    $p = New-Object System.Drawing.Drawing2D.GraphicsPath
    $p.AddArc($x, $y, $d, $d, 180, 90)
    $p.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $p.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
    $p.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $p.CloseFigure()
    return $p
}

# Draws the brand mark centered in the given square content box.
function Draw-Mark([System.Drawing.Graphics]$g, [double]$cx, [double]$cy, [double]$size) {
    $panel = $size * 0.60
    $radius = $panel * 0.22
    $offset = $size * 0.18
    $keyline = [Math]::Max(1.0, $size * 0.05)

    # Back panel (upper-left), semi-transparent white for depth.
    $bx = $cx - $panel / 2 - $offset / 2
    $by = $cy - $panel / 2 - $offset / 2
    $backBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(150, 255, 255, 255))
    $backPath = New-RoundedPath $bx $by $panel $panel $radius
    $g.FillPath($backBrush, $backPath)

    # Keyline behind the front panel to separate it from the back.
    $fx = $cx - $panel / 2 + $offset / 2
    $fy = $cy - $panel / 2 + $offset / 2
    $keyBrush = New-Object System.Drawing.SolidBrush($Indigo)
    $keyPath = New-RoundedPath ($fx - $keyline) ($fy - $keyline) ($panel + 2 * $keyline) ($panel + 2 * $keyline) ($radius + $keyline)
    $g.FillPath($keyBrush, $keyPath)

    # Front panel (lower-right), solid white.
    $frontBrush = New-Object System.Drawing.SolidBrush($White)
    $frontPath = New-RoundedPath $fx $fy $panel $panel $radius
    $g.FillPath($frontBrush, $frontPath)

    $backBrush.Dispose(); $keyBrush.Dispose(); $frontBrush.Dispose()
    $backPath.Dispose(); $keyPath.Dispose(); $frontPath.Dispose()
}

# Renders a plated icon (gradient rounded-square + centered mark) to a Bitmap.
# Caller disposes the returned Bitmap.
function Render-IconBitmap([int]$w, [int]$h, [bool]$wordmark = $false) {
    $bmp = New-Object System.Drawing.Bitmap($w, $h)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = 'AntiAlias'
    $g.InterpolationMode = 'HighQualityBicubic'
    $g.Clear([System.Drawing.Color]::Transparent)

    # Background: rounded square (corner radius scales with the smaller side).
    $rect = New-Object System.Drawing.Rectangle(0, 0, $w, $h)
    $bgRadius = [Math]::Min($w, $h) * 0.18
    $bgPath = New-RoundedPath 0 0 $w $h $bgRadius
    $grad = New-Object System.Drawing.Drawing2D.LinearGradientBrush($rect, $Indigo, $Teal, 45.0)
    $g.FillPath($grad, $bgPath)

    if ($wordmark) {
        # Splash: mark in the upper area, app name below.
        $markSize = [Math]::Min($w, $h) * 0.42
        Draw-Mark $g ($w / 2) ($h * 0.40) $markSize
        $fontSize = [Math]::Max(10, [Math]::Floor($h * 0.11))
        $font = New-Object System.Drawing.Font('Segoe UI', $fontSize, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
        $brush = New-Object System.Drawing.SolidBrush($White)
        $fmt = New-Object System.Drawing.StringFormat
        $fmt.Alignment = 'Center'; $fmt.LineAlignment = 'Center'
        $textRect = New-Object System.Drawing.RectangleF([float]0, [float]($h * 0.72), [float]$w, [float]($h * 0.2))
        $g.DrawString('Context Switcher', $font, $brush, $textRect, $fmt)
        $font.Dispose(); $brush.Dispose()
    }
    else {
        $markSize = [Math]::Min($w, $h) * 0.66
        Draw-Mark $g ($w / 2) ($h / 2) $markSize
    }

    $grad.Dispose(); $bgPath.Dispose(); $g.Dispose()
    return $bmp
}

# Plated icon PNG: renders and saves to the Assets folder.
function New-Icon([string]$name, [int]$w, [int]$h, [bool]$wordmark = $false) {
    $bmp = Render-IconBitmap $w $h $wordmark
    $bmp.Save((Join-Path $OutDir $name), [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
}

# Multi-size .ico (PNG-compressed entries) for the executable / window (ADR-0022).
function New-Ico([string]$name, [int[]]$sizes) {
    $blobs = foreach ($s in $sizes) {
        $bmp = Render-IconBitmap $s $s $false
        $ms = New-Object System.IO.MemoryStream
        $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
        $bmp.Dispose()
        , $ms.ToArray()
    }
    $count = $blobs.Count
    $out = New-Object System.IO.MemoryStream
    $bw = New-Object System.IO.BinaryWriter($out)
    $bw.Write([UInt16]0)      # reserved
    $bw.Write([UInt16]1)      # type: icon
    $bw.Write([UInt16]$count)
    $offset = 6 + 16 * $count
    for ($i = 0; $i -lt $count; $i++) {
        $s = $sizes[$i]; $len = $blobs[$i].Length
        $dim = if ($s -ge 256) { 0 } else { $s }   # 0 means 256 in ICO
        $bw.Write([Byte]$dim)      # width
        $bw.Write([Byte]$dim)      # height
        $bw.Write([Byte]0)         # palette colors
        $bw.Write([Byte]0)         # reserved
        $bw.Write([UInt16]1)       # color planes
        $bw.Write([UInt16]32)      # bits per pixel
        $bw.Write([UInt32]$len)    # bytes in resource
        $bw.Write([UInt32]$offset) # offset from file start
        $offset += $len
    }
    foreach ($blob in $blobs) { $bw.Write($blob) }
    $bw.Flush()
    [System.IO.File]::WriteAllBytes((Join-Path $OutDir $name), $out.ToArray())
    $bw.Dispose(); $out.Dispose()
}

# --- Base logos + the scale/target-size variants the manifest resolves --------
New-Icon 'Square44x44Logo.png'                   44   44
New-Icon 'Square44x44Logo.scale-200.png'         88   88
New-Icon 'Square44x44Logo.targetsize-16.png'     16   16
New-Icon 'Square44x44Logo.targetsize-24.png'     24   24
New-Icon 'Square44x44Logo.targetsize-32.png'     32   32
New-Icon 'Square44x44Logo.targetsize-48.png'     48   48
New-Icon 'Square44x44Logo.targetsize-256.png'    256  256

New-Icon 'Square71x71Logo.png'                   71   71
New-Icon 'Square71x71Logo.scale-200.png'         142  142

New-Icon 'Square150x150Logo.png'                 150  150
New-Icon 'Square150x150Logo.scale-200.png'       300  300

New-Icon 'Square310x310Logo.png'                 310  310

New-Icon 'Wide310x150Logo.png'                   310  150
New-Icon 'Wide310x150Logo.scale-200.png'         620  300

New-Icon 'StoreLogo.png'                         50   50
New-Icon 'StoreLogo.scale-200.png'               100  100

New-Icon 'SplashScreen.png'                      620  300  $true
New-Icon 'SplashScreen.scale-200.png'            1240 600  $true

# Executable / window icon (ADR-0022).
New-Ico  'app.ico' @(16, 24, 32, 48, 64, 128, 256)

Get-ChildItem $OutDir -Filter *.png | Sort-Object Name | ForEach-Object {
    Write-Output ("  " + $_.Name + " (" + $_.Length + " bytes)")
}
Write-Output ("Wrote branded assets to " + $OutDir)
