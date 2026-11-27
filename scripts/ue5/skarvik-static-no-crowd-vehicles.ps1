# SKARVIK static City Sample staging. No Crowd or Vehicle folders are copied.
# Source D: is read-only; destination is the isolated C: UE5 project.
param([switch]$Apply,[string]$ReportPath='')
$ErrorActionPreference='Stop'
$src='D:\ANOMALIA\FabImports\CitySample\Content'
$dst='C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal\Content'
$stage='C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal'
$folders=@('__ExternalActors__','Building','City','Environment','Lighting','Map','Material','Road','Textures')
$extras=@('Megascans','Prop','Effect','WFC','MSPresets','Lookdev')
$result=[ordered]@{state='BLOCKED';sourcePreserved=$true;coreCopied=$false;extrasCopied=$false;crowdCopied=$false;vehiclesCopied=$false;cityIntegrated=$false;nativeSM5Tested=$false}
try {
 if(!(Test-Path (Join-Path $stage '.skarvik-ci-stage-marker'))){throw 'Isolated stage marker missing'}
 if((Get-Content (Join-Path $stage '.skarvik-ci-stage-marker') -Raw).Trim() -ne '41188816555'){throw 'Invalid stage marker'}
 if(!(Test-Path (Join-Path $stage 'Content\Maps\PRIGIMALIA_SKARVIK_CITY_v1.umap'))){throw 'Staged Unreal world missing'}
 if(!(Test-Path (Join-Path $src 'Map\Big_City_LVL.umap'))){throw 'City Sample world missing'}
 if((Test-Path (Join-Path $dst 'Crowd')) -or (Test-Path (Join-Path $dst 'Vehicle'))){throw 'Excluded folders already present in stage'}
 if(@(Get-Process UnrealEditor,UnrealEditor-Cmd,AnomaliaZPrigimalia -ErrorAction SilentlyContinue).Count){throw 'Unreal Editor is running'}
 $bytes=@{};[long]$core=0;[long]$additional=0
 foreach($f in @($folders)+@($extras)){
  $path=Join-Path $src $f
  if(!(Test-Path $path)){throw "Missing $path"}
  [long]$sum=0
  foreach($item in (Get-ChildItem -LiteralPath $path -Recurse -File -Force)){$sum+=$item.Length}
  $bytes[$f]=$sum
  if($f -in $folders){$core+=$sum}else{$additional+=$sum}
 }
 $free=[long]([IO.DriveInfo]::new('C')).AvailableFreeSpace
 $result.coreGiB=[math]::Round($core/1GB,2)
 $result.extrasGiB=[math]::Round($additional/1GB,2)
 $result.freeGiB=[math]::Round($free/1GB,2)
 Write-Host "SKARVIK_STATIC_AUDIT coreGiB=$($result.coreGiB) extrasGiB=$($result.extrasGiB) freeGiB=$($result.freeGiB)"
 if($free -lt ($core+30GB)){throw 'Insufficient C space for core + 30GB reserve'}
 if(-not $Apply){$result.state='SAFE_CORE_STATIC_ASSETS_READY';return}
 foreach($f in $folders){
  $from=Join-Path $src $f;$to=Join-Path $dst $f
  if(Test-Path $to){
   # The newly created SKARVIK terrain already owns external actor packages.
   # Preserve them; refuse any source/destination filename collision.
   foreach($existing in (Get-ChildItem -LiteralPath $to -Recurse -File -ErrorAction Stop)){
    $relative=$existing.FullName.Substring($to.Length).TrimStart('\\')
    if(Test-Path -LiteralPath (Join-Path $from $relative)){throw "Staged source filename collision in $f : $relative"}
   }
  }
  & robocopy.exe $from $to /E /R:1 /W:1 /NP /NFL /NDL /NJH /NJS
  if($LASTEXITCODE -ge 8){throw "Static folder copy failed: $f"}
  Write-Host "SKARVIK_STATIC_FOLDER_STAGED=$f"
 }
 $result.coreCopied=$true
 $free=[long]([IO.DriveInfo]::new('C')).AvailableFreeSpace
 if($free -ge ($additional+18GB)){
  foreach($f in $extras){
   $from=Join-Path $src $f;$to=Join-Path $dst $f
   if(Test-Path $to){throw "Destination folder already exists: $to"}
   & robocopy.exe $from $to /E /R:1 /W:1 /NP /NFL /NDL /NJH /NJS
   if($LASTEXITCODE -ge 8){throw "Extra static folder copy failed: $f"}
   Write-Host "SKARVIK_EXTRA_FOLDER_STAGED=$f"
  }
  $result.extrasCopied=$true
 }
 if((Test-Path (Join-Path $dst 'Crowd')) -or (Test-Path (Join-Path $dst 'Vehicle'))){throw 'Excluded folder unexpectedly found'}
 $result.state=if($result.extrasCopied){'STATIC_ASSETS_STAGED_NATIVE_CITY_NOT_INTEGRATED'}else{'CORE_STAGED_EXTRAS_BLOCKED_DISK'}
 $result.freeAfterGiB=[math]::Round(([IO.DriveInfo]::new('C')).AvailableFreeSpace/1GB,2)
} catch {$result.state='BLOCKED';$result.error=$_.Exception.Message;Write-Host "SKARVIK_STATIC_BLOCKED=$($result.error)"} finally {
 $json=$result|ConvertTo-Json -Depth 5
 Write-Host $json
 if($ReportPath){[IO.File]::WriteAllText($ReportPath,$json)}
}
if($result.state -eq 'BLOCKED'){exit 2}
# robocopy exit codes 1-7 are normal; do not leak their last exit code to GitHub.
exit 0
