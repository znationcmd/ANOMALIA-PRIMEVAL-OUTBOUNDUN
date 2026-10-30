param([string]$EngineRoot = $env:UE_ROOT)
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$project = Join-Path $repo 'unreal/AnomaliaZPrigimalia.uproject'
$map = Join-Path $repo 'unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap'
if (-not (Test-Path -LiteralPath $map)) {
    throw 'La carte native n’existe pas encore dans ce projet. Attendre la création UE5 réussie ; aucune heightmap manuelle n’est nécessaire.'
}
if (-not $EngineRoot) { $EngineRoot = [Environment]::GetEnvironmentVariable('UE_ROOT', 'User') }
if (-not $EngineRoot) { $EngineRoot = 'C:\Program Files\Epic Games\UE_5.8' }
$editor = Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor.exe'
if (-not (Test-Path -LiteralPath $editor)) { throw 'Définir UE_ROOT sur le dossier Unreal Engine 5.8 installé.' }
Start-Process -FilePath $editor -ArgumentList @(('"' + $project + '"'), '/Game/Maps/ANOMALIA_Archipelago_v2')
