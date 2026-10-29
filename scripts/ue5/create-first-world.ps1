# ANOMALIA - Unreal Engine 5.8 World Partition first-test map.
# Run from Windows PowerShell after the UE C++ project compiles.
# Never deletes or replaces an existing .umap.
param([string]$EngineRoot = "C:\Program Files\Epic Games\UE_5.8")
$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Project = Join-Path $Repo "unreal\AnomaliaZPrigimalia.uproject"
$Script = Join-Path $PSScriptRoot "create-first-world.py"
$Editor = Join-Path $EngineRoot "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$Report = Join-Path $Repo "unreal\Saved\AnomaliaMigration\first-world-report.json"
foreach ($file in @($Project, $Script, $Editor)) {
    if (!(Test-Path -LiteralPath $file -PathType Leaf)) {
        throw "Missing file: $file"
    }
}
Write-Host "Unreal will generate /Game/Maps/ANOMALIA_FirstTest with World Partition."
Write-Host "No existing level, original JS version or terrain source will be overwritten."
$Started = Get-Date
& $Editor $Project "-ExecutePythonScript=$Script" "-unattended" "-nop4" "-nosplash"
$Exit = $LASTEXITCODE
if ($Exit -ne 0) { throw "Unreal Editor returned exit code $Exit. Read Saved/Logs for details." }
if (!(Test-Path -LiteralPath $Report -PathType Leaf)) { throw "Unreal did not produce its execution report." }
$Info = Get-Item -LiteralPath $Report
if ($Info.LastWriteTime -lt $Started.AddSeconds(-3)) { throw "Report was not refreshed by this run." }
$Result = Get-Content -LiteralPath $Report -Raw -Encoding UTF8 | ConvertFrom-Json
if ($Result.status -notin @("umap_created_needs_ue_play_test", "already_exists_not_modified")) {
    throw "World creation did not pass: $($Result.status). Report: $Report"
}
if (!(Test-Path -LiteralPath $Result.mapFile -PathType Leaf)) {
    throw "Missing .umap even though an execution report was written: $($Result.mapFile)"
}
Write-Host "World level file: $($Result.mapFile)"
Write-Host "Status: $($Result.status)"
Write-Host "The complete 48x48 km landscape and in-editor gameplay tests are still outstanding."
