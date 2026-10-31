# Copy only non-Megascans static City Sample decor into isolated UE5 stage.
# Stage has verified nine core folders. Never delete or alter original assets on D.
[CmdletBinding()]
param([string]$ReportPath='')
$ErrorActionPreference='Stop'
$src='D:\ANOMALIA\FabImports\CitySample\Content'
$stage='C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal'
$dest=Join-Path $stage 'Content'
$wanted=@('Prop','Effect','WFC','MSPresets','Lookdev')
$blocked=@('Crowd','Vehicle')
$r=[ordered]@{state='BLOCKED';filesCopied=0;bytesCopied=0;sourceProtected=$true;crowdExcluded=$true;vehiclesExcluded=$true;megascansExcludedPendingDisk=$true;cityNotIntegrated=$true;nativeSM5NotPlaytested=$true;folders=@()}
try{
 $marker=Join-Path $stage '.skarvik-ci-stage-marker'
 if(!(Test-Path -LiteralPath $marker) -or ((Get-Content -LiteralPath $marker -Raw).Trim() -ne '41188816555')){throw 'Stage marker invalid'}
 foreach($f in @('Content\Maps\PRIGIMALIA_SKARVIK_CITY_v1.umap','AnomaliaZPrigimalia.uproject')){
  if(!(Test-Path -LiteralPath (Join-Path $stage $f) -PathType Leaf)){throw "Required staged world absent: $f"}
 }
 if(@(Get-Process -Name UnrealEditor,UnrealEditor-Cmd,AnomaliaPrimeval,AnomaliaZPrigimalia -ErrorAction SilentlyContinue).Count){throw 'Unreal process running'}
 foreach($f in $blocked){
  if(Test-Path -LiteralPath (Join-Path $dest $f)){throw "Excluded content exists: $f"}
 }
 [long]$needed=0
 foreach($name in $wanted){
  $p=Join-Path $src $name
  if(!(Test-Path -LiteralPath $p -PathType Container)){throw "Missing source $p"}
  foreach($f in (Get-ChildItem -LiteralPath $p -File -Recurse -Force -ErrorAction Stop)){$needed+=[long]$f.Length}
 }
 [long]$free=([IO.DriveInfo]::new('C')).AvailableFreeSpace
 $r.bytesPlanned=$needed;$r.freeBeforeGiB=[math]::Round($free/1GB,2)
 if($free -lt ($needed+24GB)){throw 'Free C below requested extras plus 24 GiB of safety headroom'}
 foreach($name in $wanted){
  $from=Join-Path $src $name;$to=Join-Path $dest $name
  if(Test-Path -LiteralPath $to -PathType Container){throw "Existing extra folder $name: refuse overwrite"}
  & robocopy.exe $from $to /E /R:1 /W:1 /NP /NFL /NDL /NJH /NJS
  $code=$LASTEXITCODE
  if($code -ge 8){throw "Robocopy failed $name code=$code"}
  [long]$srcBytes=0;[long]$dstBytes=0;$srcCount=0;$dstCount=0
  foreach($f in (Get-ChildItem -LiteralPath $from -File -Recurse -Force -ErrorAction Stop)){$srcCount++;$srcBytes+=[long]$f.Length}
  foreach($f in (Get-ChildItem -LiteralPath $to -File -Recurse -Force -ErrorAction Stop)){$dstCount++;$dstBytes+=[long]$f.Length}
  if($srcCount -ne $dstCount -or $srcBytes -ne $dstBytes){throw "Incomplete copy of $name"}
  $r.filesCopied+=$dstCount;$r.bytesCopied+=$dstBytes
  $r.folders+=@([ordered]@{name=$name;files=$dstCount;bytes=$dstBytes})
  Write-Host ("SKARVIK_DECOR_COPIED={0} FILES={1} GIB={2:N3}" -f $name,$dstCount,($dstBytes/1GB))
 }
 foreach($f in $blocked){
  if(Test-Path -LiteralPath (Join-Path $dest $f)){throw "Excluded content unexpectedly copied $f"}
 }
 $r.state='NON_MEGASCANS_DECOR_STAGED_CITY_NOT_INTEGRATED'
 $r.freeAfterGiB=[math]::Round(([IO.DriveInfo]::new('C')).AvailableFreeSpace/1GB,2)
} catch {
 $r.state='BLOCKED';$r.error=$_.Exception.Message
 Write-Host ('SKARVIK_DECOR_BLOCKED='+$r.error)
} finally{
 $json=$r|ConvertTo-Json -Depth 8
 Write-Host $json
 if($ReportPath){[IO.File]::WriteAllText($ReportPath,$json,(New-Object System.Text.UTF8Encoding($false)))}
}
if($r.state -eq 'BLOCKED'){exit 2}
exit 0
