# Import first real UE5.8 native landscape tile of the 100km CHERNASKALUXRIA
# world, from deterministic 5km provisional heightmap. Other 399 tiles pending.
# Never modify original D:\ANOMALIA; never replace existing maps or sources.
$ErrorActionPreference='Stop'
$root='D:\ANOMALIAZ-PRIGIMALIA\unreal'
$project=Join-Path $root 'AnomaliaZPrigimalia.uproject'
$original='D:\ANOMALIA\unreal\AnomaliaPrimeval.uproject'
$marker=Join-Path $root 'Saved\BrandMigration\verified-source-backup.marker'
$native=Join-Path $root 'Source\AnomaliaZPrigimalia\World'
$repoNative=Join-Path $env:GITHUB_WORKSPACE 'unreal\Source\AnomaliaZPrigimalia\World'
$cpp=Join-Path $native 'AnomaliaZPrigimaliaWorldImportLibrary.cpp'
$header=Join-Path $native 'AnomaliaZPrigimaliaWorldImportLibrary.h'
$repoCpp=Join-Path $repoNative 'AnomaliaZPrigimaliaWorldImportLibrary.cpp'
$repoHeader=Join-Path $repoNative 'AnomaliaZPrigimaliaWorldImportLibrary.h'
$pythonRepo=Join-Path $env:GITHUB_WORKSPACE 'unreal\Scripts\create_chernaskaluxria_native_safe_v2.py'
$pythonStage=Join-Path $root 'Scripts\create_chernaskaluxria_native_safe_v2.py'
$sourceScript=Join-Path $env:GITHUB_WORKSPACE 'scripts\ue5\generate_chernaskaluxria_tiles.py'
$enginePy=Join-Path $env:UE_ROOT 'Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$editor=Join-Path $env:UE_ROOT 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$build=Join-Path $env:UE_ROOT 'Engine\Build\BatchFiles\Build.bat'
$map=Join-Path $root 'Content\Maps\PRIGIMALIA_CHERNASKALUXRIA.umap'
$external=Join-Path $root 'Content\__ExternalActors__\Maps\PRIGIMALIA_CHERNASKALUXRIA'
$raw=Join-Path $root 'TerrainSource\CHERNASKALUXRIA\CHERNASKALUXRIA_x10_y10.r16'
$legacyReceipt=Join-Path $root 'Saved\CHERNASKALUXRIA\created-owner.json'
$reportDir=Join-Path $env:RUNNER_TEMP ('ANOMALIA_CHERNASKALUXRIA_PILOT_'+$env:GITHUB_RUN_ID)
New-Item -ItemType Directory -Path $reportDir -Force|Out-Null
foreach($file in @($project,$original,$marker,$cpp,$header,$repoCpp,$repoHeader,$pythonRepo,$sourceScript,$enginePy,$editor,$build)){
 if(-not(Test-Path -LiteralPath $file -PathType Leaf)){throw ('Required file not found: '+$file)}
}
if(@(Get-Process UnrealEditor,UnrealEditor-Cmd,UnrealBuildTool,robocopy -ErrorAction SilentlyContinue).Count -gt 0){throw 'Another Unreal task running; refuse concurrent import'}
foreach($p in @($map,$external,$legacyReceipt,$pythonStage)){
 if(Test-Path -LiteralPath $p){throw ('CHERNASKALUXRIA earlier partial native work is preserved: '+$p)}
}
if((Get-PSDrive D).Free -lt 5GB){throw 'Insufficient D: disk space; do not start native build'}
$protected=@(
 $original,
 (Join-Path $root 'Content\Maps\ANOMALIA_Archipelago_v2.umap'),
 (Join-Path $root 'Content\Maps\ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate.umap'),
 (Join-Path $root 'Content\Maps\PRIGIMALIA_KOLCHIEM_ORIGINS_FULL.umap')
)
$hashes=@{}
foreach($f in $protected){if(-not(Test-Path -LiteralPath $f -PathType Leaf)){throw ('Protected map missing: '+$f)};$hashes[$f]=(Get-FileHash $f -Algorithm SHA256).Hash}
$src=[IO.File]::ReadAllText($repoCpp)
$dst=[IO.File]::ReadAllText($cpp)
$headRepo=[IO.File]::ReadAllText($repoHeader)
$headDst=[IO.File]::ReadAllText($header)
$open='AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateChernaskaluxriaLandscapeTile('
$next='TArray<FVector2D> UAnomaliaZPrigimaliaWorldImportLibrary::InhabitedSettlementSites()'
$a=$src.IndexOf($open,[StringComparison]::Ordinal)
$b=$src.IndexOf($next,$a,[StringComparison]::Ordinal)
$addBefore=$dst.IndexOf('AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateArchipelagoLandscape(',[StringComparison]::Ordinal)
if($a -lt 0 -or $b -le $a -or $addBefore -lt 0){throw 'Native C++ sources have unexpected layout'}
$patch=$src.Substring($a,$b-$a)
if($patch.Contains('Subsystem->ChangeGridSize(') -or -not $patch.Contains('InspectChernaskaluxriaTileComponents') -or -not $patch.Contains('LandscapeComponents.Num()!=4')){throw 'Native CHERNASKALUXRIA C++ patch validation failed'}
if($dst.Contains($open) -or $dst.Contains('InspectChernaskaluxriaTileComponents(')){throw 'CHERNASKALUXRIA native code already staged: do not overwrite'}
$dst=$dst.Substring(0,$addBefore)+$patch+[Environment]::NewLine+$dst.Substring($addBefore)
$anchor='static AActor* CreateArchipelagoLandscape();'
$chDecl='static AActor* CreateChernaskaluxriaLandscapeTile(int32 Col,int32 Row);'
$chInspect='static int32 InspectChernaskaluxriaTileComponents(AActor* Candidate);'
if(-not $headDst.Contains($anchor) -or $headDst.Contains($chDecl) -or
   -not $headRepo.Contains($chInspect)){throw 'Staged native header incompatible or CH importer already present'}
