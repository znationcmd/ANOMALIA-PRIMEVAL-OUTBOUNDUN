# Non-destructive six-map native terrain previews; not replacements for image references.
$ErrorActionPreference='Stop'
$stage='D:\ANOMALIAZ-PRIGIMALIA\unreal'
$original='D:\ANOMALIA\unreal\AnomaliaPrimeval.uproject'
$project=Join-Path $stage 'AnomaliaZPrigimalia.uproject'
$marker=Join-Path $stage 'Saved\BrandMigration\verified-source-backup.marker'
$src=Join-Path $env:GITHUB_WORKSPACE 'unreal\Source\AnomaliaZPrigimalia\World'
$native=Join-Path $stage 'Source\AnomaliaZPrigimalia\World'
$sourceCpp=Join-Path $src 'AnomaliaZPrigimaliaWorldImportLibrary.cpp'
$sourceHeader=Join-Path $src 'AnomaliaZPrigimaliaWorldImportLibrary.h'
$cpp=Join-Path $native 'AnomaliaZPrigimaliaWorldImportLibrary.cpp'
$header=Join-Path $native 'AnomaliaZPrigimaliaWorldImportLibrary.h'
$pythonSource=Join-Path $env:GITHUB_WORKSPACE 'unreal\Scripts\create_named_terrain_preview_safe.py'
$python=Join-Path $stage 'Scripts\create_named_terrain_preview_safe.py'
$editor=Join-Path $env:UE_ROOT 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$build=Join-Path $env:UE_ROOT 'Engine\Build\BatchFiles\Build.bat'
$names=@('KARSKOV','VORGRAD','NEMORIS','DRAKHEIM','SOLYNACALYRA','NEXAVARKHOS')
$runReport=Join-Path $env:RUNNER_TEMP ('ANOMALIA_SIX_MAP_PREVIEWS_'+$env:GITHUB_RUN_ID)
New-Item -ItemType Directory -Path $runReport -Force | Out-Null
if(-not(Test-Path $original -PathType Leaf) -or -not(Test-Path $project -PathType Leaf) -or -not(Test-Path $marker -PathType Leaf)){throw 'Verified independent Unreal stage missing'}
if(@(Get-Process UnrealEditor,UnrealEditor-Cmd,AnomaliaPrimeval,AnomaliaZPrigimalia,UnrealBuildTool,robocopy -ErrorAction SilentlyContinue).Count -gt 0){throw 'Native editor/build/copy already running; refuse concurrency'}
foreach($p in @($sourceCpp,$sourceHeader,$cpp,$header,$pythonSource,$editor,$build)){
 if(-not(Test-Path -LiteralPath $p -PathType Leaf)){throw ('Required engine/source missing: '+$p)}
}
$protected=@(
 (Join-Path $stage 'Content\Maps\ANOMALIA_Archipelago_v2.umap'),
 (Join-Path $stage 'Content\Maps\ANOMALIA_Inhabited_v2.umap'),
 (Join-Path $stage 'Content\Maps\ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate.umap'),
 $original
)
$originalHashes=@{}
foreach($p in $protected){if(-not(Test-Path -LiteralPath $p -PathType Leaf)){throw ('Missing protected map '+$p)};$originalHashes[$p]=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
foreach($id in $names){
 $candidate=Join-Path $stage ("Content\Maps\PRIGIMALIA_"+$id+"_TerrainPreview.umap")
 if(Test-Path -LiteralPath $candidate){throw ('Preview map already exists: '+$id)}
 foreach($kind in @('__ExternalActors__','__ExternalObjects__')){
  $dir=Join-Path $stage ("Content\"+$kind+"\Maps\PRIGIMALIA_"+$id+"_TerrainPreview")
  if(Test-Path -LiteralPath $dir){throw ('Preview external actor data already exists: '+$id)}
 }
 $photoRaw=Join-Path $stage ("TerrainSource\"+$id+"\"+$id+".r16")
 if(Test-Path -LiteralPath $photoRaw){throw ('Photo heightmap already exists; do not create procedural substitute: '+$id)}
}
if(Test-Path -LiteralPath $python){throw 'Preview Python script already staged; preserve existing work'}
$sourceText=[IO.File]::ReadAllText($sourceCpp)
$oldText=[IO.File]::ReadAllText($cpp)
$needle='AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateNamedWorldLandscape('
$after='AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateChernaskaluxriaLandscapeTile('
$start=$sourceText.IndexOf($needle,[StringComparison]::Ordinal)
$end=$sourceText.IndexOf($after,$start,[StringComparison]::Ordinal)
$oldStart=$oldText.IndexOf($needle,[StringComparison]::Ordinal)
$oldEnd=$oldText.IndexOf($after,$oldStart,[StringComparison]::Ordinal)
if($start -lt 0 -or $end -le $start -or $oldStart -lt 0 -or $oldEnd -le $oldStart){throw 'Unexpected C++ source layout'}
$patch=$sourceText.Substring($start,$end-$start)
if(-not $patch.Contains('InspectNamedWorldPreviewComponents') -or $patch.Contains('Subsystem->ChangeGridSize(') -or -not $patch.Contains('_TerrainPreview')){throw 'Unsafe native importer patch'}
$newCpp=$oldText.Substring(0,$oldStart)+$patch+$oldText.Substring($oldEnd)
$sourceHdr=[IO.File]::ReadAllText($sourceHeader)
$stagedHdr=[IO.File]::ReadAllText($header)
$declaration='static int32 InspectNamedWorldPreviewComponents(AActor* Candidate, const FString& MapIdentifier);'
$anchor='static AActor* CreateNamedWorldLandscape(const FString& MapIdentifier);'
if(-not $sourceHdr.Contains($declaration) -or -not $stagedHdr.Contains($anchor)){throw 'Native headers incompatible'}
if(-not $stagedHdr.Contains($declaration)){
 $addition=[Environment]::NewLine+' UFUNCTION(BlueprintPure, Category="ANOMALIA|World")'+[Environment]::NewLine+' '+$declaration
 $stagedHdr=$stagedHdr.Replace($anchor,$anchor+$addition)
}
$backup=Join-Path $stage ('Saved\NamedTerrainPreviews\source-backup-'+$env:GITHUB_RUN_ID)
if(Test-Path -LiteralPath $backup){throw 'Source backup already exists for this run'}
New-Item -ItemType Directory -Path $backup|Out-Null
Copy-Item -LiteralPath $cpp -Destination (Join-Path $backup 'WorldImportLibrary.cpp.bak')
Copy-Item -LiteralPath $header -Destination (Join-Path $backup 'WorldImportLibrary.h.bak')
[IO.File]::WriteAllText($cpp,$newCpp,[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText($header,$stagedHdr,[Text.UTF8Encoding]::new($false))
Copy-Item -LiteralPath $pythonSource -Destination $python
Write-Host 'SIX_PREVIEW_SAFE_STAGING_COMPLETE=true'
$results=@()
try{
 & $build AnomaliaZPrigimaliaEditor Win64 Development "-Project=$project" -WaitMutex -NoHotReloadFromIDE -MaxParallelActions=2
 if($LASTEXITCODE -ne 0){throw 'Native UE5.8 C++ build failed'}
 Write-Host 'SIX_PREVIEW_CPP_BUILD_SUCCESS=true'
 foreach($id in $names){
  $env:PRIGIMALIA_PREVIEW_MAP=$id
  $env:PRIGIMALIA_PREVIEW_RECEIPT=Join-Path $runReport ($id+'.json')
  $log=Join-Path $runReport ($id+'.log')
  Write-Host ('SIX_PREVIEW_BEGIN='+$id)
  & $editor $project '-NullRHI' '-unattended' '-nopause' '-nosound' '-run=pythonscript' "-script=$python" "-abslog=$log"
  $ec=$LASTEXITCODE
  $receipt=$env:PRIGIMALIA_PREVIEW_RECEIPT
  if($ec -eq 0 -and (Test-Path -LiteralPath $receipt)){
   $proof=Get-Content -LiteralPath $receipt -Raw -Encoding UTF8|ConvertFrom-Json
   $map=Join-Path $stage ("Content\Maps\PRIGIMALIA_"+$id+"_TerrainPreview.umap")
   if($proof.state -eq 'PROCEDURAL_TERRAIN_PREVIEW_SAVED_NOT_PLAYTESTED' -and $proof.originalMapHashesUnchanged -eq $true -and (Test-Path -LiteralPath $map -PathType Leaf)){
    Write-Host ('SIX_PREVIEW_SAVED='+$id)
    $results+=@{id=$id;state='NATIVE_PREVIEW_SAVED';components=$proof.landscapeComponents}
    continue
   }
  }
  $results+=@{id=$id;state='FAILED';exitCode=$ec}
  Write-Host ('SIX_PREVIEW_FAILED='+$id+'; preserving partial assets')
 }
}finally{
 $reportPath=Join-Path $runReport 'summary.json'
 @{source='procedural-preview-not-user-photo';gameplayTested=$false;results=$results}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $reportPath -Encoding UTF8
 foreach($p in $originalHashes.Keys){
  if(-not (Test-Path -LiteralPath $p -PathType Leaf) -or (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $originalHashes[$p]){throw ('PROTECTED_MAP_CHANGED: '+$p)}
 }
 Write-Host 'PROTECTED_ORIGINAL_DRAZOVIA_SKARVIK_HASHES_UNCHANGED=true'
}
if(@($results|Where-Object{$_.state -eq 'FAILED'}).Count -gt 0){throw 'Some preview worlds failed; inspect receipts and logs before retry'}
Write-Host 'SIX_NATIVE_PREVIEW_WORLDS_SAVED_NOT_PHOTO_TERRAIN=true'
