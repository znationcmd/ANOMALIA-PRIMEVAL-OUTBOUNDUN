# Finish one interrupted, already SHA-approved C:\ANOMALIA dedup.
# Original full 5040-file SHA comparison and unique-data backup was performed
# before the physical snapshot was renamed to C:\ANOMALIA.dedup-41332976014.
# A previous Remove-Item step failed because Windows PowerShell 5.1 cannot
# enumerate one very long imported texture name. Do not enumerate it again.
$ErrorActionPreference='Stop'
$old='C:\ANOMALIA'
$pending='C:\ANOMALIA.dedup-41332976014'
$main='D:\ANOMALIAZ\01_Projet_Principal'
$oldD='D:\ANOMALIA'
$archive='D:\ANOMALIAZ\07_Archives_Anciennes_C_Differences\ANOMALIA'
$marker='D:\ANOMALIAZ\.anomaliaz-one-workspace-marker'
$manifest=Join-Path $archive 'MANIFEST_FICHIERS_DIFFERENTS_C.json'
$out=Join-Path $env:RUNNER_TEMP 'anomaliaz-final-long-path-snapshot-cleanup.json'
$report=[ordered]@{
 state='PREFLIGHT'
 cFreeGiBBefore=[math]::Round(([IO.DriveInfo]::new('C')).AvailableFreeSpace/1GB,3)
 cFreeGiBAfter=0
 dFreeGiBBefore=[math]::Round(([IO.DriveInfo]::new('D')).AvailableFreeSpace/1GB,3)
 preservedOriginalMainAndSkarvik=$true
 archivedUniqueCFilesSHA256Valid=0
 originalOldCPathIsJunction=$false
 removedOnlyExactInterruptedPhysicalSnapshot=$false
 priorCleanupJobId='41332976014'
 error=$null
}
function Output {
 $report.cFreeGiBAfter=[math]::Round(([IO.DriveInfo]::new('C')).AvailableFreeSpace/1GB,3)
 ($report|ConvertTo-Json -Depth 7)|Set-Content -LiteralPath $out -Encoding UTF8
 Write-Host ('ANOMALIA_CLEANUP_RECOVERY_STATE='+$report.state)
 Write-Host ('ANOMALIA_CLEANUP_C_FREE_BEFORE_GIB='+$report.cFreeGiBBefore)
 Write-Host ('ANOMALIA_CLEANUP_C_FREE_AFTER_GIB='+$report.cFreeGiBAfter)
 Write-Host ('ANOMALIA_CLEANUP_D_FREE_GIB='+([math]::Round(([IO.DriveInfo]::new('D')).AvailableFreeSpace/1GB,3)))
 if($report.error){Write-Host ('ANOMALIA_CLEANUP_RECOVERY_ERROR='+$report.error)}
}
try{
 if(!(Test-Path -LiteralPath $marker -PathType Leaf) -or (Get-Content -LiteralPath $marker -Raw).Trim() -ne 'ANOMALIAZ_SAFE_CONSOLIDATION_V1_20261101'){
   throw 'Wrong or absent unified workspace'
 }
 if(!(Test-Path -LiteralPath $main -PathType Container) -or !(Test-Path -LiteralPath (Join-Path $main 'unreal\AnomaliaPrimeval.uproject'))){
   throw 'Physical original 196 GiB primary project is unavailable'
 }
 foreach($p in @($old,$oldD)){
   if(!(Test-Path -LiteralPath $p -PathType Container)){throw ('Old compatibility path not available '+$p)}
   $item=Get-Item -LiteralPath $p -Force
   if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0){throw ('Original legacy path no longer a junction: '+$p)}
 }
 $cItem=Get-Item -LiteralPath $old -Force
 $dItem=Get-Item -LiteralPath $oldD -Force
 if(@($cItem.Target)[0] -ine $oldD -and @($cItem.Target)[0] -ine $main){
   throw ('Unexpected C junction destination: '+@($cItem.Target)[0])
 }
 if(@($dItem.Target)[0] -ine $main){throw ('Unexpected D junction destination: '+@($dItem.Target)[0])}
 $report.originalOldCPathIsJunction=$true
 if(!(Test-Path -LiteralPath $pending -PathType Container)){throw 'Already partly removed physical snapshot is absent; no additional deletion permitted'}
 if((([IO.File]::GetAttributes($pending)) -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Target is a junction; refuse'}
 if(!(Test-Path -LiteralPath (Join-Path $old 'unreal\AnomaliaPrimeval.uproject'))){throw 'Old C compatibility project unavailable'}
 if(!(Test-Path -LiteralPath 'C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal\.skarvik-ci-stage-marker')){throw 'SKARVIK native stage not verified'}
 if((Get-Content -LiteralPath 'C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal\.skarvik-ci-stage-marker' -Raw).Trim() -ne '41188816555'){throw 'SKARVIK marker mismatch'}
 $processes=@(Get-Process -Name UnrealEditor,UnrealEditor-Cmd,AnomaliaZPrigimalia,AnomaliaPrimeval,UnrealBuildTool,ShaderCompileWorker,MSBuild -ErrorAction SilentlyContinue)
 if($processes.Count){throw 'Unreal currently running; old C dedup is unsafe'}
 if(!(Test-Path -LiteralPath $manifest -PathType Leaf)){throw 'Immutable unique-data backup manifest is missing'}
 $m=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json
 if($m.original -ine $old -or $m.nativeDMaster -ine $oldD -or $m.archive -ine $archive){throw 'Backup metadata not from the previous successful verified dedup'}
 $unique=@($m.differentFiles)
 if($unique.Count -ne 165){throw 'Incorrect expected unique C file count'}
 foreach($entry in $unique){
   $rel=[string]$entry.relative
   if([IO.Path]::IsPathRooted($rel) -or $rel.Contains('..') -or $rel.Contains(':')){throw ('Untrusted archive relative path '+$rel)}
   $file=Join-Path $archive $rel
   if(!(Test-Path -LiteralPath $file -PathType Leaf)){throw ('Unique C backup missing '+$rel)}
   if((Get-Item -LiteralPath $file).Length -ne [long]$entry.bytes -or
      (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne [string]$entry.sha256){
       throw ('Unique C backup corrupted '+$rel)
   }
   $report.archivedUniqueCFilesSHA256Valid++
 }
 $report.state='ALL_165_UNIQUE_C_FILES_VERIFIED_SAFE_TO_FINISH_PREVIOUS_PARTIAL_DEDUP'
 Output
 # Mirror a freshly created empty local directory onto the *one known* old
 # physical snapshot. Robocopy handles long paths in FBX/imported textures.
 # Source and target are checked exact paths; there is no /MIR of any master.
 $empty='C:\ANOMALIAZ_DEDUP_EMPTY_'+$env:GITHUB_RUN_ID
 if(Test-Path -LiteralPath $empty){throw 'Temporary empty source already exists'}
 New-Item -ItemType Directory -Path $empty -ErrorAction Stop|Out-Null
 try{
   $code=$null
   & robocopy.exe $empty $pending /MIR /R:0 /W:0 /XJ /NP /NJH /NJS /NFL /NDL
   $code=$LASTEXITCODE
   if($code -ge 8){throw ('Robocopy long-path cleanup failed code='+$code)}
   $long='\\?\'+$pending
   & cmd.exe /d /c rmdir /s /q $long
   if(Test-Path -LiteralPath $pending -PathType Container){
     throw ('Still cannot remove the old temporary snapshot with extended Win32 path')
   }
 }finally{
   if(Test-Path -LiteralPath $empty){
     Remove-Item -LiteralPath $empty -Force -ErrorAction Stop
   }
 }
 if(!(Test-Path -LiteralPath (Join-Path $old 'unreal\AnomaliaPrimeval.uproject'))){throw 'Old C compatible project unavailable after cleanup'}
 if(!(Test-Path -LiteralPath (Join-Path $main 'unreal\AnomaliaPrimeval.uproject'))){throw 'Main 196 GiB project not available after cleanup'}
 $report.removedOnlyExactInterruptedPhysicalSnapshot=$true
 $report.state='OLD_C_DUPLICATE_SNAPSHOT_FINALLY_REMOVED_ARCHIVE_AND_MAPS_PRESERVED'
}catch{
 $report.state='STOPPED_SAFELY_INCOMPLETE_CHECK_REPORT'
 $report.error=$_.Exception.Message
}finally{Output}
if($report.state -ne 'OLD_C_DUPLICATE_SNAPSHOT_FINALLY_REMOVED_ARCHIVE_AND_MAPS_PRESERVED'){exit 2}
