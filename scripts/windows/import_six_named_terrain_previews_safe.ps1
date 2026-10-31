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
$extraSource=Join-Path $src 'AnomaliaZPrigimaliaExtraWorldHeights.h'
$extraDest=Join-Path $native 'AnomaliaZPrigimaliaExtraWorldHeights.h'
if(-not(Test-Path -LiteralPath $extraSource -PathType Leaf)){throw 'Missing source ExtraWorldHeights C++'}
if(Test-Path -LiteralPath $extraDest){throw 'ExtraWorldHeights stage file already exists; preserve it'}
$helper=' AnomaliaZPrigimaliaExtraWorlds::EWorld ResolveAdditionalWorld('
$helperStart=$sourceText.IndexOf('namespace'+[char]10+'{'+[char]10+$helper,[StringComparison]::Ordinal)
$methodStart=$sourceText.IndexOf('AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateChernaskaluxriaLandscapeTile(',[StringComparison]::Ordinal)
$insertAt=$oldText.IndexOf('AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateArchipelagoLandscape(',[StringComparison]::Ordinal)
if($helperStart -lt 0 -or $methodStart -le $helperStart -or $insertAt -lt 0){throw 'Unexpected extra native world helper or stage insertion anchor'}
$patch=$sourceText.Substring($helperStart,$methodStart-$helperStart)
if(-not $patch.Contains('CreateNamedWorldLandscape(') -or -not $patch.Contains('NamedWorldHeight(') -or -not $patch.Contains('InspectNamedWorldPreviewComponents(') -or $patch.Contains('Subsystem->ChangeGridSize(') -or -not $patch.Contains('_TerrainPreview')){throw 'C++ map preview patch invalid'}
foreach($needle in @('CreateNamedWorldLandscape(', 'NamedWorldHeight(', 'InspectNamedWorldPreviewComponents(', 'ResolveAdditionalWorld(')){
 if($oldText.Contains($needle)){throw ('Extra world method already present; refuse duplicate: '+$needle)}
}
$newCpp=$oldText.Substring(0,$insertAt)+$patch+[Environment]::NewLine+$oldText.Substring($insertAt)
$include='#include "AnomaliaZPrigimaliaExtraWorldHeights.h"'
if(-not $newCpp.Contains($include)){
 $anchor='#include "AnomaliaZPrigimaliaWorldImportLibrary.h"'
 if(-not $newCpp.Contains($anchor)){throw 'C++ include insertion anchor missing'}
 $newCpp=$newCpp.Replace($anchor,$anchor+[Environment]::NewLine+$include)
}
foreach($additional in @('#include "Misc/CommandLine.h"','#include "Misc/Parse.h"')){
 if(-not $newCpp.Contains($additional)){
  $newCpp=$newCpp.Replace('#include "AnomaliaZPrigimaliaExtraWorldHeights.h"','#include "AnomaliaZPrigimaliaExtraWorldHeights.h"'+[Environment]::NewLine+$additional)
 }
}
$sourceHdr=[IO.File]::ReadAllText($sourceHeader)
$stagedHdr=[IO.File]::ReadAllText($header)
$anchor='static AActor* CreateArchipelagoLandscape();'
if(-not $stagedHdr.Contains($anchor)){throw 'Staged header anchor missing'}
foreach($decl in @(
 'static AActor* CreateNamedWorldLandscape(const FString& MapIdentifier);',
 'static double NamedWorldHeight(const FString& MapIdentifier,double EastMeters,double NorthMeters);',
 'static int32 InspectNamedWorldPreviewComponents(AActor* Candidate, const FString& MapIdentifier);'
)){
 if(-not $sourceHdr.Contains($decl)){throw ('Missing repository C++ declaration '+$decl)}
 if($stagedHdr.Contains($decl)){throw 'Native declaration unexpectedly already staged'}
}
$headerAddition=[Environment]::NewLine+' UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")'+[Environment]::NewLine+' static AActor* CreateNamedWorldLandscape(const FString& MapIdentifier);'
$headerAddition+=[Environment]::NewLine+' UFUNCTION(BlueprintPure, Category="ANOMALIA|World")'+[Environment]::NewLine+' static double NamedWorldHeight(const FString& MapIdentifier,double EastMeters,double NorthMeters);'
$headerAddition+=[Environment]::NewLine+' UFUNCTION(BlueprintPure, Category="ANOMALIA|World")'+[Environment]::NewLine+' static int32 InspectNamedWorldPreviewComponents(AActor* Candidate, const FString& MapIdentifier);'
$stagedHdr=$stagedHdr.Replace($anchor,$anchor+$headerAddition)
$backup=Join-Path $stage ('Saved\NamedTerrainPreviews\source-backup-'+$env:GITHUB_RUN_ID)
if(Test-Path -LiteralPath $backup){throw 'Source backup already exists for this run'}
New-Item -ItemType Directory -Path $backup|Out-Null
Copy-Item -LiteralPath $cpp -Destination (Join-Path $backup 'WorldImportLibrary.cpp.bak')
Copy-Item -LiteralPath $header -Destination (Join-Path $backup 'WorldImportLibrary.h.bak')
[IO.File]::WriteAllText($cpp,$newCpp,[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText($header,$stagedHdr,[Text.UTF8Encoding]::new($false))
Copy-Item -LiteralPath $extraSource -Destination $extraDest
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
