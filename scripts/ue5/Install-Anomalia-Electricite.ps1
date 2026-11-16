# ANOMALIA'Z PRIGIMALIA — safe local source installer for Unreal Engine 5.
# Run on the actual Windows PC. It never edits user saves, maps, items, or built packaged game.
param([string]$ProjectRoot = "", [switch]$NoBuild)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Repository = 'znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN'
$Revision = 'a6e8e3c4ceb977dad7dfc3d2e94f317674659535'
$BaseRevision = 'c30bca107b3ee502e0c4c58a842a29f681275e1d'
$Module = 'AnomaliaPrimeval'

$Modified = @(
    'Source/AnomaliaPrimeval/AnomaliaGameMode.h',
    'Source/AnomaliaPrimeval/AnomaliaGameMode.cpp',
    'Source/AnomaliaPrimeval/AnomaliaSurvivor.h',
    'Source/AnomaliaPrimeval/AnomaliaSurvivor.cpp',
    'Source/AnomaliaPrimeval/AnomaliaInventoryComponent.h',
    'Source/AnomaliaPrimeval/AnomaliaInventoryComponent.cpp'
)
$Added = @(
    'Source/AnomaliaPrimeval/AnomaliaFoodPreservation.h',
    'Source/AnomaliaPrimeval/AnomaliaFoodPreservation.cpp',
    'Source/AnomaliaPrimeval/AnomaliaPowerGenerator.h',
    'Source/AnomaliaPrimeval/AnomaliaPowerGenerator.cpp',
    'Source/AnomaliaPrimeval/AnomaliaRefrigerator.h',
    'Source/AnomaliaPrimeval/AnomaliaRefrigerator.cpp',
    'Source/AnomaliaPrimeval/AnomaliaRefrigeratorWidget.h',
    'Source/AnomaliaPrimeval/AnomaliaRefrigeratorWidget.cpp',
    'Source/AnomaliaPrimeval/AnomaliaBatteryCharger.h',
    'Source/AnomaliaPrimeval/AnomaliaBatteryCharger.cpp',
    'Source/AnomaliaPrimeval/AnomaliaWorkLight.h',
    'Source/AnomaliaPrimeval/AnomaliaWorkLight.cpp',
    'Source/AnomaliaPrimeval/AnomaliaPowerUtilityWidget.h',
    'Source/AnomaliaPrimeval/AnomaliaPowerUtilityWidget.cpp',
    'Source/AnomaliaPrimeval/Tests/AnomaliaRefrigerationTests.cpp',
    'Config/Anomalia/appliances.example.json'
)
$All = @($Modified) + @($Added)

function Test-Project([string]$Directory) {
    if ([string]::IsNullOrWhiteSpace($Directory)) { return $false }
    $File = Join-Path $Directory 'AnomaliaPrimeval.uproject'
    return (Test-Path -LiteralPath $File -PathType Leaf) -and
        (Test-Path -LiteralPath (Join-Path $Directory 'Source/AnomaliaPrimeval/AnomaliaGameMode.cpp') -PathType Leaf)
}

