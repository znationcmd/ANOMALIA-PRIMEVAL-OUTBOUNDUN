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
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    throw "Node.js est necessaire pour convertir exactement la carte Work. Installer Node.js LTS (nodejs.org), rouvrir PowerShell puis relancer la commande. Aucun fichier de carte existant n'a ete modifie."
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
        throw "Terrain valide mais fichier des sites manquant : $landmarks. Rien n'a ete remplace."
    }
    Write-Host "Carte Work deja presente, integrite verifiee (SHA256)." -ForegroundColor Green
}
else {
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

# Install *new* preview C++ source files only; never rewrite existing user code.
# Source files are reviewed independently on GitHub and compilation still occurs in UE on Windows.
$previewSources = @(
    'unreal/Source/AnomaliaPrimeval/AnomaliaAmbientAgent.h',
    'unreal/Source/AnomaliaPrimeval/AnomaliaAmbientAgent.cpp',
    'unreal/Source/AnomaliaPrimeval/AnomaliaWorkWorldBootstrap.h',
    'unreal/Source/AnomaliaPrimeval/AnomaliaWorkWorldBootstrap.cpp'
)
$previewStaging = Join-Path ([IO.Path]::GetTempPath()) ('anomalia-preview-' + [Guid]::NewGuid().ToString('N'))
$previewBase = 'https://raw.githubusercontent.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/ue5/prototype-world-ai-roads-20261020'
try {
    New-Item -Path $previewStaging -ItemType Directory -Force | Out-Null
    $pending = @()
    foreach ($source in $previewSources) {
        $file = [IO.Path]::GetFileName($source)
        $tempFile = Join-Path $previewStaging $file
        Invoke-WebRequest -Uri "$previewBase/$source" -OutFile $tempFile -UseBasicParsing
        if ((Get-Item -LiteralPath $tempFile).Length -lt 400) {
            throw "Telechargement invalide pour $file. Les fichiers du projet restent inchanges."
        }
        $destination = Join-Path $root ($source -replace '/', '\')
        $remoteHash = (Get-FileHash -LiteralPath $tempFile -Algorithm SHA256).Hash
        if (Test-Path -LiteralPath $destination) {
            $localHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
            if ($remoteHash -ne $localHash) {
                throw "Fichier source deja present mais different : $destination. Il n'a PAS ete remplace. Faire examiner la divergence."
            }
        } else {
            $pending += [pscustomobject]@{ From = $tempFile; To = $destination }
        }
    }
    foreach ($item in $pending) {
        $dir = Split-Path -Path $item.To -Parent
        if (-not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
        Copy-Item -LiteralPath $item.From -Destination $item.To -ErrorAction Stop
        Write-Host "Nouveau module ajoute : $($item.To)" -ForegroundColor Green
    }
    Write-Host "Module routes/batiments/arbres/agents pret pour compilation UE 5.8 (non teste)." -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $previewStaging) {
        Remove-Item -LiteralPath $previewStaging -Recurse -Force -ErrorAction SilentlyContinue
    }
}

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
