# Deduplicate only independently SHA256-verified C copies into D:\ANOMALIAZ.
# All differing C files are backed up, hashed and documented BEFORE deletion.
# Each original C path is preserved by a Windows NTFS junction.
# We never alter D originals, C native SKARVIK, FabImports or sketchfab.
[CmdletBinding()]
param(
 [string]$ReportPath=(Join-Path $env:RUNNER_TEMP 'anomaliaz-c-dedup-verified.json')
)
$ErrorActionPreference='Stop'
$central='D:\ANOMALIAZ'
$marker=Join-Path $central '.anomaliaz-one-workspace-marker'
$expected='ANOMALIAZ_SAFE_CONSOLIDATION_V1_20261101'
$archive=Join-Path $central '07_Archives_Anciennes_C_Differences'
$tasks=@(
 @{name='ANOMALIA-Validation';source='C:\ANOMALIA-Validation';master='D:\ANOMALIAZ\03_Validation'},
 @{name='ANOMALIA';source='C:\ANOMALIA';master='D:\ANOMALIA'}
)
function IsLink([string]$p) {
 return (([IO.File]::GetAttributes($p) -band [IO.FileAttributes]::ReparsePoint) -ne 0)
}
function Sha([string]$p) {(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Resolved([string]$p) {[IO.Path]::GetFullPath($p).TrimEnd('\')}
function Trace([string]$m) {Write-Host ('ANOMALIAZ_VERIFIED_CLEANUP '+$m)}
function SaveReport {
 $folder=Split-Path -Parent $ReportPath
 if(!(Test-Path $folder)){New-Item -ItemType Directory -Force -Path $folder|Out-Null}
 ($report | ConvertTo-Json -Depth 10) | Set-Content -LiteralPath $ReportPath -Encoding UTF8
}
$report=[ordered]@{
 state='IN_PROGRESS'
 startedUTC=[DateTime]::UtcNow.ToString('o')
 central=$central
 sourceDiskFreeGiBBefore=[math]::Round(([IO.DriveInfo]::new('C')).AvailableFreeSpace/1GB,3)
 sourceDiskFreeGiBAfter=$null
 archiveDiskFreeGiBBefore=[math]::Round(([IO.DriveInfo]::new('D')).AvailableFreeSpace/1GB,3)
 archiveDiskFreeGiBAfter=$null
 DOriginalFilesAltered=$false
 CNativeSkarvikStageAltered=$false
 gameAssetsRemoved=$false
 differingOldCFilesKeptInArchive=$true
 tasks=@()
 error=$null
}
try {
 if(!(Test-Path -LiteralPath $central -PathType Container) -or
   !(Test-Path -LiteralPath $marker -PathType Leaf) -or
   (Get-Content -LiteralPath $marker -Raw).Trim() -ne $expected){
   throw 'Central D workspace not yet prepared or wrong identifier; refuse cleanup'
 }
 if(!(Test-Path -LiteralPath 'D:\ANOMALIA\unreal\AnomaliaPrimeval.uproject')){
   throw 'The original primary UE project on D is missing'
 }
 if(!(Test-Path -LiteralPath 'C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal\.skarvik-ci-stage-marker')){
   throw 'Real C SKARVIK stage is absent'
 }
 if((Get-Content 'C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal\.skarvik-ci-stage-marker' -Raw).Trim() -ne '41188816555'){
   throw 'Real C SKARVIK stage marker incorrect'
 }
 if(@(Get-Process -Name UnrealEditor,UnrealEditor-Cmd,AnomaliaZPrigimalia,AnomaliaPrimeval,UnrealBuildTool,ShaderCompileWorker,MSBuild -ErrorAction SilentlyContinue).Count){
   throw 'UE5 editor or compiler active: no deletion of older C directories'
 }
 foreach($job in $tasks){
  $src=Resolved $job.source
  $master=Resolved $job.master
  $label=$job.name
  $backup=Join-Path $archive $label
  $result=[ordered]@{
   name=$label; source=$src; master=$master; archive=$backup
   state='PREFLIGHT'
   identicalFiles=0; identicalGiB=0
   preservedDifferentFiles=0; preservedDifferentGiB=0
   sourceFiles=0; sourceGiB=0
   compatibilityJunctionCreated=$false
   oldFilesRemoved=$false
   verifiedArchiveSHA256=$false
   error=$null
  }
  $report.tasks+= $result
  SaveReport
  if(!(Test-Path -LiteralPath $master -PathType Container)){throw ('Missing preserved D counterpart '+$master)}
  if(IsLink $master){throw ('Counterpart is a link, not independent D master '+$master)}
  if(!(Test-Path -LiteralPath $src -PathType Container)){throw ('Old C source missing '+$src)}
  if(IsLink $src){
   # Idempotency: an existing compatibility junction is fine ONLY if it targets expected D.
   $item=Get-Item -LiteralPath $src -Force
   $target=($item.Target -join ';')
   if(($target -ne $master) -and ($target -ne $job.master)){
     throw ('Unexpected existing C link '+$src+' -> '+$target)
   }
   $result.state='ALREADY_CLEAN_WITH_VERIFIED_JUNCTION'
   $result.compatibilityJunctionCreated=$true
   $result.oldFilesRemoved=$true
   SaveReport
   continue
  }
  # Refuse junction traversal, hard-to-see directory links, or a pending old cleanup.
  $reparse=@(Get-ChildItem -LiteralPath $src -Recurse -Force -ErrorAction Stop |
    Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 } |
    Select-Object -First 3)
  if($reparse.Count){throw ('Nested symlink/reparse found in '+$src+' : '+($reparse.FullName -join ', '))}
  $stale=$src+'.dedup-'+$env:GITHUB_RUN_ID
  if(Test-Path -LiteralPath $stale){throw ('Temporary relocation already exists '+$stale)}
  $files=@(Get-ChildItem -LiteralPath $src -Recurse -Force -File -ErrorAction Stop)
  if($files.Count -lt 100){throw ('Unexpectedly few old source files '+$src)}
  $diff=@()
  [long]$identicalBytes=0;[long]$diffBytes=0;[long]$totalBytes=0
  foreach($file in $files){
   $relative=$file.FullName.Substring($src.Length).TrimStart([char]'\')
   $target=Join-Path $master $relative
   $totalBytes+=[long]$file.Length
   $same=$false
   if((Test-Path -LiteralPath $target -PathType Leaf) -and
     (Get-Item -LiteralPath $target).Length -eq $file.Length){
     $same=((Sha $file.FullName) -eq (Sha $target))
   }
   if($same){$identicalBytes+=[long]$file.Length;$result.identicalFiles++}
   else{
     $diffBytes+=[long]$file.Length
     $diff+=([pscustomobject]@{relative=$relative;source=$file.FullName;target=(Join-Path $backup $relative);bytes=[long]$file.Length})
   }
  }
  $result.sourceFiles=$files.Count
  $result.sourceGiB=[math]::Round($totalBytes/1GB,3)
  $result.identicalGiB=[math]::Round($identicalBytes/1GB,3)
  $result.preservedDifferentFiles=$diff.Count
  $result.preservedDifferentGiB=[math]::Round($diffBytes/1GB,3)
  if($identicalBytes -lt 5GB){throw ('Too few identical bytes to justify destructive dedup: '+$label)}
  $freeD=[long]([IO.DriveInfo]::new('D')).AvailableFreeSpace
  if($freeD -lt ($diffBytes+3GB)){
    throw ('Insufficient D space to safely retain every unique C file with 3GB spare: '+$label)
  }
  $result.state='VERIFIED_DUPLICATES_BACKING_UP_DIFFERENCES'
  SaveReport
  # Archive is append-only for this operation. Existing conflicting names BLOCK deletion.
  if(!(Test-Path -LiteralPath $backup)){New-Item -ItemType Directory -Path $backup -Force|Out-Null}
  $manifest=New-Object 'System.Collections.Generic.List[object]'
  foreach($file in $diff){
    $parent=Split-Path -Parent $file.target
    if(!(Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Force -Path $parent|Out-Null}
    if(Test-Path -LiteralPath $file.target){
      if((Sha $file.source) -ne (Sha $file.target)){throw ('Archive has conflicting file '+$file.relative)}
    }else{Copy-Item -LiteralPath $file.source -Destination $file.target -ErrorAction Stop}
    $hash=Sha $file.source
    if((Sha $file.target) -ne $hash){throw ('Failed exact preservation of '+$file.relative)}
    $manifest.Add([ordered]@{relative=$file.relative;bytes=$file.bytes;sha256=$hash;masterDiffersOrMissing=$true})
  }
  $manifestFile=Join-Path $backup 'MANIFEST_FICHIERS_DIFFERENTS_C.json'
  if(Test-Path $manifestFile){throw ('Previous manifest already exists, do not overwrite '+$manifestFile)}
  ([ordered]@{
    original=$src;nativeDMaster=$master;archive=$backup
    purpose='Original C unique and different files needed to reconstruct original C snapshot'
    identicalDataCanBeRecoveredFromMaster=$true
    differentFiles=$manifest
  }|ConvertTo-Json -Depth 8)|Set-Content -LiteralPath $manifestFile -Encoding UTF8
  $result.verifiedArchiveSHA256=$true
  $result.state='ARCHIVED_ALL_DIFFERENCES_AND_READY_TO_SWITCH'
  SaveReport
  # Rename on same volume is metadata-only. Create verified junction at old C path.
  Rename-Item -LiteralPath $src -NewName ([IO.Path]::GetFileName($stale)) -ErrorAction Stop
  try{
    New-Item -ItemType Junction -Path $src -Target $master -ErrorAction Stop|Out-Null
    if(!(Test-Path -LiteralPath $src -PathType Container) -or !(IsLink $src)){
      throw ('Compatibility junction not created '+$src)
    }
    if(!(Test-Path -LiteralPath (Join-Path $src 'c40543166274\unreal\AnomaliaPrimeval.uproject')) -and
        $label -eq 'ANOMALIA-Validation'){
      throw 'Preserved validation project unavailable through C junction'
    }
    if(!(Test-Path -LiteralPath (Join-Path $src 'unreal\AnomaliaPrimeval.uproject')) -and
        $label -eq 'ANOMALIA'){
      throw 'Original main UE project unavailable through C junction'
    }
    $result.compatibilityJunctionCreated=$true
  }catch{
    if(Test-Path -LiteralPath $src){
      $item=Get-Item -LiteralPath $src -Force
      if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){
        & cmd.exe /c ('rmdir "'+$src+'"')|Out-Null
      }
    }
    if(!(Test-Path -LiteralPath $src) -and (Test-Path -LiteralPath $stale)){
      Rename-Item -LiteralPath $stale -NewName ([IO.Path]::GetFileName($src)) -ErrorAction Stop
    }
    throw
  }
  # Old bytes are now SHA-identical to D or verified in the append-only archive.
  # Deletion excludes reparse points by the preflight above.
  $result.state='JUNCTION_VERIFIED_REMOVING_OLD_C_DUPLICATE_SNAPSHOT'
  SaveReport
  Remove-Item -LiteralPath $stale -Recurse -Force -ErrorAction Stop
  $result.oldFilesRemoved=$true
  $result.state='C_DUPLICATES_REMOVED_ALL_UNIQUE_C_FILES_ARCHIVED'
  SaveReport
  Trace ('C_CLEANED name='+$label+' identicalGiB='+$result.identicalGiB+
     ' archivedGiB='+$result.preservedDifferentGiB+' sourceGiB='+$result.sourceGiB)
 }
 $report.state='VERIFIED_OLD_C_PROJECT_DUPLICATES_REMOVED_AND_JUNCTIONS_CREATED'
}catch{
 $report.state='STOPPED_SAFELY_INSPECT_REPORT_BEFORE_RETRY'
 $report.error=$_.Exception.Message
 Trace ('BLOCKED='+$report.error)
}finally{
 $report.sourceDiskFreeGiBAfter=[math]::Round(([IO.DriveInfo]::new('C')).AvailableFreeSpace/1GB,3)
 $report.archiveDiskFreeGiBAfter=[math]::Round(([IO.DriveInfo]::new('D')).AvailableFreeSpace/1GB,3)
 SaveReport
 Trace ('RESULT='+$report.state)
 Trace ('C_FREE_GIB_BEFORE='+$report.sourceDiskFreeGiBBefore)
 Trace ('C_FREE_GIB_AFTER='+$report.sourceDiskFreeGiBAfter)
 Trace ('D_FREE_GIB_BEFORE='+$report.archiveDiskFreeGiBBefore)
 Trace ('D_FREE_GIB_AFTER='+$report.archiveDiskFreeGiBAfter)
 Trace 'ORIGINAL_D_PROJECT_UNMODIFIED=true'
}
if($report.state -ne 'VERIFIED_OLD_C_PROJECT_DUPLICATES_REMOVED_AND_JUNCTIONS_CREATED'){exit 2}