function Find-ProjectRoot {
    if (Test-Project $ProjectRoot) { return (Resolve-Path -LiteralPath $ProjectRoot).Path }
    if (-not [string]::IsNullOrWhiteSpace($ProjectRoot)) {
        throw "Le chemin choisi ne contient pas le projet AnomaliaPrimeval : $ProjectRoot"
    }
    $Candidates = @(
        'D:\ANOMALIA\unreal', 'D:\ANOMALIA', 'C:\ANOMALIA\unreal',
        'C:\ANOMALIA', 'D:\ANOMALIA\ANOMALIA', 'D:\ANOMALIA\AnomaliaPrimeval'
    )
    foreach ($Candidate in $Candidates) {
        if (Test-Project $Candidate) { return (Resolve-Path -LiteralPath $Candidate).Path }
    }
    # Search only a few levels; do not crawl gigabytes of Content/Sketchfab/Saved data.
    $Ignore = @('Content','Saved','Binaries','Intermediate','DerivedDataCache','sketchfab','FabImports','versions','.git','node_modules')
    $Queue = New-Object 'System.Collections.Generic.Queue[object]'
    foreach ($Root in @('D:\ANOMALIA','C:\ANOMALIA')) {
        if (Test-Path -LiteralPath $Root -PathType Container) {
            $Queue.Enqueue(@($Root, 0))
        }
    }
    while ($Queue.Count -gt 0) {
        $Entry = $Queue.Dequeue()
        $Dir = [string]$Entry[0]
        $Depth = [int]$Entry[1]
        if (Test-Project $Dir) { return (Resolve-Path -LiteralPath $Dir).Path }
        if ($Depth -ge 3) { continue }
        foreach ($Sub in (Get-ChildItem -LiteralPath $Dir -Directory -ErrorAction SilentlyContinue)) {
            if ($Ignore -notcontains $Sub.Name) { $Queue.Enqueue(@($Sub.FullName, $Depth+1)) }
        }
    }
    throw "Projet Unreal ANOMALIA introuvable. Aucun fichier n'a ete modifie."
}

function Download-Pinned([string]$RevisionId, [string]$RelativePath, [string]$Destination) {
    $Url = "https://raw.githubusercontent.com/$Repository/$RevisionId/unreal/$RelativePath"
    $Parent = Split-Path $Destination -Parent
    New-Item -ItemType Directory -Path $Parent -Force | Out-Null
    Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Destination -TimeoutSec 60
    if ((Get-Item -LiteralPath $Destination).Length -lt 4) {
        throw "Telechargement vide : $RelativePath"
    }
}

function File-Matches([string]$One,[string]$Two) {
    if (-not (Test-Path -LiteralPath $One -PathType Leaf) -or -not (Test-Path -LiteralPath $Two -PathType Leaf)) {
        return $false
    }
    return (Get-FileHash -LiteralPath $One -Algorithm SHA256).Hash -eq
           (Get-FileHash -LiteralPath $Two -Algorithm SHA256).Hash
}

function Find-UnrealEngine {
    if ($env:UE_ROOT -and (Test-Path -LiteralPath (Join-Path $env:UE_ROOT 'Engine/Build/BatchFiles/Build.bat'))) {
        return $env:UE_ROOT
    }
    $Installations = @('C:\Program Files\Epic Games','D:\Epic Games','D:\Unreal Engine')
    foreach ($Parent in $Installations) {
        if (-not (Test-Path -LiteralPath $Parent)) { continue }
        $Engines = @(Get-ChildItem -LiteralPath $Parent -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '^UE_5\.' } | Sort-Object Name -Descending)
        foreach ($Engine in $Engines) {
            if (Test-Path -LiteralPath (Join-Path $Engine.FullName 'Engine/Build/BatchFiles/Build.bat')) {
                return $Engine.FullName
            }
        }
    }
    return $null
}

$Project = Find-ProjectRoot
$Uproject = Join-Path $Project 'AnomaliaPrimeval.uproject'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$LogRoot = Join-Path $Project "Saved/AnomaliaElectricalInstaller/$Stamp"
$Stage = Join-Path $LogRoot 'staging'
$Baseline = Join-Path $LogRoot 'baseline'
$Backup = Join-Path $LogRoot 'backup'
New-Item -ItemType Directory -Path $Stage,$Baseline,$Backup -Force | Out-Null

Write-Host "ANOMALIA'Z — Projet detecte : $Project"
Write-Host "Sauvegardes et journal : $LogRoot"

