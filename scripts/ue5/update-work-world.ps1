# ANOMALIA: prepare Work's 48 x 48 km heightmap in an existing Unreal project.
# Does not touch Content/, Saved/, Config/, Blueprints, or existing .umap.
[CmdletBinding()]
param(
    [string]$ProjectRoot = 'C:\ANOMALIA'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$root = [IO.Path]::GetFullPath($ProjectRoot)
$uproject = Join-Path $root 'unreal\AnomaliaPrimeval.uproject'
if (-not (Test-Path -LiteralPath $uproject -PathType Leaf)) {
    throw "Projet Unreal introuvable : $uproject. Utilise -ProjectRoot avec le dossier qui contient unreal\AnomaliaPrimeval.uproject."
}
$folder = Join-Path $root 'unreal\TerrainWorkImport'
$heightmap = Join-Path $folder 'ANOMALIA_WorkMap_48km_3025.r16'
$manifest = Join-Path $folder 'ANOMALIA_WorkMap_48km_3025.json'
$landmarks = Join-Path $folder 'ANOMALIA_WorkMap_Landmarks.json'
if (Test-Path -LiteralPath $heightmap -PathType Leaf) {
    if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
        throw "Un terrain existe sans manifeste : $heightmap. Il n'est pas modifie. Verifie ce fichier ou sauvegarde-le avant de relancer."
    }
    $info = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
    $hash = (Get-FileHash -LiteralPath $heightmap -Algorithm SHA256).Hash.ToLowerInvariant()
    $length = (Get-Item -LiteralPath $heightmap).Length
    if ($length -ne (3025 * 3025 * 2) -or $hash -ne [string]$info.sha256) {
        throw "Terrain existant different du manifeste. Rien n'a ete remplace : $heightmap"
    }
    if (-not (Test-Path -LiteralPath $landmarks -PathType Leaf)) {
        Write-Warning "Relief ZIP valide. Coordonnees des sites absentes : ce fichier est facultatif pour le premier import du relief."
    }
    Write-Host "Carte Work deja presente, integrite verifiee (SHA256)." -ForegroundColor Green
}
else {
    $node = Get-Command node -ErrorAction SilentlyContinue
    if (-not $node) {
        throw "Node.js est necessaire UNIQUEMENT si le fichier R16 n'est pas deja present. Tu peux utiliser le fichier R16 du ZIP ou installer Node.js LTS (nodejs.org). Aucun fichier existant n'a ete modifie."
    }
    if ((Test-Path -LiteralPath $manifest) -or (Test-Path -LiteralPath $landmarks)) {
        throw "Import partiel deja present dans $folder. Aucun fichier existant ne sera remplace."
    }
    $staging = Join-Path ([IO.Path]::GetTempPath()) ('anomalia-work-' + [Guid]::NewGuid().ToString('N'))
    try {
        New-Item -Path (Join-Path $staging 'scripts\ue5') -ItemType Directory -Force | Out-Null
        New-Item -Path (Join-Path $staging 'src') -ItemType Directory -Force | Out-Null
        $utf8 = [System.Text.UTF8Encoding]::new($false)
        [IO.File]::WriteAllText((Join-Path $staging 'package.json'), '{"type":"module"}', $utf8)
        $base = 'https://raw.githubusercontent.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/ue5/prototype-world-ai-roads-20261020'
        $paths = @('scripts/ue5/export-work-map.mjs', 'src/mechanics.js', 'src/ecology.js')
        foreach ($p in $paths) {
            $target = Join-Path $staging ($p -replace '/', '\')
            $uri = "$base/$p"
            Write-Host "Recuperation : $p"
            Invoke-WebRequest -Uri $uri -OutFile $target -UseBasicParsing
            if ((Get-Item -LiteralPath $target).Length -lt 100) {
                throw "Fichier distant vide ou incorrect : $p"
            }
        }
        New-Item -Path $folder -ItemType Directory -Force | Out-Null
        Push-Location $root
        try {
            Write-Host "Generation de la carte Work (48 km x 48 km). Cela peut prendre plusieurs minutes." -ForegroundColor Cyan
            & $node.Source (Join-Path $staging 'scripts\ue5\export-work-map.mjs')
            if ($LASTEXITCODE -ne 0) {
                throw "Le generateur a echoue (code $LASTEXITCODE). Voir les messages ci-dessus."
            }
        }
        finally { Pop-Location }
    }
    finally {
        if (Test-Path -LiteralPath $staging) {
            Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    if (-not (Test-Path -LiteralPath $heightmap) -or -not (Test-Path -LiteralPath $manifest)) {
        throw "Generation terminee sans fichiers attendus. Import Unreal non effectue."
    }
    Write-Host "Terrain cree avec succes dans $folder" -ForegroundColor Green
}

# Repair the JSON next to a previously exported .r16 RAW Landscape heightmap.
# Epic RAW format requires "width", "height", "bbp" (spelled bbp, not bpp).
# The original ZIP bundled a valid 16-bit raw file but a JSON without these keys.
# Preserve all metadata and copy original JSON once before adding them.
$sidecarInfo = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
if (($sidecarInfo.width -ne 3025) -or
    ($sidecarInfo.height -ne 3025) -or
    ($sidecarInfo.bbp -ne 16)) {
    $metadataBackup = Join-Path $folder 'ANOMALIA_WorkMap_48km_3025_MetadataBeforeUnrealFix.json'
    if (-not (Test-Path -LiteralPath $metadataBackup -PathType Leaf)) {
        Copy-Item -LiteralPath $manifest -Destination $metadataBackup -ErrorAction Stop
    }
    $sidecarInfo | Add-Member -NotePropertyName 'width' -NotePropertyValue 3025 -Force
    $sidecarInfo | Add-Member -NotePropertyName 'height' -NotePropertyValue 3025 -Force
    $sidecarInfo | Add-Member -NotePropertyName 'bbp' -NotePropertyValue 16 -Force
    [IO.File]::WriteAllText($manifest, ($sidecarInfo | ConvertTo-Json -Depth 20),
        [System.Text.UTF8Encoding]::new($false))
    Write-Host 'Format Unreal corrige : 3025 x 3025, profondeur 16 bits. JSON original sauvegarde.' -ForegroundColor Green
} else {
    Write-Host 'Format Unreal RAW deja configure : 3025 x 3025, 16 bits.' -ForegroundColor Green
}

# Update the four isolated C++ prototype sources without overwriting local changes.
# Hash-based update: automatically replace only files that match our previous installation.
# If the local file was edited, skip that file and preserve the modifications.
$previewSources = @(
    'unreal/Source/AnomaliaPrimeval/AnomaliaAmbientAgent.h',
    'unreal/Source/AnomaliaPrimeval/AnomaliaAmbientAgent.cpp',
    'unreal/Source/AnomaliaPrimeval/AnomaliaWorkWorldBootstrap.h',
    'unreal/Source/AnomaliaPrimeval/AnomaliaWorkWorldBootstrap.cpp'
)
$previewStaging = Join-Path ([IO.Path]::GetTempPath()) ('anomalia-preview-' + [Guid]::NewGuid().ToString('N'))
$previewBase = 'https://raw.githubusercontent.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/ue5/prototype-world-ai-roads-20261020'
$sourceStatePath = Join-Path $folder '.anomalia-source-update-state.json'
$sourceState = @{}
if (Test-Path -LiteralPath $sourceStatePath -PathType Leaf) {
    $savedState = Get-Content -LiteralPath $sourceStatePath -Raw | ConvertFrom-Json
    foreach ($property in $savedState.PSObject.Properties) {
        if ([string]$property.Value -match '^[a-fA-F0-9]{64}$') {
            $sourceState[$property.Name] = ([string]$property.Value).ToLowerInvariant()
        }
    }
}
$sourceStateModified = $false
try {
    New-Item -Path $previewStaging -ItemType Directory -Force | Out-Null
    foreach ($source in $previewSources) {
        $file = [IO.Path]::GetFileName($source)
        $tempFile = Join-Path $previewStaging $file
        Invoke-WebRequest -Uri "$previewBase/$source" -OutFile $tempFile -UseBasicParsing
        if ((Get-Item -LiteralPath $tempFile).Length -lt 400) {
            throw "Telechargement invalide pour $file. Les autres fichiers ne sont pas modifies."
        }
        $destination = Join-Path $root ($source -replace '/', '\')
        $remoteHash = (Get-FileHash -LiteralPath $tempFile -Algorithm SHA256).Hash.ToLowerInvariant()
        $install = $false
        if (Test-Path -LiteralPath $destination -PathType Leaf) {
            $localHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($remoteHash -eq $localHash) {
                Write-Host "Deja a jour : $file"
                $sourceState[$source] = $remoteHash
                $sourceStateModified = $true
                continue
            }
            if (-not $sourceState.ContainsKey($source) -or $sourceState[$source] -ne $localHash) {
                Write-Warning "Fichier modifie localement : $file. Il est conserve sans etre ecrase. Fusion manuelle necessaire."
                continue
            }
            $backupDir = Join-Path $folder ('SourceBackups\' + (Get-Date -Format 'yyyyMMdd-HHmmss-ffff'))
            New-Item -Path $backupDir -ItemType Directory -Force | Out-Null
            Copy-Item -LiteralPath $destination -Destination (Join-Path $backupDir $file) -ErrorAction Stop
            $install = $true
        } else {
            $install = $true
        }
        if ($install) {
            $dir = Split-Path -Path $destination -Parent
            if (-not (Test-Path -LiteralPath $dir)) {
                New-Item -Path $dir -ItemType Directory -Force | Out-Null
            }
            Copy-Item -LiteralPath $tempFile -Destination $destination -Force -ErrorAction Stop
            $sourceState[$source] = $remoteHash
            $sourceStateModified = $true
            Write-Host "Module installe/mis a jour : $file" -ForegroundColor Green
        }
    }
}
finally {
    if ($sourceStateModified) {
        $stateJson = $sourceState | ConvertTo-Json -Depth 4
        [IO.File]::WriteAllText($sourceStatePath, $stateJson,
            [System.Text.UTF8Encoding]::new($false))
    }
    if (Test-Path -LiteralPath $previewStaging) {
        Remove-Item -LiteralPath $previewStaging -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "Sources de prototype pretes. La compilation UE reste a lancer sur Windows." -ForegroundColor Green

Write-Host ""
Write-Host "ETAPE SUIVANTE DANS UNREAL ENGINE 5.8 :" -ForegroundColor Yellow
Write-Host "  1. Conserver AnomaliaWorld sans modification."
Write-Host "  2. Creer une nouvelle carte Open World : ANOMALIA_WorkMap_Test."
Write-Host "  3. Sur cette carte TEST seulement, retirer son terrain de demonstration."
Write-Host "  4. Paysage (Maj+2) > Gerer > Importer depuis un fichier :"
Write-Host "     $heightmap"
Write-Host "  5. Resolution : 3025 x 3025 ; Section 63, sections/composant 2x2, composants 24x24."
Write-Host "     Echelle X=1587.301587 Y=1587.301587 Z=800."
Write-Host "  6. Fermer puis rouvrir Unreal pour compiler les nouveaux fichiers C++."
Write-Host "  7. Dans C++ Classes, placer un AnomaliaWorkWorldBootstrap sur ANOMALIA_WorkMap_Test."
Write-Host "  8. Enregistrer puis cliquer Jouer : prototypes de routes, maisons, arbres et IA."
Write-Host ""
Write-Host "NOTE : la commande prepare le vrai fichier de relief. Le clic Importer dans l'editeur est necessaire pour creer le Landscape .umap."
