$ErrorActionPreference = 'Stop'
try {
    $installRoot = Split-Path -Parent $PSScriptRoot
    $active = Get-Content -LiteralPath (Join-Path $installRoot 'active.json') -Raw | ConvertFrom-Json
    if ($active.state -ne 'VALIDATED_EDITOR_PROJECT_INSTALLED' -or $active.commit -notmatch '^[0-9a-f]{40}$') { throw 'Version active non reconnue.' }
    $project = [IO.Path]::GetFullPath([string]$active.project)
    $versions = [IO.Path]::GetFullPath((Join-Path $installRoot 'versions')) + [IO.Path]::DirectorySeparatorChar
    if (-not $project.StartsWith($versions,[StringComparison]::OrdinalIgnoreCase)) { throw 'Projet actif hors du dossier de versions.' }
    $editor = Join-Path ([string]$active.engineRoot) 'Engine/Binaries/Win64/UnrealEditor.exe'
    if (-not (Test-Path -LiteralPath $project) -or -not (Test-Path -LiteralPath $editor)) { throw 'Projet ou Unreal Engine introuvable.' }
    $map='/Game/Maps/ANOMALIA_Archipelago_v2'
    if ($active.mapPackage -in @('/Game/Maps/ANOMALIA_Archipelago_v2','/Game/Maps/ANOMALIA_Inhabited_v2')) { $map=[string]$active.mapPackage }
    Start-Process -FilePath $editor -ArgumentList @(('"' + $project + '"'), $map, '-d3d11', '-sm5')
} catch {
    Add-Type -AssemblyName System.Windows.Forms
    [Windows.Forms.MessageBox]::Show($_.Exception.Message,'ANOMALIA — Unreal') | Out-Null
    exit 1
}
