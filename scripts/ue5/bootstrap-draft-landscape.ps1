# ANOMALIA UE5.8: generate verified draft tiles, create an EMPTY World Partition .umap.
# This does NOT import the terrain or validate gameplay. Requires compiled UE5 C++ project.
param([string]$EngineRoot = "C:\Program Files\Epic Games\UE_5.8")
$ErrorActionPreference = "Stop"
$Repository = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Game = Join-Path $Repository "unreal\AnomaliaZPrigimalia.uproject"
$Generator = Join-Path $PSScriptRoot "generate-playtest-terrain.py"
$Script = Join-Path $PSScriptRoot "create-terrain-draft-level.py"
$Editor = Join-Path $EngineRoot "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$Output = Join-Path $Repository "unreal\TerrainPreview"
$Report = Join-Path $Repository "unreal\Saved\AnomaliaZPrigimaliaMigration\draft-level-report.json"
foreach ($Required in @($Game, $Generator, $Script, $Editor)) {
  if (!(Test-Path -LiteralPath $Required -PathType Leaf)) {
    throw "File missing: $Required"
  }
}
Write-Host "[ANOMALIA] Generating 144 lower-cost 48km terrain source tiles (no overwrites)."
& python $Generator "--output" $Output
if ($LASTEXITCODE -ne 0) { throw "ANOMALIA terrain generation failed; existing files were not deleted." }
& python $Generator "--output" $Output "--verify-only"
if ($LASTEXITCODE -ne 0) { throw "ANOMALIA terrain tile verification failed." }
Write-Host "[ANOMALIA] Asking Unreal Editor to create EMPTY /Game/Maps/ANOMALIA_TerrainDraft."
$Started = Get-Date
& $Editor $Game "-ExecutePythonScript=$Script" "-unattended" "-nop4" "-nosplash"
if ($LASTEXITCODE -ne 0) { throw "UE Editor failed. Check unreal/Saved/Logs and draft-level-report.json." }
if (!(Test-Path -LiteralPath $Report -PathType Leaf)) { throw "No Unreal execution report found." }
if ((Get-Item -LiteralPath $Report).LastWriteTime -lt $Started.AddSeconds(-3)) {
  throw "Unreal report is stale and cannot verify this run."
}
$Status = Get-Content -LiteralPath $Report -Raw -Encoding UTF8 | ConvertFrom-Json
if ($Status.status -notin @("partitioned_shell_created_terrain_import_required", "already_exists_not_modified")) {
  throw "Unreal reported an error: $($Status.status). Read $Report."
}
if (!(Test-Path -LiteralPath $Status.mapFile -PathType Leaf)) { throw "Unreal .umap file missing." }
Write-Host "[ANOMALIA] Verified Unreal .umap: $($Status.mapFile)"
Write-Host "NEXT STEP: Open this level in Unreal, Landscape mode (Shift+2), Import from File:"
Write-Host "           unreal/TerrainPreview/ANOMALIA_x0_y0.r16, and accept all 144 tiles."
Write-Host "           Scale X=Y=1587.301587 cm, Z=200; confirm Flip Y visually."
Write-Host "No playable terrain yet; imported Landscape and Play In Editor remain to be tested."
