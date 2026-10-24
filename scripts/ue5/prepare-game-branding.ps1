$ErrorActionPreference='Stop'
$project=Join-Path $env:GITHUB_WORKSPACE 'unreal'
$source=Join-Path $project 'SourceAssets/Branding/menu-backdrop.jpg'
$folder=Join-Path $project 'Content/Splash'
New-Item -ItemType Directory -Path $folder -Force | Out-Null
Add-Type -AssemblyName System.Drawing
$image=[Drawing.Image]::FromFile($source)
try { $image.Save((Join-Path $folder 'Splash.bmp'),[Drawing.Imaging.ImageFormat]::Bmp) }
finally { $image.Dispose() }
if (-not (Test-Path -LiteralPath (Join-Path $project 'Build/Windows/Application.ico'))) { throw 'User application icon missing.' }
