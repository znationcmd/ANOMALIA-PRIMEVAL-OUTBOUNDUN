param(
    [Parameter(Mandatory=$true)][string]$Project,
    [Parameter(Mandatory=$true)][string]$EngineRoot
)
$ErrorActionPreference = 'Stop'
$Project = (Resolve-Path -LiteralPath $Project).Path
$projectDir = Split-Path -Parent $Project
if ($projectDir -ne 'D:\ANOMALIA\unreal') {
    throw 'Select the actual D:\ANOMALIA\unreal project.'
}
if (Get-Process -Name UnrealEditor,UnrealEditor-Cmd,AnomaliaPrimeval,AnomaliaZPrigimalia -ErrorAction SilentlyContinue) {
    throw 'Close the running Unreal editor or game before generating maps.'
}
$engine = (Resolve-Path -LiteralPath $EngineRoot).Path
$build = Join-Path $engine 'Engine\Build\BatchFiles\Build.bat'
$editor = Join-Path $engine 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$author = Join-Path $repo 'unreal\Scripts\create_three_requested_native_maps.py'
$installer = Join-Path $PSScriptRoot 'install-three-map-sources.py'
$python = Join-Path $engine 'Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
foreach ($path in @($build, $editor, $author, $installer, $python)) {
    if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing file: $path" }
}
$descriptor = Get-Content -LiteralPath $Project -Raw | ConvertFrom-Json
$module = $descriptor.Modules[0].Name
if ([IO.Path]::GetFileName($Project) -eq 'AnomaliaPrimeval.uproject') {
    $env:THREE_MAP_OUT = Join-Path $projectDir ('Saved\RequestedTenMaps\SourceInstall-' + [guid]::NewGuid())
    New-Item -ItemType Directory -Path $env:THREE_MAP_OUT -Force | Out-Null
    & $python -B $installer
    if ($LASTEXITCODE -ne 0) { throw "Guarded source installation failed. See $env:THREE_MAP_OUT." }
}
& $build ($module + 'Editor') Win64 Development $Project -WaitMutex -NoHotReloadFromIDE -MaxParallelActions=2
if ($LASTEXITCODE -ne 0) { throw "Unreal editor compilation failed ($LASTEXITCODE)." }

$reportDir = Join-Path $projectDir 'Saved\RequestedTenMaps'
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
foreach ($id in @('CLEOSPHINIL_X','VELUNDA','KARVERRA','NOKTERA','AETHORION','SALVERIA','WARRAKULL','DIJKENHAVEN','LAGUNERIA','KUNTARAY','COFFIN_CREEK','ZNIECZULENIE','ORBITALE_TERMINUS')) {
    $mapPath = Join-Path $projectDir "Content\Maps\PRIGIMALIA_$id.umap"
    $report = Join-Path $reportDir "$id.json"
    if ((Test-Path -LiteralPath $mapPath) -and (Test-Path -LiteralPath $report)) {
        $previous = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
        if (($previous.actualLandscapeSaved -or $previous.actualStationSaved) -and $previous.mapPackage -eq "/Game/Maps/PRIGIMALIA_$id") {
            Write-Host "Already generated: $id"
            continue
        }
    }
    if (Test-Path -LiteralPath $mapPath) { throw "Existing map requires review: $mapPath" }
    $env:PRIGIMALIA_THREE_MAP = $id
    $env:PRIGIMALIA_THREE_REPORT = $report
    & $editor $Project "-ExecutePythonScript=$author" -unattended -nopause -nosound -NullRHI "-abslog=$reportDir\$id.log"
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0 -or !(Test-Path -LiteralPath $report)) {
        throw "Unreal failed to generate $id ($exitCode). See $reportDir."
    }
    $receipt = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
    if (!($receipt.actualLandscapeSaved -or $receipt.actualStationSaved) -or !(Test-Path -LiteralPath $mapPath)) {
        throw "Unreal did not save ${id}: $($receipt.error)"
    }
}