$add=[Environment]::NewLine+' UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")'+[Environment]::NewLine+' '+$chDecl
$add+=[Environment]::NewLine+' UFUNCTION(BlueprintPure, Category="ANOMALIA|World")'+[Environment]::NewLine+' '+$chInspect
$headDst=$headDst.Replace($anchor,$anchor+$add)
$backup=Join-Path $root ('Saved\CHERNASKALUXRIA\NativeSourceBackup_'+$env:GITHUB_RUN_ID)
if(Test-Path -LiteralPath $backup){throw 'Existing run backup must be preserved'}
New-Item -ItemType Directory -Path $backup -Force|Out-Null
Copy-Item -LiteralPath $cpp -Destination (Join-Path $backup 'WorldImportLibrary.cpp.bak')
Copy-Item -LiteralPath $header -Destination (Join-Path $backup 'WorldImportLibrary.h.bak')
$state='FAILED_NATIVE_IMPORT'
try{
 $srcOut=Join-Path $reportDir 'raw-source'
 New-Item -ItemType Directory -Path $srcOut|Out-Null
 $sourceReport=Join-Path $reportDir 'source-manifest.json'
 & $enginePy $sourceScript '--output' $srcOut '--col' '10' '--row' '10' '--count' '1' '--report' $sourceReport
 if($LASTEXITCODE -ne 0){throw 'Generator of center height tile failed'}
 $generated=Join-Path $srcOut 'CHERNASKALUXRIA_x10_y10.r16'
 if(-not(Test-Path -LiteralPath $generated -PathType Leaf) -or (Get-Item $generated).Length -ne 253*253*2){throw 'Invalid generated CHERNASKALUXRIA height tile'}
 $hash=(Get-FileHash $generated -Algorithm SHA256).Hash
 if(Test-Path -LiteralPath $raw){
  if((Get-FileHash $raw -Algorithm SHA256).Hash -ne $hash){throw 'Existing CHERNASKALUXRIA source differs; do not overwrite'}
 }else{
  $folder=Split-Path $raw -Parent
  if(-not(Test-Path -LiteralPath $folder)){New-Item -ItemType Directory -Path $folder -Force|Out-Null}
  Copy-Item -LiteralPath $generated -Destination $raw
 }
 [IO.File]::WriteAllText($cpp,$dst,[Text.UTF8Encoding]::new($false))
 [IO.File]::WriteAllText($header,$headDst,[Text.UTF8Encoding]::new($false))
 Copy-Item -LiteralPath $pythonRepo -Destination $pythonStage
 Write-Host 'CHERNASKALUXRIA_NATIVE_IMPORTER_STAGED_WITHOUT_MAP_OVERWRITE=true'
 & $build AnomaliaZPrigimaliaEditor Win64 Development "-Project=$project" -WaitMutex -NoHotReloadFromIDE -MaxParallelActions=2
 if($LASTEXITCODE -ne 0){throw 'UE5.8 C++ compilation for CHERNASKALUXRIA failed'}
 Write-Host 'CHERNASKALUXRIA_NATIVE_CPP_BUILD_SUCCESS=true'
 $env:PRIGIMALIA_CH_MODE='initialize'
 $env:PRIGIMALIA_CH_COL='10'
 $env:PRIGIMALIA_CH_ROW='10'
 $env:PRIGIMALIA_CH_REPORT=Join-Path $reportDir 'native-import.json'
 $log=Join-Path $reportDir 'native-import.log'
 & $editor $project '-NullRHI' '-unattended' '-nopause' '-nosound' '-run=pythonscript' "-script=$pythonStage" "-abslog=$log"
 if($LASTEXITCODE -ne 0){throw 'UE5 native pilot tile import failed; preserve partial map for manual inspection'}
 if(-not(Test-Path -LiteralPath $env:PRIGIMALIA_CH_REPORT -PathType Leaf)){throw 'Missing native UE import receipt'}
 $r=Get-Content -LiteralPath $env:PRIGIMALIA_CH_REPORT -Raw -Encoding UTF8|ConvertFrom-Json
 if($r.state -ne 'NATIVE_PARTIAL_WORLD_SAVED_NOT_PLAYTESTED' -or $r.completedNativeTiles -ne 1){throw 'UE CH native level did not confirm one pilot terrain tile'}
 if(-not(Test-Path -LiteralPath $map -PathType Leaf)){throw 'No genuine CHERNASKALUXRIA .umap'}
 $state='FIRST_1_OF_400_NATIVE_TERRAIN_TILE_SAVED_NOT_PLAYTESTED'
 Write-Host 'CHERNASKALUXRIA_WORLD_FIRST_TILE_NATIVE_IMPORT_SUCCESS_1_OF_400=true'
}finally{
 $changes=@()
 foreach($p in $hashes.Keys){
  if(-not(Test-Path -LiteralPath $p -PathType Leaf) -or (Get-FileHash $p -Algorithm SHA256).Hash -ne $hashes[$p]){$changes+=,$p}
 }
 @{status=$state;completedNativeTiles=$(if($state -like 'FIRST*'){1}else{0});
   plannedNativeTiles=400;sourceType='deterministic-provisional-not-user-final-topography';
   protectedMapHashChanges=@($changes);gameplayTested=$false
 }|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $reportDir 'summary.json') -Encoding UTF8
 if($changes.Count -gt 0){throw ('Protected project maps changed unexpectedly: '+($changes -join ','))}
 Write-Host 'CHERNASKALUXRIA_OTHER_MAP_HASHES_PRESERVED=true'
}
