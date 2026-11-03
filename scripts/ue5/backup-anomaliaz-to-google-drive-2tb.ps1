param(
  [long]$MaxUploadBytes = 1073741824,
  [int]$MaxUploadFiles = 70,
  [switch]$Continuous
)
$ErrorActionPreference='Stop'
# Google Drive for desktop can mount as G: or H:. Require the explicit authorization marker.
$cloudCandidates=@('H:\Mon Drive\ANOMALIAZ','G:\Mon Drive\ANOMALIAZ','G:\My Drive\ANOMALIAZ','H:\My Drive\ANOMALIAZ')
$cloud=$null
foreach($candidate in $cloudCandidates){
  $candidateToken=Join-Path $candidate '03_Rapports_Sauvegardes\AUTORISATION_SAUVEGARDE_2TO_ANOMALIAZ_20261102'
  if((Test-Path -LiteralPath $candidate -PathType Container) -and (Test-Path -LiteralPath $candidateToken -PathType Leaf)){$cloud=$candidate;break}
}
if(!$cloud){Write-Host 'ANOMALIAZ_BACKUP_BLOCKED=AUTHORIZED_2TB_FOLDER_NOT_FOUND_ON_G_OR_H';exit 0}
$token=Join-Path $cloud '03_Rapports_Sauvegardes\AUTORISATION_SAUVEGARDE_2TO_ANOMALIAZ_20261102'
$manifestRoot=Join-Path $cloud '03_Rapports_Sauvegardes'
$driveLetter=$cloud.Substring(0,1)
$reportName='lots_UE5_sauvegarde_'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.csv'
$report=Join-Path $manifestRoot $reportName
$records=New-Object System.Collections.Generic.List[object]
[long]$newBytes=0
[int]$newFiles=0
[int]$verifiedExisting=0
[int]$skippedOversized=0
[int]$conflicts=0
[int]$processed=0

