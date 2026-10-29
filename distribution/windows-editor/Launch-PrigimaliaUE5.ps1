# ANOMALIA’Z PRIGIMALIA — lanceur Windows Unreal Engine 5.8.
# Opens the renamed, separately staged project. NEVER modifies D:\ANOMALIA.
$ErrorActionPreference = 'Stop'
$project = 'D:\ANOMALIAZ-PRIGIMALIA\unreal\AnomaliaZPrigimalia.uproject'
$marker = 'D:\ANOMALIAZ-PRIGIMALIA\unreal\Saved\BrandMigration\verified-source-backup.marker'
if (-not (Test-Path -LiteralPath $marker)) {
    throw 'La copie ANOMALIA’Z PRIGIMALIA n’est pas encore validée. Projet original préservé.'
}
if (-not (Test-Path -LiteralPath $project)) {
    throw 'Projet Unreal renommé absent : D:\ANOMALIAZ-PRIGIMALIA\unreal\AnomaliaZPrigimalia.uproject'
}
$engineRoots = @()
if ($env:UE_ROOT) { $engineRoots += $env:UE_ROOT }
$engineRoots += 'C:\Program Files\Epic Games\UE_5.8'
$editor = $null
foreach ($root in $engineRoots) {
    $candidate = Join-Path $root 'Engine\Binaries\Win64\UnrealEditor.exe'
    if (Test-Path -LiteralPath $candidate) { $editor = $candidate; break }
}
if (-not $editor) { throw 'Unreal Engine 5.8 introuvable. Configure UE_ROOT avec le dossier du moteur.' }
$report='D:\ANOMALIAZ-PRIGIMALIA\unreal\Saved\BrandMigration\asset-rename-report.json'
$map='/Game/Maps/ANOMALIA_Archipelago_v2'
if(Test-Path -LiteralPath $report) {
    $details=Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
    if($details.verified -and @($details.mapsRenamed | Where-Object { $_.old -eq '/Game/Maps/ANOMALIA_Archipelago_v2' }).Count -gt 0) {
        $map='/Game/Maps/PRIGIMALIA_Archipelago_v2'
    }
}
Start-Process -FilePath $editor -ArgumentList @('"' + $project + '"', $map, '-d3d11', '-sm5')
