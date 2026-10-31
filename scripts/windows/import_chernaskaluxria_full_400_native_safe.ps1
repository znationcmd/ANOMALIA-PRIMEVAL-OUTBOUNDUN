# Full CHERNASKALUXRIA 100km / 20x20 / 400-tile UE5.8 native import.
# Resumable and checkpointed. NEVER remove/recreate source World or overwrite
# original D:\ANOMALIA. Only adds missing tiles after native provenance checks.
$ErrorActionPreference='Stop'
$root='D:\ANOMALIAZ-PRIGIMALIA\unreal'
$original='D:\ANOMALIA\unreal\AnomaliaPrimeval.uproject'
$project=Join-Path $root 'AnomaliaZPrigimalia.uproject'
$owner=Join-Path $root 'Saved\CHERNASKALUXRIA\created-owner.json'
$tileDir=Join-Path $root 'TerrainSource\CHERNASKALUXRIA'
$firstTile=Join-Path $tileDir 'CHERNASKALUXRIA_x10_y10.r16'
$firstProof=Join-Path $root 'Saved\CHERNASKALUXRIA\CHERNASKALUXRIA_x10_y10.json'
$world=Join-Path $root 'Content\Maps\PRIGIMALIA_CHERNASKALUXRIA.umap'
$repoPy=Join-Path $env:GITHUB_WORKSPACE 'unreal\Scripts\chernaskaluxria_import_all_remaining_tiles_batch.py'
$stagePy=Join-Path $root 'Scripts\chernaskaluxria_import_all_remaining_tiles_batch.py'
$generator=Join-Path $env:GITHUB_WORKSPACE 'scripts\ue5\generate_chernaskaluxria_tiles.py'
$verify=Join-Path $env:GITHUB_WORKSPACE 'scripts\ue5\verify_chernaskaluxria_all_tile_inputs.py'
$python=Join-Path $env:UE_ROOT 'Engine\Binaries\ThirdParty\Python3\Win64\python.exe'
$editor=Join-Path $env:UE_ROOT 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$reportDir=Join-Path $env:RUNNER_TEMP ('CHERNASKALUXRIA_FULL_400_'+$env:GITHUB_RUN_ID)
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
$protected=@(
 $original,
 (Join-Path $root 'Content\Maps\ANOMALIA_Archipelago_v2.umap'),
 (Join-Path $root 'Content\Maps\ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate.umap'),
 (Join-Path $root 'Content\Maps\PRIGIMALIA_KOLCHIEM_ORIGINS_FULL.umap')
)
$hashes=@{}
$status='NOT_STARTED'
$batchRecords=@()
try {
 foreach($required in @($project,$world,$owner,$firstTile,$firstProof,$repoPy,$generator,$verify,$python,$editor)+$protected){
  if(-not(Test-Path -LiteralPath $required -PathType Leaf)){throw ('Missing source/engine or protected project: '+$required)}
 }
 $binaries=@(Get-Process -Name UnrealEditor,UnrealEditor-Cmd,UnrealBuildTool,robocopy -ErrorAction SilentlyContinue)
 if($binaries.Count -gt 0){throw 'Another editor/build/copy process active; refuse concurrent import'}
 if((Get-PSDrive -Name D).Free -lt 4GB){throw 'Insufficient D: free space to safely import remaining CH landscape tiles'}
 $ownership=Get-Content -LiteralPath $owner -Raw -Encoding UTF8|ConvertFrom-Json
 $proof=Get-Content -LiteralPath $firstProof -Raw -Encoding UTF8|ConvertFrom-Json
 if($ownership.owner -ne 'PRIGIMALIA_CHERNASKALUXRIA' -or
    $ownership.mapPackage -ne '/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA' -or
    $ownership.tilesExpected -ne 400 -or
    $proof.state -ne 'NATIVE_LANDSCAPE_TILE_SAVED_NOT_PLAYTESTED'){
   throw 'Owned first world/tile receipt does not match official initialized level'
 }
 if((Get-FileHash -LiteralPath $firstTile -Algorithm SHA256).Hash.ToLowerInvariant() -ne ([string]$proof.sourceSha256).ToLowerInvariant()){
  throw 'First native heightfield checksum mismatch'
 }
 foreach($p in $protected){$hashes[$p]=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
 $sha=(Get-FileHash -LiteralPath $repoPy -Algorithm SHA256).Hash
 if(Test-Path -LiteralPath $stagePy -PathType Leaf){
  if((Get-FileHash -LiteralPath $stagePy -Algorithm SHA256).Hash -ne $sha){throw 'Different batch importer already staged. Preserve prior importer.'}
 }else{Copy-Item -LiteralPath $repoPy -Destination $stagePy}
 Write-Host 'CHERNASKALUXRIA_FULL_IMPORT_INITIAL_STAGE_GUARDS_PASSED=true'
 # Idempotent generator rejects mismatched old sources; creates every missing tile.
 $sourceReport=Join-Path $reportDir 'all400-source-generated.json'
 & $python $generator '--output' $tileDir '--all' '--report' $sourceReport
 if($LASTEXITCODE -ne 0){throw 'Generating 400 deterministic height sources failed'}
 $checked=Join-Path $reportDir 'all400-source-verified.json'
 & $python $verify '--terrain-dir' $tileDir '--report' $checked
 if($LASTEXITCODE -ne 0){throw '400 heightfields and seams verification failed'}
 Write-Host 'CHERNASKALUXRIA_400_HEIGHTFIELDS_PRESENT_AND_SEAM_VERIFIED=true'
 $status='NATIVE_BATCH_IMPORT_IN_PROGRESS'
 # Each UnrealEditor-Cmd process saves a bounded eight-tile group, with per-tile
 # receipts on D: for safe resume after crashes, restarts or resource exhaustion.
 # Include every coordinate 0..399, including the initial x10,y10 receipt.
 for($index=0;$index -lt 400;$index+=8){
  if((Get-PSDrive -Name D).Free -lt 4GB){throw ('Low disk reserve during full import, safely paused before tile index '+$index)}
  $env:CH_ALL_TILES_START=[string]$index
  $env:CH_ALL_TILES_BATCH_COUNT=[string][Math]::Min(8,400-$index)
  $env:CH_ALL_TILES_BATCH_RECEIPT=Join-Path $reportDir ('batch-'+('{0:d3}' -f $index)+'.json')
  $log=Join-Path $reportDir ('batch-'+('{0:d3}' -f $index)+'.log')
  Write-Host ('CHERNASKALUXRIA_NATIVE_FULL_BATCH_BEGIN='+$index)
  & $editor $project '-NullRHI' '-unattended' '-nopause' '-nosound' '-run=pythonscript' "-script=$stagePy" "-abslog=$log"
  $exitCode=$LASTEXITCODE
  if(-not(Test-Path -LiteralPath $env:CH_ALL_TILES_BATCH_RECEIPT -PathType Leaf)){
   throw ('No native batch receipt after Unreal run at index '+$index+' exit='+$exitCode)
  }
  $batch=Get-Content -LiteralPath $env:CH_ALL_TILES_BATCH_RECEIPT -Raw -Encoding UTF8|ConvertFrom-Json
  $batchRecords+=,@{start=$index;status=$batch.status;saved=@($batch.saved).Count;previous=@($batch.previouslySaved).Count;exitCode=$exitCode}
  if($exitCode -ne 0 -or $batch.status -ne 'BOUNDED_NATIVE_TILE_BATCH_SAVED_NOT_PLAYTESTED' -or
     (@($batch.saved).Count+@($batch.previouslySaved).Count) -ne [Math]::Min(8,400-$index)){
    throw ('Native full-grid batch not validated at index '+$index+', stop without overwriting')
  }
  Write-Host ('CHERNASKALUXRIA_FULL_GRID_BATCH_SAVED='+$index+' NEXT='+($index+8))
 }
 # All 400 native actor saves have distinct stable provenance receipts.
 $receipts=@(Get-ChildItem -LiteralPath (Join-Path $root 'Saved\CHERNASKALUXRIA') -Filter 'CHERNASKALUXRIA_x??_y??.json' -File -ErrorAction Stop)
 if($receipts.Count -ne 400){throw ('Not all native tile receipts exist: '+$receipts.Count+'/400')}
 $seen=@{}
 for($row=0;$row -lt 20;$row++){
  for($col=0;$col -lt 20;$col++){
   $name=('CHERNASKALUXRIA_x{0:d2}_y{1:d2}' -f $col,$row)
   $receipt=Join-Path $root ('Saved\CHERNASKALUXRIA\'+$name+'.json')
   $data=Join-Path $tileDir ($name+'.r16')
   if(-not(Test-Path -LiteralPath $receipt -PathType Leaf)){throw ('Missing native tile receipt '+$name)}
   $r=Get-Content -LiteralPath $receipt -Raw -Encoding UTF8|ConvertFrom-Json
   $digest=(Get-FileHash -LiteralPath $data -Algorithm SHA256).Hash
   if($r.mapPackage -ne '/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA' -or
      $r.state -ne 'NATIVE_LANDSCAPE_TILE_SAVED_NOT_PLAYTESTED' -or
      $r.sourceSha256.ToLowerInvariant() -ne $digest.ToLowerInvariant()){
    throw ('Corrupt or mismatched native tile ledger '+$name)
   }
   $seen[$name]=$true
  }
 }
 if(-not(Test-Path -LiteralPath $world -PathType Leaf)){throw 'World disappeared during full import'}
 $external=Join-Path $root 'Content\__ExternalActors__\Maps\PRIGIMALIA_CHERNASKALUXRIA'
 $actorFiles=if(Test-Path -LiteralPath $external -PathType Container){@(Get-ChildItem -LiteralPath $external -File -Recurse -ErrorAction Stop).Count}else{0}
 if($actorFiles -lt 400){throw ('Only '+$actorFiles+' World Partition external actor packages visible after 400 native saves')}
 $status='ALL_400_LANDSCAPE_TILES_SAVED_NATIVE_WITH_CHECKPOINTS_NOT_PLAYTESTED'
 Write-Host 'CHERNASKALUXRIA_ALL_400_NATIVE_LANDSCAPE_TILES_IMPORTED=true'
 Write-Host ('CHERNASKALUXRIA_ALL_400_EXTERNAL_ACTOR_PACKAGES='+$actorFiles)
}finally{
 $changed=@()
 foreach($p in $hashes.Keys){
  if(-not(Test-Path -LiteralPath $p -PathType Leaf) -or
     (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $hashes[$p]){$changed+=,$p}
 }
 $receipts=@(Get-ChildItem -LiteralPath (Join-Path $root 'Saved\CHERNASKALUXRIA') -Filter 'CHERNASKALUXRIA_x??_y??.json' -File -ErrorAction SilentlyContinue)
 $summary=@{status=$status;nativeTileReceiptCount=$receipts.Count;expectedTiles=400;
   nativeSource='PROCEDURAL_PREVIEW_NOT_FINAL_USER_PHOTO';
   protectedMapHashChanges=@($changed);
   gameplayTested=$false;worldPartitionStreamingTested=$false;batches=$batchRecords}
 $summary | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $reportDir 'summary.json') -Encoding UTF8
 if($changed.Count -gt 0){throw ('Protected original map modified unexpectedly: '+($changed -join ','))}
 Write-Host 'CHERNASKALUXRIA_ALL_OTHER_MAP_HASHES_UNCHANGED=true'
}