# Do not write unless the exact authorization marker is visible on the discovered mount.
if(!(Test-Path -LiteralPath $token -PathType Leaf)){
  Write-Host 'ANOMALIAZ_BACKUP_BLOCKED=CORRECT_2TB_CLOUD_MARKER_NOT_VISIBLE_TO_WINDOWS_RUNNER'
  exit 0
}
$volume=Get-CimInstance Win32_LogicalDisk -Filter ("DeviceID='"+$driveLetter+":'") -ErrorAction SilentlyContinue
if(!$volume -or !$volume.Size){throw ('Missing or unready Google Drive volume '+$driveLetter+':')}
$driveProcess=@(Get-Process -Name GoogleDriveFS -ErrorAction SilentlyContinue)
if($driveProcess.Count -eq 0){throw 'Google Drive for desktop process is not running; refusing local-only copy'}
if(!(Test-Path -LiteralPath $cloud -PathType Container)){throw 'Google Drive ANOMALIAZ destination root is not mounted'}
Write-Host ('ANOMALIAZ_BACKUP_CLOUD_MARKER_VERIFIED=true; marker_type=FILE; volume_label='+$volume.VolumeName)
Write-Host 'ANOMALIAZ_GOOGLE_DRIVE_DESKTOP_PROCESS_RUNNING=true'
Write-Host 'ANOMALIAZ_CLOUD_SYNC_CONFIRMATION=NOT_PROVEN_BY_LOCAL_COPY'
if((Get-Process -Name UnrealEditor,UnrealEditor-Cmd,AnomaliaZPrigimalia -ErrorAction SilentlyContinue)){
  Write-Host 'ANOMALIAZ_BACKUP_DEFERRED=UNREAL_RUNNING_NO_CONCURRENT_SNAPSHOT'
  exit 0
}
$free=[IO.DriveInfo]::new('C').AvailableFreeSpace
if($free -lt 23GB){
  Write-Host ('ANOMALIAZ_BACKUP_BLOCKED=INSUFFICIENT_C_CACHE_FREE GiB='+[math]::Round($free/1GB,2))
  exit 0
}
$roots=@(
  [pscustomobject]@{Name='Sketchfab'; Source='D:\ANOMALIA\sketchfab'; Dest='02_Modeles_3D\Sketchfab'; SkipTop=@()},
  [pscustomobject]@{Name='Stage_UE5_Maps'; Source='C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal\Content\Maps'; Dest='01_Cartes_UE5\01_Stage_15_Cartes\Content\Maps'; SkipTop=@()},
  [pscustomobject]@{Name='Original_D_Maps'; Source='D:\ANOMALIA\unreal\Content\Maps'; Dest='01_Cartes_UE5\02_Original_D\Content\Maps'; SkipTop=@()},
  [pscustomobject]@{Name='FabImports_Rest'; Source='D:\ANOMALIA\FabImports'; Dest='02_Modeles_3D\FabImports'; SkipTop=@('CitySample')},
  [pscustomobject]@{Name='CitySample'; Source='D:\ANOMALIA\FabImports\CitySample'; Dest='02_Modeles_3D\City Sample - Unreal Engine\CitySample'; SkipTop=@('DerivedDataCache','Intermediate','Saved','.vs')},
  [pscustomobject]@{Name='UE5_Content_Models'; Source='D:\ANOMALIA\unreal\Content'; Dest='02_Modeles_3D\UE5_Content_Assets'; SkipTop=@('Maps','__ExternalActors__','__ExternalObjects__')},
  [pscustomobject]@{Name='Stage_WorldPartition_Actors'; Source='C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal\Content\__ExternalActors__'; Dest='01_Cartes_UE5\01_Stage_15_Cartes\Content\__ExternalActors__'; SkipTop=@()},
  [pscustomobject]@{Name='Stage_WorldPartition_Objects'; Source='C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal\Content\__ExternalObjects__'; Dest='01_Cartes_UE5\01_Stage_15_Cartes\Content\__ExternalObjects__'; SkipTop=@()},
  [pscustomobject]@{Name='Original_D_WP_Actors'; Source='D:\ANOMALIA\unreal\Content\__ExternalActors__'; Dest='01_Cartes_UE5\02_Original_D\Content\__ExternalActors__'; SkipTop=@()},
  [pscustomobject]@{Name='Original_D_WP_Objects'; Source='D:\ANOMALIA\unreal\Content\__ExternalObjects__'; Dest='01_Cartes_UE5\02_Original_D\Content\__ExternalObjects__'; SkipTop=@()}
)
function Enumerate-FilesWithoutLinks {
  param([string]$Path,[string[]]$SkipTop)
  $stack=New-Object 'System.Collections.Generic.Stack[string]'
  $stack.Push($Path)
  while($stack.Count -gt 0){
    $d=$stack.Pop()
    foreach($item in (Get-ChildItem -LiteralPath $d -Force -ErrorAction Stop)){
      if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){continue}
      $rel=$item.FullName.Substring($Path.Length).TrimStart('\')
      if($SkipTop.Count -gt 0){
        $top=($rel -split '\\',2)[0]
        if($SkipTop -contains $top){continue}
      }
      if($item.PSIsContainer){$stack.Push($item.FullName)}
      else{Write-Output $item}
    }
  }
}
foreach($root in $roots){
  if(!(Test-Path -LiteralPath $root.Source -PathType Container)){
    Write-Host ('ANOMALIAZ_BACKUP_SOURCE_MISSING='+$root.Name)
    continue
  }
  $info=Get-Item -LiteralPath $root.Source -Force
  if($info.Attributes -band [IO.FileAttributes]::ReparsePoint){throw ('Unsafe source root junction: '+$root.Source)}
  Write-Host ('ANOMALIAZ_BACKUP_SCAN='+$root.Name)
  foreach($file in (Enumerate-FilesWithoutLinks -Path $root.Source -SkipTop $root.SkipTop)){
    $processed++
    $relative=$file.FullName.Substring($root.Source.Length).TrimStart('\')
    $target=Join-Path (Join-Path $cloud $root.Dest) $relative
    # Large files are eligible; the normal batch byte limit decides when to stop.
    if(Test-Path -LiteralPath $target -PathType Leaf){
      $there=Get-Item -LiteralPath $target
      if($there.Length -ne $file.Length){
        Write-Host ('ANOMALIAZ_BACKUP_CONFLICT_SIZE='+$root.Name+'\'+$relative)
        $conflicts++
        continue
      }
      $s=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
      $t=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
      if($s -ne $t){Write-Host ('ANOMALIAZ_BACKUP_CONFLICT_HASH='+$root.Name+'\'+$relative);$conflicts++;continue}
      $verifiedExisting++
      continue
    }
    if(!$Continuous -and ($newFiles -ge $MaxUploadFiles -or $newBytes+$file.Length -gt $MaxUploadBytes)){
      Write-Host 'ANOMALIAZ_BACKUP_BATCH_LIMIT_REACHED=TRUE'
      break
    }
    $available=[IO.DriveInfo]::new('C').AvailableFreeSpace
    if($available -lt 23GB){
      Write-Host 'ANOMALIAZ_BACKUP_STOPPED=LOW_C_CACHE_CAPACITY'
      break
    }
    if($file.Length -gt ($available - 23GB)){
      Write-Host ('ANOMALIAZ_BACKUP_SKIPPED_REQUIRES_MORE_C_CACHE='+$root.Name+'\'+$relative+' bytes='+$file.Length)
      continue
    }
    $dir=Split-Path -Parent $target
    if(!(Test-Path -LiteralPath $dir -PathType Container)){New-Item -ItemType Directory -Path $dir -Force|Out-Null}
    $temp=$target+'.ANOMALIAZ_COPY_PARTIAL'
    if(Test-Path -LiteralPath $temp){Write-Host ('ANOMALIAZ_BACKUP_PARTIAL_PRESENT_SKIP='+$relative);continue}
    try{
      Copy-Item -LiteralPath $file.FullName -Destination $temp -ErrorAction Stop
      $before=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
      $after=(Get-FileHash -LiteralPath $temp -Algorithm SHA256).Hash
      if($before -ne $after){throw ('Hash verification mismatch on '+$relative)}
      if(Test-Path -LiteralPath $target){throw ('Target appeared unexpectedly '+$relative)}
      Move-Item -LiteralPath $temp -Destination $target -ErrorAction Stop
      $records.Add([pscustomobject]@{SourceGroup=$root.Name;RelativePath=$relative;Bytes=$file.Length;SHA256=$before;LocalCopyVerified=$true;CloudUploadConfirmed=$false})
      $newBytes += [long]$file.Length
      $newFiles++
      Write-Host ('ANOMALIAZ_BACKUP_LOCAL_COPY_VERIFIED='+$root.Name+'\'+$relative+' bytes='+$file.Length)
    }catch{
      Write-Host ('ANOMALIAZ_BACKUP_COPY_FAILED='+$root.Name+'\'+$relative+' '+$_.Exception.Message)
      break
    }
  }
  if(!$Continuous -and ($newFiles -ge $MaxUploadFiles -or $newBytes -ge [long]($MaxUploadBytes * 0.90))){break}
  if([IO.DriveInfo]::new('C').AvailableFreeSpace -lt 23GB){break}
}
if($records.Count -gt 0){
  $records|Export-Csv -Path $report -Encoding UTF8 -NoTypeInformation
}
Write-Host ('ANOMALIAZ_BACKUP_LOCAL_COPY_VERIFIED_FILES='+$newFiles)
Write-Host ('ANOMALIAZ_BACKUP_LOCAL_COPY_VERIFIED_GIB='+[math]::Round($newBytes/1GB,3))
Write-Host ('ANOMALIAZ_BACKUP_PREEXISTING_MATCHED_FILES='+$verifiedExisting)
Write-Host ('ANOMALIAZ_BACKUP_SKIPPED_OVER_768MB='+$skippedOversized)
Write-Host ('ANOMALIAZ_BACKUP_CONTINUOUS_MODE='+[bool]$Continuous)
Write-Host ('ANOMALIAZ_BACKUP_CONFLICTS='+$conflicts)
Write-Host ('ANOMALIAZ_BACKUP_FILES_SCANNED='+$processed)
Write-Host ('ANOMALIAZ_C_FREE_GIB_AT_END='+[math]::Round([IO.DriveInfo]::new('C').AvailableFreeSpace/1GB,2))
Write-Host ('ANOMALIAZ_D_FREE_GIB_AT_END='+[math]::Round([IO.DriveInfo]::new('D').AvailableFreeSpace/1GB,2))
Write-Host 'ANOMALIAZ_BACKUP_NOTE=COPY_ON_VIRTUAL_DRIVE_ONLY; CLOUD_SYNC_CONFIRMATION_REQUIRED_BEFORE_LOCAL_DELETIONS'
Write-Host 'ANOMALIAZ_BACKUP_ORIGINAL_FILES_DELETED=0'
