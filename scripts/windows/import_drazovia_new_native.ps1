# Import DRAZOVIA RAW16 ONLY into the verified isolated Unreal stage.
# Refuses to modify D:\ANOMALIA or any existing .umap / save.
$ErrorActionPreference='Stop'
$stage='D:\ANOMALIAZ-PRIGIMALIA'
$original='D:\ANOMALIA'
$project=Join-Path $stage 'unreal\AnomaliaZPrigimalia.uproject'
$projectDir=Join-Path $stage 'unreal'
$marker=Join-Path $projectDir 'Saved\BrandMigration\verified-source-backup.marker'
$rawIn=Join-Path $env:RUNNER_TEMP 'DRAZOVIA_FROM_USER\DRAZOVIA_NEW_TOPO_48KM_3025.r16'
$rawDest=Join-Path $projectDir 'TerrainSource\DRAZOVIA_NEW_REFERENCE\DRAZOVIA_NEW_TOPO_48KM_3025.r16'
$cpp=Join-Path $projectDir 'Source\AnomaliaZPrigimalia\World\AnomaliaZPrigimaliaWorldImportLibrary.cpp'
$header=Join-Path $projectDir 'Source\AnomaliaZPrigimalia\World\AnomaliaZPrigimaliaWorldImportLibrary.h'
$sourceCpp=Join-Path $env:GITHUB_WORKSPACE 'unreal\Source\AnomaliaZPrigimalia\World\AnomaliaZPrigimaliaWorldImportLibrary.cpp'
$sourceHeader=Join-Path $env:GITHUB_WORKSPACE 'unreal\Source\AnomaliaZPrigimalia\World\AnomaliaZPrigimaliaWorldImportLibrary.h'
$sourceAuthor=Join-Path $env:GITHUB_WORKSPACE 'unreal\Scripts\create_drazovia_izurvive_candidate.py'
$author=Join-Path $projectDir 'Scripts\create_drazovia_izurvive_candidate.py'
$candidate=Join-Path $projectDir 'Content\Maps\ANOMALIA_DrazoviaTopo_NewReference_Candidate.umap'
$report=Join-Path $projectDir 'Saved\DrazoviaIzurviveReferenceCandidate\first-import.json'
$expectedHash='704222bd547c6ec4a417a20e7b580aaefec1db769d18a4b331adf2ac0d263e9c'
if(-not (Test-Path -LiteralPath (Join-Path $original 'unreal\AnomaliaPrimeval.uproject'))){throw 'Original game missing. Reject.'}
if(-not (Test-Path -LiteralPath $marker) -or -not (Test-Path -LiteralPath $project)){throw 'Verified independent stage not found.'}
if(@(Get-Process UnrealEditor,UnrealEditor-Cmd,AnomaliaPrimeval,AnomaliaZPrigimalia -ErrorAction SilentlyContinue).Count -gt 0){throw 'Native game or editor currently active. Refuse concurrent edits.'}
if((Test-Path -LiteralPath $candidate) -or (Test-Path -LiteralPath $report)){throw 'This candidate already exists. No overwrites.'}
foreach($kind in @('__ExternalActors__','__ExternalObjects__')){
 $path=Join-Path $projectDir ('Content\'+$kind+'\Maps\ANOMALIA_DrazoviaTopo_NewReference_Candidate')
 if(Test-Path -LiteralPath $path){throw 'Existing candidate actor data. No overwrites.'}
}
if(-not (Test-Path -LiteralPath $rawIn) -or ((Get-Item -LiteralPath $rawIn).Length -ne 18301250)){throw 'Approved RAW16 artifact missing/truncated.'}
if((Get-FileHash -LiteralPath $rawIn -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash){throw 'RAW16 checksum differs from approved user image.'}
foreach($p in @($cpp,$header,$sourceCpp,$sourceHeader,$sourceAuthor)){
 if(-not (Test-Path -LiteralPath $p)){throw "Missing necessary source: $p"}
}
$needleCpp='AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateDrazoviaIzurviveCandidateLandscape()'
$needleAfter='AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateArchipelagoLandscape()'
$fullCpp=[IO.File]::ReadAllText($sourceCpp)
$a=$fullCpp.IndexOf($needleCpp,[StringComparison]::Ordinal)
$b=$fullCpp.IndexOf($needleAfter,$a,[StringComparison]::Ordinal)
if($a -lt 0 -or $b -le $a){throw 'Approved new C++ function missing from repository.'}
$function=$fullCpp.Substring($a,$b-$a)
if(-not $function.Contains('/Game/Maps/ANOMALIA_DrazoviaTopo_NewReference_Candidate') -or -not $function.Contains('DRAZOVIA_NEW_TOPO_48KM_3025.r16')){throw 'Wrong target/source: refuse import.'}
$existing=[IO.File]::ReadAllText($cpp)
if(-not $existing.Contains($needleCpp)){
 if(-not $existing.Contains($needleAfter)){throw 'Existing staged C++ cannot be updated conservatively.'}
 $updated=$existing.Replace($needleAfter,$function+"`r`n"+$needleAfter)
}else{$updated=$existing}
$h=[IO.File]::ReadAllText($header)
$declaration='static AActor* CreateDrazoviaIzurviveCandidateLandscape();'
if(-not $h.Contains($declaration)){
 $old='static AActor* CreateDrazoviaTopoCandidateLandscape();'
 $anchor=if($h.Contains($old)){$old}else{'static AActor* CreateArchipelagoLandscape();'}
 if(-not $h.Contains($anchor)){throw 'Existing staged C++ header has no known safe insertion point.'}
 $new=$h.Replace($anchor,$anchor+"`r`n UFUNCTION(BlueprintCallable, Category=`"ANOMALIA|World`")`r`n "+$declaration)
}else{$new=$h}
$sourceAuthorContent=[IO.File]::ReadAllText($sourceAuthor)
if(-not $sourceAuthorContent.Contains($expectedHash)){throw 'Native editor source does not validate approved SHA.'}
$editor=Join-Path $env:UE_ROOT 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$build=Join-Path $env:UE_ROOT 'Engine\Build\BatchFiles\Build.bat'
if(-not (Test-Path -LiteralPath $editor) -or -not (Test-Path -LiteralPath $build)){throw 'Installed UE editor/build not available.'}
# Hash the protected original .umap files in stage and in the original project before any writes
$protected=@(
 (Join-Path $projectDir 'Content\Maps\ANOMALIA_Inhabited_v2.umap'),
 (Join-Path $projectDir 'Content\Maps\ANOMALIA_Archipelago_v2.umap'),
 (Join-Path $original 'unreal\Content\Maps\ANOMALIA_Inhabited_v2.umap'),
 (Join-Path $original 'unreal\Content\Maps\ANOMALIA_Archipelago_v2.umap')
)
$before=@{}
foreach($file in $protected){if(Test-Path -LiteralPath $file){$before[$file]=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash}}
$backup=Join-Path $projectDir ('Saved\DrazoviaIzurviveReferenceCandidate\source-backup-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $backup -Force | Out-Null
Copy-Item -LiteralPath $cpp -Destination (Join-Path $backup 'WorldImportLibrary.cpp.bak')
Copy-Item -LiteralPath $header -Destination (Join-Path $backup 'WorldImportLibrary.h.bak')
try{
 $sourceFolder=Split-Path -Parent $rawDest
 New-Item -ItemType Directory -Path $sourceFolder -Force | Out-Null
 if(Test-Path -LiteralPath $rawDest){
  if((Get-FileHash -LiteralPath $rawDest -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash){throw 'Preexisting RAW16 differs; no overwrite.'}
 }else{Copy-Item -LiteralPath $rawIn -Destination $rawDest}
 if($updated -ne $existing){[IO.File]::WriteAllText($cpp,$updated,[Text.UTF8Encoding]::new($false))}
 if($new -ne $h){[IO.File]::WriteAllText($header,$new,[Text.UTF8Encoding]::new($false))}
 if(Test-Path -LiteralPath $author){throw 'Native author script already present; no overwrite.'}
 Copy-Item -LiteralPath $sourceAuthor -Destination $author
 Write-Host 'DRAZOVIA_NEW_R16_VERIFIED_AND_STAGED=true'
 & $build 'AnomaliaZPrigimaliaEditor' 'Win64' 'Development' "-Project=$project" '-WaitMutex' '-NoHotReloadFromIDE' '-MaxParallelActions=2'
 if($LASTEXITCODE -ne 0){throw 'Native editor C++ build failed. Candidate not imported.'}
 Write-Host 'DRAZOVIA_NATIVE_CPP_BUILD_SUCCESS=true'
 $log=Join-Path $projectDir 'Saved\DrazoviaIzurviveReferenceCandidate\unreal-import.log'
 & $editor $project '-NullRHI' '-unattended' '-nopause' '-nosound' '-run=pythonscript' "-script=$author" "-abslog=$log"
 if($LASTEXITCODE -ne 0){throw 'Native editor R16 World Partition import failed.'}
 if(-not (Test-Path -LiteralPath $candidate) -or -not (Test-Path -LiteralPath $report)){throw 'Candidate .umap or native receipt not found.'}
 $receipt=Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
 if($receipt.state -ne 'CANDIDATE_NATIVE_TERRAIN_SAVED_NOT_PLAYTESTED' -or $receipt.landscapeComponents -ne 576){throw 'Native 576 component validation failed.'}
 Write-Host 'DRAZOVIA_NATIVE_ISOLATED_CANDIDATE_576_COMPONENTS_SAVED=true'
}finally{
 foreach($file in $before.Keys){
  if(-not (Test-Path -LiteralPath $file)){throw "Protected .umap disappeared: $file"}
  if((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $before[$file]){throw "Protected .umap mutated: $file"}
 }
 Write-Host 'PROTECTED_DRAZOVIA_AND_SKARVIK_MAP_HASHES_UNCHANGED=true'
}
