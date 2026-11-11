# Resume an already approved SHA-256 C old-project cleanup after partial Windows file deletion.
# Never touch native SKARVIK, original D master, archives, original C source path
# or any files whose preserved counterpart cannot be validated.
[CmdletBinding()]
param([string]$ReportPath=(Join-Path $env:RUNNER_TEMP 'anomaliaz-resume-c-dedup.json'))
$ErrorActionPreference='Stop'
$source='C:\ANOMALIA'
$pending='C:\ANOMALIA.dedup-41332976014'
$master='D:\ANOMALIA'
$root='D:\ANOMALIAZ'
$archive='D:\ANOMALIAZ\07_Archives_Anciennes_C_Differences\ANOMALIA'
$marker=Join-Path $root '.anomaliaz-one-workspace-marker'
$manifest=Join-Path $archive 'MANIFEST_FICHIERS_DIFFERENTS_C.json'
$report=[ordered]@{
  state='PREFLIGHT'
  pending=$pending
  expectedOldJunction=$source
  preservedMaster=$master
  preservedArchive=$archive
  CFreeGiBBefore=[math]::Round(([IO.DriveInfo]::new('C')).AvailableFreeSpace/1GB,3)
  CFreeGiBAfter=0
  DFreeGiBBefore=[math]::Round(([IO.DriveInfo]::new('D')).AvailableFreeSpace/1GB,3)
  remainingFilesVerifiedBeforeDeletion=0
  archivedDifferentFileCount=0
  archivedDifferentBytesVerified=0
  oldLegacyJunctionPreserved=$false
  DOriginalChanged=$false
  SKARVIKChanged=$false
  error=$null
}
function WriteReport {
 ($report|ConvertTo-Json -Depth 8)|Set-Content -LiteralPath $ReportPath -Encoding UTF8
}
function Hash([string]$p) {(Get-FileHash -LiteralPath $p -Algorithm SHA256 -ErrorAction Stop).Hash}
function IsLink([string]$p) {
 return (((Get-Item -LiteralPath $p -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)
}
try{
 if(!(Test-Path -LiteralPath $marker) -or (Get-Content -LiteralPath $marker -Raw).Trim() -ne 'ANOMALIAZ_SAFE_CONSOLIDATION_V1_20261101'){throw 'Wrong central project marker'}
 if(!(Test-Path -LiteralPath $source -PathType Container) -or !(IsLink $source)){throw 'C old ANOMALIA is not an existing compatibility junction'}
 $target=@((Get-Item -LiteralPath $source -Force).Target)[0]
 if($target -ine $master){throw ('Unexpected junction target '+$target)}
 $report.oldLegacyJunctionPreserved=$true
 if(!(Test-Path -LiteralPath (Join-Path $source 'unreal\AnomaliaPrimeval.uproject'))){throw 'Original project is not reachable through C legacy junction'}
 if(!(Test-Path -LiteralPath (Join-Path $master 'unreal\AnomaliaPrimeval.uproject'))){throw 'D primary original Unreal project missing'}
 if(!(Test-Path -LiteralPath $manifest)){throw 'Unique C archive manifest missing'}
 if(!(Test-Path -LiteralPath $pending -PathType Container)){throw 'Partial old C physical folder no longer present; refuse guessing'}
 if(IsLink $pending){throw 'Pending old physical root is a link'}
 if(@(Get-Process -Name UnrealEditor,UnrealEditor-Cmd,AnomaliaZPrigimalia,UnrealBuildTool,ShaderCompileWorker,MSBuild -ErrorAction SilentlyContinue).Count){
  throw 'Unreal or compiler process currently using assets: refuse deletion'
 }
 $stagemarker='C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal\.skarvik-ci-stage-marker'
 if(!(Test-Path -LiteralPath $stagemarker) -or (Get-Content -LiteralPath $stagemarker -Raw).Trim() -ne '41188816555'){throw 'SKARVIK stage missing; refuse'}
 $m=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json
 if($m.original -ine $source -or $m.nativeDMaster -ine $master -or $m.archive -ine $archive){
   throw 'The preserved archive manifest has unexpected source/master references'
 }
 if(@($m.differentFiles).Count -ne 165){throw ('Unexpected number of different C files in verified archive '+@($m.differentFiles).Count)}
 foreach($entry in @($m.differentFiles)){
   $rel=[string]$entry.relative
   if([IO.Path]::IsPathRooted($rel) -or $rel.Contains('..') -or $rel.Contains(':')){throw ('Dangerous archive-relative path '+$rel)}
   $file=Join-Path $archive $rel
   if(!(Test-Path -LiteralPath $file -PathType Leaf)){throw ('Archived different file missing '+$rel)}
   if((Get-Item -LiteralPath $file).Length -ne [long]$entry.bytes -or (Hash $file) -ne [string]$entry.sha256){
     throw ('Archived different file hash mismatch '+$rel)
   }
   $report.archivedDifferentFileCount++
   $report.archivedDifferentBytesVerified+=[long]$entry.bytes
 }
 $report.state='ARCHIVE_MANIFEST_VERIFIED_CHECKING_ALL_REMAINING_OLD_C_FILES'
 WriteReport
 $files=@(Get-ChildItem -LiteralPath $pending -File -Recurse -Force -ErrorAction Stop)
 foreach($file in $files){
   $rel=$file.FullName.Substring($pending.Length).TrimStart([char]'\')
   if($rel.Contains('..') -or [IO.Path]::IsPathRooted($rel)){throw 'Unexpected physical source relative name'}
   $candidate=Join-Path $master $rel
   $backed=Join-Path $archive $rel
   $preserved=$false
   foreach($other in @($candidate,$backed)){
     if((Test-Path -LiteralPath $other -PathType Leaf) -and
      (Get-Item -LiteralPath $other).Length -eq $file.Length -and
      (Hash $other) -eq (Hash $file.FullName)){
       $preserved=$true;break
     }
   }
   if(!$preserved){throw ('Remaining old C file has no identical preserved D backup: '+$rel)}
   $report.remainingFilesVerifiedBeforeDeletion++
 }
 $links=@(Get-ChildItem -LiteralPath $pending -Recurse -Force -ErrorAction Stop|
   Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }|Select-Object -First 2)
 if($links.Count){throw 'Pending old physical folder contains junctions or symlinks'}
 $report.state='ALL_REMAINING_OLD_C_FILES_MATCH_PRESERVED_D_RECORDS'
 WriteReport
 # Win32 long-path deletion, used only for the one verified temp snapshot.
 # rmdir /s /q handles long nested imported asset filenames that
 # Remove-Item -Recurse on Windows PowerShell 5.1 cannot process.
 $long='\\?\'+$pending
 & cmd.exe /d /c rmdir /s /q $long
 $exitCode=$LASTEXITCODE
 if(Test-Path -LiteralPath $pending -PathType Container){
   throw ('Win32 extended-path cleanup incomplete; exit code '+$exitCode)
 }
 if(!(Test-Path -LiteralPath $source -PathType Container) -or !(IsLink $source)){throw 'Legacy C junction changed after cleanup'}
 if(!(Test-Path -LiteralPath (Join-Path $source 'unreal\AnomaliaPrimeval.uproject'))){throw 'Legacy C project no longer resolves'}
 $report.state='VERIFIED_C_DUPLICATE_RESUME_CLEANED'
}catch{
 $report.state='SAFE_STOP_INSPECT_PENDING_DIRECTORY'
 $report.error=$_.Exception.Message
}finally{
 $report.CFreeGiBAfter=[math]::Round(([IO.DriveInfo]::new('C')).AvailableFreeSpace/1GB,3)
 $report.DFreeGiBAfter=[math]::Round(([IO.DriveInfo]::new('D')).AvailableFreeSpace/1GB,3)
 WriteReport
 Write-Host ('ANOMALIAZ_RESUME_DEDUP_STATUS='+$report.state)
 Write-Host ('ANOMALIAZ_RESUME_C_FREE_BEFORE='+$report.CFreeGiBBefore)
 Write-Host ('ANOMALIAZ_RESUME_C_FREE_AFTER='+$report.CFreeGiBAfter)
 Write-Host ('ANOMALIAZ_RESUME_ARCHIVED_C_UNIQUE_FILES='+$report.archivedDifferentFileCount)
 Write-Host ('ANOMALIAZ_RESUME_C_FILES_VERIFIED='+$report.remainingFilesVerifiedBeforeDeletion)
 Write-Host 'ANOMALIAZ_SOURCE_D_ORIGINAL_AND_SKARVIK_NOT_MODIFIED=true'
 if($report.error){Write-Host ('ANOMALIAZ_RESUME_DEDUP_BLOCKER='+$report.error)}
}
if($report.state -ne 'VERIFIED_C_DUPLICATE_RESUME_CLEANED'){exit 2}
