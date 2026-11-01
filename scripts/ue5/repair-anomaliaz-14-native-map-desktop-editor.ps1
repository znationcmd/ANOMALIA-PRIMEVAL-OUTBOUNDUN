# Repair only verified ANOMALIA UE5 desktop shortcuts after the 14 real
# native worlds have been staged. Old shortcuts are ARCHIVED, not destroyed.
[CmdletBinding()]
param([string]$ReportPath=(Join-Path $env:RUNNER_TEMP 'anomaliaz-correct-desktop-editor.json'))
$ErrorActionPreference='Stop'
$root='C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal'
$project=Join-Path $root 'AnomaliaZPrigimalia.uproject'
$central='D:\ANOMALIAZ'
$desk=[Environment]::GetFolderPath('Desktop')
$iconSource=Join-Path $env:GITHUB_WORKSPACE 'build\icon.ico'
$iconFolder=Join-Path $central 'AnomaliaZ_Brand'
$iconFile=Join-Path $iconFolder 'ANOMALIAZ.ico'
$archived=Join-Path $central ('04_Sauvegardes\Anciens_raccourcis_Bureau\run-'+$env:GITHUB_RUN_ID)
$legacyNames=@(
  'ANOMALIA - Carte D.lnk',
  'ANOMALIA - Jouer carte D.lnk',
  'ANOMALIAZ - JOUER SKARVIK TEST MODE LEGER.lnk',
  'ANOMALIAZ - SKARVIK FINAL (Unreal 5.8).lnk'
)
$newName='ANOMALIAZ - EDITER LES CARTES (UE5.8).lnk'
$newPath=Join-Path $desk $newName
$report=[ordered]@{
 state='PRECHECK'
 project=$project
 fixedLauncher=$newPath
 original15MapIntention=15
 actuallyImportedNativeMapCount=14
 originalFALCHeightmapMissing=$true
 oldGameExeNotConfusedWithUEEditor=$true
 oldLinkFilesArchived=@()
 independentOriginalProjectsUnmodified=$true
 nativeGameInstallerNotBuilt=$true
 executableLaunchNotPlaytested=$true
 iconCopied=$false
 error=$null
}
try{
 $owner=Join-Path $root '.skarvik-ci-stage-marker'
 if(!(Test-Path $owner) -or (Get-Content $owner -Raw).Trim() -ne '41188816555'){throw 'SKARVIK native project marker absent'}
 if(!(Test-Path -LiteralPath $project)){throw 'Native SKARVIK project absent'}
 if(!(Test-Path -LiteralPath $desk -PathType Container)){throw 'User desktop is unavailable'}
 if(!(Test-Path -LiteralPath (Join-Path $central '.anomaliaz-one-workspace-marker'))){throw 'One central D project not mounted'}
 $required=@(
 'PRIGIMALIA_SKARVIK_FINAL_v1','ANOMALIA_Inhabited_v2',
 'PRIGIMALIA_KARSKOV','PRIGIMALIA_VORGRAD',
 'PRIGIMALIA_NEMORIS','PRIGIMALIA_DRAKHEIM',
 'PRIGIMALIA_SOLYNACALYRA','PRIGIMALIA_NEXAVARKHOS',
 'PRIGIMALIA_CHERNASKALUXRIA','PRIGIMALIA_KOLCHIEM_ORIGINS',
 'PRIGIMALIA_ROSKATVIA_B1','PRIGIMALIA_NOGOKV_51',
 'PRIGIMALIA_PARADISIOMANIA','PRIGIMALIA_DEADROOT'
 )
 foreach($name in $required){
   if(!(Test-Path -LiteralPath (Join-Path $root ('Content\Maps\'+$name+'.umap')))){
     throw ('Native 14-map import incomplete: '+$name)
   }
 }
 $ed=$null
 foreach($base in @($env:UE_ROOT,'C:\Program Files\Epic Games\UE_5.8','C:\Program Files\Epic Games\UE_5.8.3')){
   if(!$base){continue}
   $candidate=Join-Path $base 'Engine\Binaries\Win64\UnrealEditor.exe'
   if(Test-Path -LiteralPath $candidate){$ed=$candidate;break}
 }
 if(!$ed){throw 'Real UE5.8 UnrealEditor.exe not found'}
 $shell=New-Object -ComObject WScript.Shell
 $legacy=@()
 foreach($name in $legacyNames){
   $old=Join-Path $desk $name
   if(!(Test-Path -LiteralPath $old)){continue}
   $shortcut=$shell.CreateShortcut($old)
   if($shortcut.TargetPath -notmatch '(?i)UnrealEditor\.exe$'){
     throw ('Legacy link is not the known UE5 Editor type: '+$name)
   }
   if($name -match 'Carte D' -and $shortcut.Arguments -notmatch 'ANOMALIA_Inhabited_v2'){throw ('Unknown desktop shortcut, refuse archive '+$name)}
   if($name -match 'SKARVIK' -and $shortcut.Arguments -notmatch 'PRIGIMALIA_SKARVIK_FINAL_v1'){throw ('Unexpected SKARVIK link '+$name)}
   $legacy+=@{source=$old;name=$name}
 }
 if(Test-Path -LiteralPath $newPath){
   $existing=$shell.CreateShortcut($newPath)
   if($existing.TargetPath -ne $ed -or $existing.Arguments -notmatch [regex]::Escape($project)){
     throw 'Unexpected existing main editor shortcut; refuse overwrite'
   }
 }
 # Optional stable copy of existing approved icon (not a generated logo).
 if(Test-Path -LiteralPath $iconSource -PathType Leaf){
   $bytes=[IO.File]::ReadAllBytes($iconSource)
   if($bytes.Length -gt 2000 -and $bytes.Length -lt 5000000 -and
      $bytes[0] -eq 0 -and $bytes[1] -eq 0 -and $bytes[2] -eq 1 -and $bytes[3] -eq 0){
     if(!(Test-Path $iconFolder)){New-Item -ItemType Directory -Force -Path $iconFolder|Out-Null}
     if(!(Test-Path $iconFile)){Copy-Item -LiteralPath $iconSource -Destination $iconFile -ErrorAction Stop}
     if((Get-FileHash -LiteralPath $iconSource -Algorithm SHA256).Hash -eq (Get-FileHash -LiteralPath $iconFile -Algorithm SHA256).Hash){
       $report.iconCopied=$true
     }
   }
 }
 $link=$shell.CreateShortcut($newPath)
 $link.TargetPath=$ed
 $link.Arguments=('"'+$project+'" /Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1 -d3d11 -sm5 -log')
 $link.WorkingDirectory=$root
 $link.Description='Editeur UE5.8 du vrai projet ANOMALIAZ : 14 cartes natives chargeables dans Content/Maps. FALC originale a importer.'
 if($report.iconCopied){$link.IconLocation=$iconFile+',0'}
 else{$link.IconLocation=$ed+',0'}
 $link.Save()
 $check=$shell.CreateShortcut($newPath)
 if($check.TargetPath -ne $ed -or $check.Arguments -notmatch 'PRIGIMALIA_SKARVIK_FINAL_v1' -or $check.Arguments -match '(?i) -game\b' -or $check.Arguments -notmatch 'AnomaliaZPrigimalia\.uproject'){
   throw 'New correct editor link verification failed'
 }
 # No deletion: archive only 4 specifically verified obsolete shortcuts.
 if($legacy.Count){
   if(Test-Path -LiteralPath $archived){throw 'An existing desktop shortcut archive has same run id'}
   New-Item -ItemType Directory -Path $archived -Force|Out-Null
   foreach($item in $legacy){
     $dst=Join-Path $archived $item.name
     Move-Item -LiteralPath $item.source -Destination $dst -ErrorAction Stop
     if(!(Test-Path -LiteralPath $dst -PathType Leaf)){throw 'Old desktop shortcut not safely archived'}
     $report.oldLinkFilesArchived+=@{oldName=$item.name;archive=$dst}
   }
 }
 $report.state='ONE_CORRECT_UE5_EDITOR_WITH_14_REAL_MAPS_OLD_LINKS_ARCHIVED_NO_FAKE_PUBLIC_BETA'
}catch{
 $report.state='FAILED_OR_PARTIAL_SAFE_DESKTOP_REPAIR'
 $report.error=$_.Exception.Message
}finally{
 $folder=Split-Path -Parent $ReportPath
 if(!(Test-Path -LiteralPath $folder)){New-Item -ItemType Directory -Path $folder -Force|Out-Null}
 ($report|ConvertTo-Json -Depth 9)|Set-Content -LiteralPath $ReportPath -Encoding UTF8
 Write-Host ('ANOMALIAZ_UE5_DESKTOP_RESULT='+$report.state)
 Write-Host ('ANOMALIAZ_UE5_OLD_LINKS_ARCHIVED='+$report.oldLinkFilesArchived.Count)
 Write-Host ('ANOMALIAZ_UE5_EDITOR_SHORTCUT='+$newName)
 Write-Host 'ANOMALIAZ_UE5_REAL_NATIVE_MAP_FILES_PRESENT=14'
 Write-Host 'ANOMALIAZ_UE5_FALC_NATIVE_WORLD_MISSING=true'
 Write-Host 'ANOMALIAZ_UE5_REAL_PUBLIC_BETA_NOT_YET_BUILT=true'
 if($report.error){Write-Host ('ANOMALIAZ_UE5_DESKTOP_ERROR='+$report.error)}
}
if($report.state -ne 'ONE_CORRECT_UE5_EDITOR_WITH_14_REAL_MAPS_OLD_LINKS_ARCHIVED_NO_FAKE_PUBLIC_BETA'){exit 2}
exit 0
