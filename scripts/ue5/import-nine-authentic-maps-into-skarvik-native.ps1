# Import only nine genuine UE5 map packages from the older original/migrated
# projects into the C:\ native world containing SKARVIK FINAL and four new maps.
# Never follow external source reparse points, never overwrite different packages.
# Never manufacture FALC from missing heightmap artwork.
[CmdletBinding()]
param([string]$ReportPath=(Join-Path $env:RUNNER_TEMP 'anomaliaz-existing-14-maps-import.json'))
$ErrorActionPreference='Stop'
$stage='C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal'
$stageContent=Join-Path $stage 'Content'
$migrated='D:\ANOMALIAZ\02_Projet_Migration\unreal\Content'
$original='D:\ANOMALIA\unreal\Content'
$marker=Join-Path $stage '.skarvik-ci-stage-marker'
$records=@(
 @{name='DRAZOVIA';package='ANOMALIA_Inhabited_v2';from=$original},
 @{name='KARSKOV';package='PRIGIMALIA_KARSKOV';from=$migrated},
 @{name='VORGRAD';package='PRIGIMALIA_VORGRAD';from=$migrated},
 @{name='NEMORIS';package='PRIGIMALIA_NEMORIS';from=$migrated},
 @{name='DRAKHEIM';package='PRIGIMALIA_DRAKHEIM';from=$migrated},
 @{name='SOLYNACALYRA';package='PRIGIMALIA_SOLYNACALYRA';from=$migrated},
 @{name='NEXAVARKHOS';package='PRIGIMALIA_NEXAVARKHOS';from=$migrated},
 @{name='CHERNASKALUXRIA';package='PRIGIMALIA_CHERNASKALUXRIA';from=$migrated},
 @{name='KOLCHIEM ORIGINS';package='PRIGIMALIA_KOLCHIEM_ORIGINS';from=$migrated}
)
$report=[ordered]@{
 state='PRECHECK'
 stage=$stage
 existingNativeSkarvikMap='/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1'
 preservedFourNewNames=@('PRIGIMALIA_ROSKATVIA_B1','PRIGIMALIA_NOGOKV_51','PRIGIMALIA_PARADISIOMANIA','PRIGIMALIA_DEADROOT')
 nativeWorldSourcesPreserved=$true
 originalsOnDPreserved=$true
 realFalcHeightmapMissing=$true
 realFalcMapNotInvented=$true
 userEditorAssetsNotOverwritten=$true
 packageFilesStaged=0
 externalActorFilesStaged=0
 hashesVerified=0
 createdBytes=0
 worlds=@()
 resultExpectedMapCount=14
 target15WorldsFullPlayable=$false
 exactUnrealLoadingStillRequiresTest=$true
 cFreeGiBBefore=0
 cFreeGiBAfter=0
 error=$null
}
function Sha([string]$file){(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash}
function IsReparse([string]$path){((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0}
function Save {
 $folder=Split-Path -Parent $ReportPath
 if(!(Test-Path -LiteralPath $folder)){New-Item -ItemType Directory -Path $folder -Force|Out-Null}
 ($report|ConvertTo-Json -Depth 9)|Set-Content -LiteralPath $ReportPath -Encoding UTF8
}
$created=New-Object 'System.Collections.Generic.List[string]'
try{
 if(!(Test-Path -LiteralPath $marker) -or (Get-Content -LiteralPath $marker -Raw).Trim() -ne '41188816555'){
   throw 'Original native SKARVIK stage owner not verified'
 }
 foreach($world in @('PRIGIMALIA_SKARVIK_FINAL_v1','PRIGIMALIA_ROSKATVIA_B1','PRIGIMALIA_NOGOKV_51','PRIGIMALIA_PARADISIOMANIA','PRIGIMALIA_DEADROOT')){
   if(!(Test-Path -LiteralPath (Join-Path $stageContent ('Maps\'+$world+'.umap')))){throw ('Protected real existing map missing '+$world)}
 }
 if(@(Get-Process -Name UnrealEditor,UnrealEditor-Cmd,AnomaliaZPrigimalia,AnomaliaPrimeval,ShaderCompileWorker,UnrealBuildTool,MSBuild -ErrorAction SilentlyContinue).Count){
   throw 'Real Unreal Editor/compile is running; no shared world files will be altered'
 }
 $c=[IO.DriveInfo]::new('C')
 $report.cFreeGiBBefore=[math]::Round($c.AvailableFreeSpace/1GB,3)
 if($c.AvailableFreeSpace -lt 18GB){throw 'At least 18GB must remain free before map imports'}
 if(!(Test-Path -LiteralPath $migrated) -or !(Test-Path -LiteralPath $original)){throw 'Existing original/migration Content folders missing'}
 # All-source preflight, no directory traversal through junctions.
 $plan=New-Object 'System.Collections.Generic.List[object]'
 [long]$neededBytes=0
 foreach($item in $records){
   $world=$item.package;$srcContent=$item.from
   $file=(Join-Path $srcContent ('Maps\'+$world+'.umap'))
   if(!(Test-Path -LiteralPath $file -PathType Leaf)){throw ('Original genuine map not found '+$item.name)}
   if(IsReparse $file){throw ('Genuine map source is a symlink '+$file)}
   $worldFiles=New-Object 'System.Collections.Generic.List[object]'
   $worldFiles.Add([pscustomobject]@{src=$file;rel=('Maps\'+$world+'.umap');kind='umap'})
   foreach($group in @('__ExternalActors__','__ExternalObjects__')){
     $dir=Join-Path $srcContent ($group+'\Maps\'+$world)
     if(!(Test-Path -LiteralPath $dir)){continue}
     if(IsReparse $dir){throw ('Map World Partition source dir is linked '+$dir)}
     foreach($sourceFile in @(Get-ChildItem -LiteralPath $dir -File -Recurse -Force -ErrorAction Stop)){
       if(IsReparse $sourceFile.FullName){throw ('Linked World Partition actor '+$sourceFile.FullName)}
       $relative=$sourceFile.FullName.Substring($srcContent.Length).TrimStart([char]'\')
       $worldFiles.Add([pscustomobject]@{src=$sourceFile.FullName;rel=$relative;kind=$group})
     }
   }
   foreach($pair in $worldFiles){
     $dst=Join-Path $stageContent $pair.rel
     if(Test-Path -LiteralPath $dst){
       if((Get-Item -LiteralPath $dst).Length -ne (Get-Item -LiteralPath $pair.src).Length -or (Sha $dst) -ne (Sha $pair.src)){
         throw ('Destination has DIFFERENT existing asset; do not overwrite: '+$pair.rel)
       }
     }else{$neededBytes+=[long](Get-Item -LiteralPath $pair.src).Length}
   }
   $plan.Add([pscustomobject]@{name=$item.name;package=$world;source=$srcContent;files=$worldFiles})
 }
 if($c.AvailableFreeSpace -lt ($neededBytes+16GB)){
   throw ('Not enough space to import 9 genuine map actor packages and keep 16 GiB free: '+$neededBytes)
 }
 $report.state='IMPORTING_REAL_MAP_PACKAGES_TO_ORIGINAL_SEVEN_ISLAND_STAGE'
 Save
 foreach($planItem in $plan){
   $worldReceipt=[ordered]@{name=$planItem.name;unrealPackage=('/Game/Maps/'+$planItem.package);fileCount=0;actorFiles=0;bytes=0;verifiedHashCount=0;state='IN_PROGRESS'}
   $report.worlds+=$worldReceipt
   Save
   foreach($part in $planItem.files){
     $dest=Join-Path $stageContent $part.rel
     if(!(Test-Path -LiteralPath $dest -PathType Leaf)){
       $folder=Split-Path -Parent $dest
       if(!(Test-Path -LiteralPath $folder)){New-Item -ItemType Directory -Path $folder -Force|Out-Null}
       # Remember created files immediately in memory for safe rollback.
       $created.Add($dest)
       Copy-Item -LiteralPath $part.src -Destination $dest -ErrorAction Stop
       $report.createdBytes += [long](Get-Item -LiteralPath $dest).Length
       if($part.kind -eq 'umap'){$report.packageFilesStaged++}
       else{$report.externalActorFilesStaged++}
     }
     if((Sha $dest) -ne (Sha $part.src)){throw ('SHA256 mismatch, imported world not valid: '+$part.rel)}
     $worldReceipt.fileCount++
     $worldReceipt.verifiedHashCount++
     $worldReceipt.bytes+=[long](Get-Item -LiteralPath $part.src).Length
     if($part.kind -ne 'umap'){$worldReceipt.actorFiles++}
     $report.hashesVerified++
   }
   $worldReceipt.state='WORLD_UMAP_AND_ACTOR_PACKAGES_STAGED_HASH_VERIFIED_NOT_YET_RENDERED'
   Save
   Write-Host ('ANOMALIAZ_NATIVE_MAP_IMPORTED='+$planItem.name+' PACKAGE=/Game/Maps/'+$planItem.package+' FILES='+$worldReceipt.fileCount+' ACTORS='+$worldReceipt.actorFiles)
 }
 $finalFiles=@(Get-ChildItem -LiteralPath (Join-Path $stageContent 'Maps') -File -Filter '*.umap')
 $existingCount=@($plan|Where-Object {Test-Path -LiteralPath (Join-Path $stageContent ('Maps\'+$_.package+'.umap'))}).Count
 if($existingCount -ne 9){throw 'Not all nine genuine map files present after import'}
 $report.state='FOURTEEN_GENUINE_UMAP_PACKAGES_STAGED_IN_SINGLE_REAL_UE5_PROJECT_FALC_MISSING'
 $report.exactUnrealLoadingStillRequiresTest=$true
}catch{
 $report.state='FAILED_MAP_IMPORT_SAFELY_REVERTING_ONLY_NEW_FILES'
 $report.error=$_.Exception.Message
 # Roll back only files created in this attempt, never touch earlier maps or originals.
 for($i=$created.Count-1; $i -ge 0; $i--){
   $newFile=$created[$i]
   if(Test-Path -LiteralPath $newFile -PathType Leaf){
     try{Remove-Item -LiteralPath $newFile -Force -ErrorAction Stop}catch{}
   }
 }
}finally{
 $report.cFreeGiBAfter=[math]::Round(([IO.DriveInfo]::new('C')).AvailableFreeSpace/1GB,3)
 Save
 Write-Host ('ANOMALIAZ_REAL_14_WORLD_IMPORT_STATE='+$report.state)
 Write-Host ('ANOMALIAZ_REAL_WORLD_IMPORT_C_GIB_BEFORE='+$report.cFreeGiBBefore)
 Write-Host ('ANOMALIAZ_REAL_WORLD_IMPORT_C_GIB_AFTER='+$report.cFreeGiBAfter)
 Write-Host ('ANOMALIAZ_REAL_WORLD_IMPORT_HASHED_FILES='+$report.hashesVerified)
 Write-Host 'ANOMALIAZ_SKARVIK_AND_ORIGINAL_D_MAPS_NOT_MODIFIED=true'
 if($report.error){Write-Host ('ANOMALIAZ_REAL_WORLD_IMPORT_ERROR='+$report.error)}
}
if($report.state -ne 'FOURTEEN_GENUINE_UMAP_PACKAGES_STAGED_IN_SINGLE_REAL_UE5_PROJECT_FALC_MISSING'){exit 2}
