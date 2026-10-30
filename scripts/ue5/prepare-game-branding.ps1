# ANOMALIA'Z PRIGIMALIA startup image only. Do not use the workshop/menu backdrop.
$ErrorActionPreference = 'Stop'
$project = Join-Path $env:GITHUB_WORKSPACE 'unreal'
$source = Join-Path $project 'SourceAssets/Branding/prigimalia-startup-poster.jpg'
$folder = Join-Path $project 'Content/Splash'
if (-not (Test-Path -LiteralPath $source)) { throw 'Approved startup poster JPG is missing: refusing to build a different splash.' }
if ((Get-Item -LiteralPath $source).Length -lt 100000) { throw 'Startup artwork file is unexpectedly small.' }
New-Item -ItemType Directory -Path $folder -Force | Out-Null
Add-Type -AssemblyName System.Drawing
$image = [Drawing.Image]::FromFile($source)
try {
    if ($image.Width -lt 1400 -or $image.Height -lt 800) { throw 'High-quality original poster required (at least 1400x800).' }
    $image.Save((Join-Path $folder 'Splash.bmp'),[Drawing.Imaging.ImageFormat]::Bmp)
} finally { $image.Dispose() }
if (-not (Test-Path -LiteralPath (Join-Path $project 'Build/Windows/Application.ico'))) { throw 'User application icon missing.' }
Write-Host 'PRIGIMALIA_BOOT_ONLY_SPLASH_READY=true'