try {
    # Download everything first, and verify existing files match the known upstream base
    # or the pinned incoming file. This prevents accidental overwrites of more advanced local work.
    $Conflicts = New-Object 'System.Collections.Generic.List[string]'
    foreach ($Rel in $All) {
        $Incoming = Join-Path $Stage $Rel
        Download-Pinned $Revision $Rel $Incoming
        $Local = Join-Path $Project $Rel
        if ($Modified -contains $Rel) {
            $Upstream = Join-Path $Baseline $Rel
            Download-Pinned $BaseRevision $Rel $Upstream
            if (-not (File-Matches $Local $Upstream) -and -not (File-Matches $Local $Incoming)) {
                $Conflicts.Add("Source locale differente : $Rel")
            }
        } elseif ((Test-Path -LiteralPath $Local) -and -not (File-Matches $Local $Incoming)) {
            $Conflicts.Add("Fichier local deja present : $Rel")
        }
    }
    if ($Conflicts.Count -gt 0) {
        $Conflicts | Set-Content -LiteralPath (Join-Path $LogRoot 'CONFLITS.txt') -Encoding UTF8
        throw ("Versions incompatibles. Aucune source modifiee. Liste : " +
            (Join-Path $LogRoot 'CONFLITS.txt'))
    }

    $Touched = New-Object 'System.Collections.Generic.List[string]'
    $Created = New-Object 'System.Collections.Generic.List[string]'
    foreach ($Rel in $All) {
        $Local = Join-Path $Project $Rel
        $Incoming = Join-Path $Stage $Rel
        if (File-Matches $Local $Incoming) { continue }
        if (Test-Path -LiteralPath $Local) {
            $BackupFile = Join-Path $Backup $Rel
            New-Item -ItemType Directory -Path (Split-Path $BackupFile -Parent) -Force | Out-Null
            Copy-Item -LiteralPath $Local -Destination $BackupFile -Force
            $Touched.Add($Rel)
        } else { $Created.Add($Rel) }
        New-Item -ItemType Directory -Path (Split-Path $Local -Parent) -Force | Out-Null
        Copy-Item -LiteralPath $Incoming -Destination $Local -Force
    }
    Write-Host "Sources de refrigerateur, generateur, batterie et chantier installees dans le projet UE5."

    if ($NoBuild) { Write-Warning "Compilation ignoree : les sources ne prouvent pas un jeu fonctionnel."; return }
    $Engine = Find-UnrealEngine
    if (-not $Engine) { throw 'Unreal Engine 5 introuvable; compilation non effectuee.' }
    $Build = Join-Path $Engine 'Engine/Build/BatchFiles/Build.bat'
    foreach ($Target in @('AnomaliaPrimevalEditor','AnomaliaPrimeval')) {
        Write-Host "Compilation $Target..."
        $Log = Join-Path $LogRoot "$Target.log"
        & $Build $Target Win64 Development "-Project=$Uproject" '-WaitMutex' '-NoHotReloadFromIDE' *> $Log
        if ($LASTEXITCODE -ne 0) { throw "Echec compilation $Target. Journal : $Log" }
    }
    Write-Host "COMPILATION C++ TERMINEE. Il reste a assigner les meshes et emplacements reels dans Unreal."
    (Get-Date -Format o) | Set-Content -LiteralPath (Join-Path $LogRoot 'SOURCE-COMPILEE.txt')
}
catch {
    Write-Warning $_.Exception.Message
    # Only revert files actually changed by this installer; never touch user maps, Content, or saves.
    if (Test-Path variable:Touched) {
        foreach ($Rel in $Touched) {
            Copy-Item -LiteralPath (Join-Path $Backup $Rel) -Destination (Join-Path $Project $Rel) -Force
        }
    }
    if (Test-Path variable:Created) {
        foreach ($Rel in $Created) {
            $Local = Join-Path $Project $Rel
            if (Test-Path -LiteralPath $Local -PathType Leaf) { Remove-Item -LiteralPath $Local -Force }
        }
    }
    throw
}
finally {
    Write-Host "Journal / sauvegarde : $LogRoot"
}