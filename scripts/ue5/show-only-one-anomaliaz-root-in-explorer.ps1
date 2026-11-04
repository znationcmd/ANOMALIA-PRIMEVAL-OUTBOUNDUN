# Show one primary ANOMALIAZ folder in File Explorer without moving, deleting
# or duplicating any Unreal assets. Only hide proven legacy NTFS junctions
# and validated, active C staging folders. All old absolute paths keep working.
[CmdletBinding()]
param([string]$ReportPath=(Join-Path $env:RUNNER_TEMP 'anomaliaz-one-visible-root.json'))
$ErrorActionPreference='Stop'
$central='D:\ANOMALIAZ'
$requiredMarker='ANOMALIAZ_SAFE_CONSOLIDATION_V1_20261101'
$marker=Join-Path $central '.anomaliaz-one-workspace-marker'
$legacy=@(
 @{path='C:\ANOMALIA';expected='D:\ANOMALIA';probe='unreal\AnomaliaPrimeval.uproject'},
 @{path='C:\ANOMALIA-Validation';expected='D:\ANOMALIAZ\03_Validation';probe='c40543166274\unreal\AnomaliaPrimeval.uproject'},
 @{path='D:\ANOMALIA';expected='D:\ANOMALIAZ\01_Projet_Principal';probe='unreal\AnomaliaPrimeval.uproject'},
 @{path='D:\ANOMALIA-Backups';expected='D:\ANOMALIAZ\04_Sauvegardes';probe='pre-differential-40767016246\EditorActive\active-version\AnomaliaPrimeval.uproject'},
 @{path='D:\ANOMALIA-Validation';expected='D:\ANOMALIAZ\03_Validation';probe='c40543166274\unreal\AnomaliaPrimeval.uproject'},
 @{path='D:\ANOMALIAZ-PRIGIMALIA';expected='D:\ANOMALIAZ\02_Projet_Migration';probe='unreal\AnomaliaZPrigimalia.uproject'}
)
$stages=@(
 @{path='C:\ANOMALIAZ_SKARVIK_STAGE_41188816555';probe='unreal\.skarvik-ci-stage-marker'},
 @{path='C:\ANOMALIAZ_SKARVIK_NATIVE_ALPHA_CANDIDATE';probe='.alpha-source-owner-marker'}
)
$report=[ordered]@{
 state='STARTED'
 projectCentralVisible=$false
 changedOnlyExplorerVisibility=$true
 filesMoved=$false
 filesDeleted=$false
 bytesFreed=0
 legacyJunctionsHidden=@()
 actualCActiveFoldersHidden=@()
 skips=@()
 error=$null
}
function WriteResult {
 ($report|ConvertTo-Json -Depth 8)|Set-Content -LiteralPath $ReportPath -Encoding utf8
}
function AssertMarker {
 if(!(Test-Path -LiteralPath $marker -PathType Leaf)){throw 'Central workspace marker absent'}
 if((Get-Content -LiteralPath $marker -Raw).Trim() -ne $requiredMarker){throw 'Wrong central workspace marker'}
 if(!(Test-Path -LiteralPath (Join-Path $central '01_Projet_Principal\unreal\AnomaliaPrimeval.uproject'))){throw 'Central original project not reachable'}
 if(!(Test-Path -LiteralPath (Join-Path $central '02_Projet_Migration\unreal\AnomaliaZPrigimalia.uproject'))){throw 'Central migrated UE project not reachable'}
}
function HidePath([string]$p,[bool]$link) {
 # /L affects the NTFS link itself, not its target. Do not recurse.
 $args=@('+h')
 if($link){$args+= '/L'}
 $args+= $p
 & "$env:SystemRoot\System32\attrib.exe" @args
 if($LASTEXITCODE -ne 0){throw ('attrib.exe could not hide '+$p)}
 # On a Windows junction, GetItem may represent target attributes differently:
 # check the link is still a reparse point AND target remained accessible.
 if(!(Test-Path -LiteralPath $p -PathType Container)){throw ('Path broken by hide '+$p)}
}
try{
 AssertMarker
 $centralItem=Get-Item -LiteralPath $central -Force
 if(($centralItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Central folder is unexpectedly a link'}
 # The one requested central folder must remain visible in Explorer.
 & "$env:SystemRoot\System32\attrib.exe" '-h' '-s' $central
 if($LASTEXITCODE -ne 0){throw 'Unable to make central folder visible'}
 foreach($entry in $legacy){
   $p=$entry.path
   if(!(Test-Path -LiteralPath $p -PathType Container)){throw ('Expected old junction missing '+$p)}
   $obj=Get-Item -LiteralPath $p -Force
   if(($obj.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0){throw ('Refuse to hide real legacy folder: '+$p)}
   $actual=@($obj.Target)[0]
   $expected=$entry.expected
   if(([string]$actual).TrimEnd('\') -ine $expected.TrimEnd('\')){
     throw ('Unexpected junction target: '+$p+' -> '+$actual)
   }
   if(!(Test-Path -LiteralPath (Join-Path $p $entry.probe) -PathType Leaf)){
     throw ('Original project is not reachable through old junction '+$p)
   }
 }
 # All six verified first; then change only Explorer hidden flags.
 foreach($entry in $legacy){
   HidePath $entry.path $true
   $now=Get-Item -LiteralPath $entry.path -Force
   if(($now.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0){throw ('Junction type changed '+$entry.path)}
   if(!(Test-Path -LiteralPath (Join-Path $entry.path $entry.probe) -PathType Leaf)){
     throw ('Link no longer resolves after hiding '+$entry.path)
   }
   $report.legacyJunctionsHidden+= $entry.path
 }
 foreach($entry in $stages){
   $p=$entry.path
   if(!(Test-Path -LiteralPath $p -PathType Container)){$report.skips+=('Missing physical working folder '+$p);continue}
   $obj=Get-Item -LiteralPath $p -Force
   if(($obj.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){$report.skips+=('Physical work folder unexpectedly junction '+$p);continue}
   if(!(Test-Path -LiteralPath (Join-Path $p $entry.probe) -PathType Leaf)){
     $report.skips+=('No verified project owner marker '+$p);continue
   }
   if($p -like '*SKARVIK_STAGE*'){
     if((Get-Content (Join-Path $p $entry.probe) -Raw).Trim() -ne '41188816555'){throw 'SKARVIK stage marker mismatch'}
   }
   HidePath $p $false
   $report.actualCActiveFoldersHidden+= $p
 }
 AssertMarker
 $report.projectCentralVisible=$true
 $report.state='ONE_VISIBLE_ANOMALIAZ_ROOT_AND_ALL_OLD_PROJECT_PATHS_PRESERVED'
}catch{
 $report.state='PARTIAL_HIDE_OR_BLOCKED_NO_USER_FILES_DELETED'
 $report.error=$_.Exception.Message
}finally{
 WriteResult
 Write-Host ('ANOMALIAZ_ONE_VISIBLE_ROOT_STATE='+$report.state)
 Write-Host ('ANOMALIAZ_HIDDEN_LEGACY_JUNCTIONS='+$report.legacyJunctionsHidden.Count)
 Write-Host ('ANOMALIAZ_HIDDEN_WORKING_FOLDERS='+$report.actualCActiveFoldersHidden.Count)
 Write-Host 'ANOMALIAZ_BYTES_REMOVED_BY_HIDING=0'
 Write-Host 'ANOMALIAZ_UNREAL_DATA_AND_OLD_PATHS_PRESERVED=true'
 if($report.error){Write-Host ('ANOMALIAZ_ONE_VISIBLE_ROOT_ERROR='+$report.error)}
}
if($report.state -ne 'ONE_VISIBLE_ANOMALIAZ_ROOT_AND_ALL_OLD_PROJECT_PATHS_PRESERVED'){exit 2}
