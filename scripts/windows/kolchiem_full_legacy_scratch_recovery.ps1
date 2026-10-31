# Attempt native duplication of the REAL legacy 7584-actor World in an isolated
# C: scratch project. Never modify D:\ANOMALIA or existing stage World assets.
# Only promote a distinctly named FULL candidate after independent count checks.
$ErrorActionPreference='Stop'
$orig='D:\ANOMALIA\unreal'
$stage='D:\ANOMALIAZ-PRIGIMALIA\unreal'
$stem='ANOMALIA_Inhabited_v2'
$targetStem='PRIGIMALIA_KOLCHIEM_ORIGINS_FULL'
$originalMap=Join-Path $orig ("Content\Maps\"+$stem+'.umap')
$originalActors=Join-Path $orig ("Content\__ExternalActors__\Maps\"+$stem)
$stageMap=Join-Path $stage 'Content\Maps\PRIGIMALIA_KOLCHIEM_ORIGINS.umap'
$targetMap=Join-Path $stage ("Content\Maps\"+$targetStem+'.umap')
$targetActors=Join-Path $stage ("Content\__ExternalActors__\Maps\"+$targetStem)
$targetObjects=Join-Path $stage ("Content\__ExternalObjects__\Maps\"+$targetStem)
$editor=Join-Path $env:UE_ROOT 'Engine\Binaries\Win64\UnrealEditor.exe'
$reportDir=Join-Path $env:RUNNER_TEMP ('KOLCHIEM_FULL_RECOVERY_'+$env:GITHUB_RUN_ID)
$scratch=Join-Path $reportDir 'ScratchAnomaliaUnreal'
$report=Join-Path $reportDir 'summary.json'
New-Item -ItemType Directory -Path $reportDir -Force|Out-Null
$state='FAILED_NOT_COPIED_TO_STAGE'
$results=@{status=$state;sourceOriginalMap=$originalMap;originalProjectChanged=$false;existingKolchiemChanged=$false;legacyActorsMigrated=$false;gameplayTested=$false;previewWarning='Must verify authored buildings, collision and gameplay before release'}
$protected=@(
 $originalMap,
 $stageMap,
 (Join-Path $stage 'Content\Maps\PRIGIMALIA_Inhabited_v2.umap'),
 (Join-Path $stage 'Content\Maps\ANOMALIA_Inhabited_v2.umap'),
 (Join-Path $stage 'Content\Maps\ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate.umap'),
 (Join-Path $stage 'Content\Maps\ANOMALIA_Archipelago_v2.umap'),
 (Join-Path $orig 'AnomaliaPrimeval.uproject')
)
$hashes=@{}
try{
  if(-not(Test-Path -LiteralPath (Join-Path $stage 'Saved\BrandMigration\verified-source-backup.marker') -PathType Leaf)){throw 'No verified staged source backup'}
  foreach($f in @($originalMap,(Join-Path $stage 'AnomaliaZPrigimalia.uproject'),$stageMap,$editor)){
    if(-not(Test-Path -LiteralPath $f -PathType Leaf)){throw ('Required file missing: '+$f)}
  }
  foreach($p in $protected){if(-not(Test-Path -LiteralPath $p -PathType Leaf)){throw ('Protected map missing: '+$p)};$hashes[$p]=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
  if(-not(Test-Path -LiteralPath $originalActors -PathType Container)){throw 'Original 7584-actor folder missing'}
  $srcFiles=@(Get-ChildItem -LiteralPath $originalActors -File -Recurse -ErrorAction Stop)
  if($srcFiles.Count -lt 7500){throw ('Refuse to recover incomplete legacy World: '+$srcFiles.Count)}
  $sourceBytes=[long](($srcFiles|Measure-Object -Property Length -Sum).Sum)
  $results['sourceOriginalExternalActors']=$srcFiles.Count
  $results['sourceOriginalExternalActorBytes']=$sourceBytes
  Write-Host ('KOLCHIEM_LEGACY_SOURCE_ACTORS='+$srcFiles.Count)
  foreach($dir in @($targetMap,$targetActors,$targetObjects,$scratch)){
    if(Test-Path -LiteralPath $dir){throw ('Existing target/scratch preserved, no overwrite: '+$dir)}
  }
  if(@(Get-Process UnrealEditor,UnrealEditor-Cmd,UnrealBuildTool,robocopy -ErrorAction SilentlyContinue).Count -gt 0){throw 'Other UE/backup/copy running; refuse concurrency'}
  $freeC=(Get-PSDrive -Name C).Free
  $freeD=(Get-PSDrive -Name D).Free
  if($freeC -lt 8GB+4*$sourceBytes -or $freeD -lt 6GB){throw 'Insufficient independent scratch/project storage; no change attempted'}
  # Minimal scratch project: Config and precompiled module plus exact source level
  # and original World Partition actors. Never create junctions/symlinks to user data.
  New-Item -ItemType Directory -Path (Join-Path $scratch 'Content\Maps') -Force|Out-Null
  New-Item -ItemType Directory -Path (Join-Path $scratch 'Content\__ExternalActors__\Maps') -Force|Out-Null
  Copy-Item -LiteralPath (Join-Path $stage 'AnomaliaZPrigimalia.uproject') -Destination (Join-Path $scratch 'AnomaliaZPrigimalia.uproject')
  Copy-Item -LiteralPath (Join-Path $stage 'Config') -Destination (Join-Path $scratch 'Config') -Recurse
  if(Test-Path -LiteralPath (Join-Path $stage 'Binaries') -PathType Container){
    Copy-Item -LiteralPath (Join-Path $stage 'Binaries') -Destination (Join-Path $scratch 'Binaries') -Recurse
  }
  Copy-Item -LiteralPath $originalMap -Destination (Join-Path $scratch 'Content\Maps\ANOMALIA_Inhabited_v2.umap')
  Copy-Item -LiteralPath $originalActors -Destination (Join-Path $scratch 'Content\__ExternalActors__\Maps\ANOMALIA_Inhabited_v2') -Recurse
  $sourceObjects=Join-Path $orig 'Content\__ExternalObjects__\Maps\ANOMALIA_Inhabited_v2'
  if(Test-Path -LiteralPath $sourceObjects){
    New-Item -ItemType Directory -Path (Join-Path $scratch 'Content\__ExternalObjects__\Maps') -Force | Out-Null
    Copy-Item -LiteralPath $sourceObjects -Destination (Join-Path $scratch 'Content\__ExternalObjects__\Maps\ANOMALIA_Inhabited_v2') -Recurse
  }
  $scratchSourceMap=Join-Path $scratch 'Content\Maps\ANOMALIA_Inhabited_v2.umap'
  if((Get-FileHash $scratchSourceMap -Algorithm SHA256).Hash -ne $hashes[$originalMap]){throw 'Original map byte-for-byte copy failed'}
  $copiedActorCount=@(Get-ChildItem -LiteralPath (Join-Path $scratch 'Content\__ExternalActors__\Maps\ANOMALIA_Inhabited_v2') -File -Recurse).Count
  if($copiedActorCount -ne $srcFiles.Count){throw ('Original external actor copy incomplete '+$copiedActorCount+'/'+$srcFiles.Count)}
  Write-Host 'KOLCHIEM_LEGACY_WORLD_CLONED_TO_ISOLATED_C_SCRATCH=true'
  $scratchProject=Join-Path $scratch 'AnomaliaZPrigimalia.uproject'
  $sourcePackage='/Game/Maps/ANOMALIA_Inhabited_v2'
  $targetPackage='/Game/Maps/'+$targetStem
  $log=Join-Path $reportDir 'original-legacy-native-duplicate.log'
  $args=@($scratchProject,$sourcePackage,'-NullRHI','-unattended','-nopause','-nosound','-run=WorldPartitionBuilderCommandlet',
          '-SCCProvider=None','-builder=WorldPartitionRenameDuplicateBuilder',"-NewPackage=$targetPackage","-abslog=$log")
  $proc=Start-Process -FilePath $editor -ArgumentList $args -Wait -PassThru -ErrorAction Stop
  $ec=[int]$proc.ExitCode
  $results['scratchBuilderExit']=$ec
  Write-Host ('KOLCHIEM_LEGACY_NATIVE_BUILDER_EXIT='+$ec)
  if($ec -ne 0){throw 'Isolated legacy native duplicate failed: inspect scratch commandlet log (no installed map modified)'}
  $scratchDest=Join-Path $scratch ("Content\Maps\"+$targetStem+'.umap')
  $scratchActors=Join-Path $scratch ("Content\__ExternalActors__\Maps\"+$targetStem)
  $scratchObjects=Join-Path $scratch ("Content\__ExternalObjects__\Maps\"+$targetStem)
  if(-not(Test-Path -LiteralPath $scratchDest -PathType Leaf)){throw 'Scratch duplicate .umap missing'}
  if(-not(Test-Path -LiteralPath $scratchActors -PathType Container)){throw 'Scratch duplicate actor folder missing'}
  $copied=@(Get-ChildItem -LiteralPath $scratchActors -File -Recurse -ErrorAction Stop)
  $results['scratchDuplicateActorCount']=$copied.Count
  Write-Host ('KOLCHIEM_LEGACY_DUPLICATE_ACTORS='+$copied.Count)
  if($copied.Count -lt [Math]::Ceiling($srcFiles.Count*.99)){throw ('Original world actors not replicated sufficiently: '+$copied.Count+'/'+$srcFiles.Count)}
  # Critical: no unresolved dependencies or missing /Game assets may be silently
  # accepted as a production copy from this intentionally minimal scratch project.
  $logText=Get-Content -LiteralPath $log -Raw -Encoding UTF8
  if($logText -match '(?im)Log(Linker|Streaming): (Warning|Error):.*(Failed to load|Can.t find file|Missing)'){
    throw 'Legacy scratch build has missing asset dependencies; refuse production copy'
  }
  foreach($path in @($targetMap,$targetActors,$targetObjects)){
    if(Test-Path -LiteralPath $path){throw ('Someone created new destination during scratch import: '+$path)}
  }
  Copy-Item -LiteralPath $scratchDest -Destination $targetMap
  Copy-Item -LiteralPath $scratchActors -Destination $targetActors -Recurse
  if(Test-Path -LiteralPath $scratchObjects){Copy-Item -LiteralPath $scratchObjects -Destination $targetObjects -Recurse}
  $installedActorCount=@(Get-ChildItem -LiteralPath $targetActors -File -Recurse -ErrorAction Stop).Count
  if($installedActorCount -ne $copied.Count){throw 'Install actor count mismatch; retain partial new package for inspection'}
  $results['installedActorCount']=$installedActorCount
  $results['nativeMapPackage']=$targetPackage
  $results['status']='LEGACY_7584_ACTOR_FULL_COPY_INSTALLED_PENDING_NATIVE_REOPEN'
  $results['legacyActorsMigrated']=$true
  Write-Host 'KOLCHIEM_ORIGINS_FULL_LEGACY_WORLD_IMPORTED=true'
} catch {
  $results['error']=$_.Exception.Message
  Write-Host ('KOLCHIEM_FULL_SCRATCH_ATTEMPT_BLOCKED='+$_.Exception.Message)
  throw
} finally {
  $changes=@()
  foreach($p in $hashes.Keys){
    if(-not(Test-Path -LiteralPath $p -PathType Leaf) -or (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $hashes[$p]){$changes+=,$p}
  }
  $results['protectedHashChanges']=@($changes)
  $results|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $report -Encoding UTF8
  if($changes.Count -gt 0){throw ('PROTECTED_EXISTING_WORLD_CHANGED: '+($changes -join ','))}
  Write-Host 'KOLCHIEM_FULL_RECOVERY_PROTECTED_PROJECTS_UNCHANGED=true'
}
