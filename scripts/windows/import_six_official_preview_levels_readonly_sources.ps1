# Native UE5.8: duplicate six already-authored provisional TerrainPreview worlds
# into distinct stable official packages WITHOUT deleting/renaming source previews.
# This is NOT import of the user's final referenced coastlines/topographies.
$ErrorActionPreference='Stop'
$root='D:\ANOMALIAZ-PRIGIMALIA\unreal'
$project=Join-Path $root 'AnomaliaZPrigimalia.uproject'
$original='D:\ANOMALIA\unreal\AnomaliaPrimeval.uproject'
$marker=Join-Path $root 'Saved\BrandMigration\verified-source-backup.marker'
$engine=Join-Path $env:UE_ROOT 'Engine\Binaries\Win64\UnrealEditor.exe'
$cmd=Join-Path $env:UE_ROOT 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$names=@('KARSKOV','VORGRAD','NEMORIS','DRAKHEIM','SOLYNACALYRA','NEXAVARKHOS')
$reportDir=Join-Path $env:RUNNER_TEMP ('ANOMALIA_6_OFFICIAL_IMPORT_'+$env:GITHUB_RUN_ID)
New-Item -ItemType Directory -Path $reportDir -Force|Out-Null
$results=@()
$protected=@(
$original,
(Join-Path $root 'Content\Maps\ANOMALIA_Archipelago_v2.umap'),
(Join-Path $root 'Content\Maps\ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate.umap'),
(Join-Path $root 'Content\Maps\PRIGIMALIA_KOLCHIEM_ORIGINS_FULL.umap')
)
foreach($item in @($project,$marker,$engine,$cmd)+$protected){
 if(-not(Test-Path -LiteralPath $item -PathType Leaf)){throw ('Missing protected project, engine, or map: '+$item)}
}
foreach($dir in @('D:\ANOMALIA','D:\ANOMALIAZ-PRIGIMALIA',$root)){
 if((Get-Item -LiteralPath $dir).Attributes -band [IO.FileAttributes]::ReparsePoint){throw ('Linked project root prohibited: '+$dir)}
}
if(@(Get-Process -Name UnrealEditor,UnrealEditor-Cmd,UnrealBuildTool,robocopy -ErrorAction SilentlyContinue).Count -gt 0){throw 'Another native editor/build/backup is active; cannot import concurrently'}
$before=@{}
foreach($item in $protected){$before[$item]=(Get-FileHash -LiteralPath $item -Algorithm SHA256).Hash}
foreach($name in $names){
 $source=Join-Path $root ('Content\Maps\PRIGIMALIA_'+$name+'_TerrainPreview.umap')
 if(-not(Test-Path -LiteralPath $source -PathType Leaf)){throw ('Missing native provisional source: '+$name)}
 $before[$source]=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
}
$drive=Get-PSDrive -Name D
if($drive.Free -lt 5GB){throw ('Not enough free D: capacity for safe independent map duplication: '+[Math]::Round($drive.Free/1GB,2)+'GiB')}
Write-Host ('SIX_OFFICIAL_PREVIEW_IMPORT_FREE_GIB='+[Math]::Round($drive.Free/1GB,2))
$state='FAILED'
try{
 foreach($name in $names){
  $sourcePackage='/Game/Maps/PRIGIMALIA_'+$name+'_TerrainPreview'
  $targetPackage='/Game/Maps/PRIGIMALIA_'+$name
  $target=Join-Path $root ('Content\Maps\PRIGIMALIA_'+$name+'.umap')
  $external=Join-Path $root ('Content\__ExternalActors__\Maps\PRIGIMALIA_'+$name)
  $extObj=Join-Path $root ('Content\__ExternalObjects__\Maps\PRIGIMALIA_'+$name)
  $sourceActor=Join-Path $root ('Content\__ExternalActors__\Maps\PRIGIMALIA_'+$name+'_TerrainPreview')
  $row=@{name=$name;source=$sourcePackage;target=$targetPackage;status='NOT_ATTEMPTED';isOriginalPhotoTopography=$false;gameplayTested=$false}
  # Never overwrite existing or half-imported target.
  if((Test-Path -LiteralPath $target) -or (Test-Path -LiteralPath $external) -or (Test-Path -LiteralPath $extObj)){
    $row.status='SKIPPED_EXISTING_OR_PARTIAL_TARGET'
    $results+=,$row
    Write-Host ('MAP_SKIP_EXISTING_OR_PARTIAL_TARGET='+$name)
    continue
  }
  $actorCount=if(Test-Path -LiteralPath $sourceActor){@(Get-ChildItem -LiteralPath $sourceActor -File -Recurse).Count}else{0}
  $row.sourceExternalActorCount=$actorCount
  $log=Join-Path $reportDir ($name+'.log')
  $args=@($project,$sourcePackage,'-NullRHI','-unattended','-nopause','-nosound',
         '-run=WorldPartitionBuilderCommandlet','-SCCProvider=None',
         '-builder=WorldPartitionRenameDuplicateBuilder',"-NewPackage=$targetPackage","-abslog=$log")
  Write-Host ('OFFICIAL_PROVISIONAL_LEVEL_BEGIN='+$name)
  $p=Start-Process -FilePath $engine -ArgumentList $args -Wait -PassThru -ErrorAction Stop
  $row.exitCode=[int]$p.ExitCode
  if($p.ExitCode -ne 0){
    $row.status='NATIVE_DUPLICATE_FAILED'
    $results+=,$row
    Write-Host ('OFFICIAL_PROVISIONAL_LEVEL_FAILED='+$name+' EXIT='+$p.ExitCode)
    continue
  }
  if(-not(Test-Path -LiteralPath $target -PathType Leaf) -or (Get-Item -LiteralPath $target).Length -lt 1024){
    $row.status='MISSING_NATIVE_TARGET_UMAP'
    $results+=,$row
    Write-Host ('OFFICIAL_PROVISIONAL_LEVEL_NO_UMAP='+$name)
    continue
  }
  $outCount=if(Test-Path -LiteralPath $external){@(Get-ChildItem -LiteralPath $external -File -Recurse).Count}else{0}
  $row.duplicateExternalActorCount=$outCount
  if($actorCount -gt 0 -and $outCount -lt $actorCount){
    $row.status='ACTOR_COUNT_MISMATCH_DO_NOT_USE'
    $results+=,$row
    Write-Host ('OFFICIAL_PROVISIONAL_ACTORS_MISMATCH='+$name+' SOURCE='+$actorCount+' OUTPUT='+$outCount)
    continue
  }
  $row.status='NATIVE_PROVISIONAL_LEVEL_DUPLICATED_PENDING_RELOAD'
  $results+=,$row
  Write-Host ('OFFICIAL_PROVISIONAL_LEVEL_CREATED='+$name+' ACTORS='+$outCount)
 }
}finally{
 $changes=@()
 foreach($key in $before.Keys){
  if(-not(Test-Path -LiteralPath $key -PathType Leaf) -or (Get-FileHash -LiteralPath $key -Algorithm SHA256).Hash -ne $before[$key]){$changes+=,$key}
 }
 $receipt=@{runId=$env:GITHUB_RUN_ID;mode='native-duplicate-preview-worlds-without-renaming';worlds=$results;protectedWorldHashChanges=@($changes);finalTopographiesImported=$false;gameplayTested=$false}
 $receipt|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $reportDir 'results.json') -Encoding UTF8
 if($changes.Count -gt 0){throw ('PROTECTED_EXISTING_LEVEL_CHANGED: '+($changes -join ', '))}
 Write-Host 'SIX_OFFICIAL_PREVIEW_PROTECTED_MAP_HASHES_UNCHANGED=true'
}
$failed=@($results|Where-Object{$_.status -ne 'NATIVE_PROVISIONAL_LEVEL_DUPLICATED_PENDING_RELOAD'})
if($failed.Count -gt 0){throw ('Not all six native map duplications succeeded; review results.json: '+$failed.Count+' incomplete')}
Write-Host 'SIX_OFFICIAL_PROVISIONAL_NATIVE_LEVELS_CREATED_PENDING_RELOAD=true'
