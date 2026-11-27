# Guarded full binary asset staging for City Sample into the isolated SKARVIK UE5 project.
# This never writes to D:\ANOMALIA, never runs when Unreal is active, and
# never claims that copying packages makes the world playable.
[CmdletBinding()]
param(
 [string]$SourceRoot='D:\ANOMALIA\FabImports\CitySample',
 [string]$StageRoot='C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal',
 [string]$ReportPath='',
 [switch]$Apply
)
$ErrorActionPreference='Stop'
function Full([string]$p){return [IO.Path]::GetFullPath($p).TrimEnd('\')}
function Snapshot([string]$p){
 $bytes=[long]0;$count=0
 if(-not(Test-Path -LiteralPath $p -PathType Container)){return [pscustomobject]@{bytes=0;files=0}}
 foreach($f in (Get-ChildItem -LiteralPath $p -Recurse -File -Force -ErrorAction Stop)){
  $bytes+=[long]$f.Length;$count++
 }
 return [pscustomobject]@{bytes=$bytes;files=$count}
}
$report=[ordered]@{
 state='BLOCKED';mode=$(if($Apply){'APPLY'}else{'AUDIT_ONLY'})
 source='';stage='';sourceBytes=0;sourceFiles=0
 cFreeGiB=0;bytesNeeded=0;copyAllowed=$false
 sourceFilesPreserved=$true;originalAnomaliaPreserved=$true
 newWorldAlreadyAuthored=$false;cityAssetsCopied=$false
 fullCityPlayable=$false;sm5VisualsVerified=$false;cityAddedToSkarvik48km=$false
 next='No binary copy has been performed'
}
try{
 $src=Full $SourceRoot;$stage=Full $StageRoot
 $expectedSrc='D:\ANOMALIA\FabImports\CitySample'
 $expectedStage='C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal'
 if($src -ine $expectedSrc -or $stage -ine $expectedStage){throw 'Unexpected source or destination: refusing operation'}
 $report.source=$src;$report.stage=$stage
 $marker=Join-Path $stage '.skarvik-ci-stage-marker'
 if(-not(Test-Path -LiteralPath $marker)){throw 'Staging marker absent'}
 if((Get-Content -LiteralPath $marker -Raw).Trim() -ne '41188816555'){throw 'Staging marker does not match original UE5 map run'}
 foreach($p in @((Join-Path $src 'CitySample.uproject'),(Join-Path $src 'Content\Map\Big_City_LVL.umap'),(Join-Path $stage 'AnomaliaZPrigimalia.uproject'),(Join-Path $stage 'Content\Maps\PRIGIMALIA_SKARVIK_CITY_v1.umap'), 'D:\ANOMALIA\unreal\Content\Maps\ANOMALIA_Archipelago_v2.umap')){
  if(!(Test-Path -LiteralPath $p -PathType Leaf)){throw ('Required source/stage map absent: '+$p)}
 }
 if(!(Test-Path -LiteralPath (Join-Path $src 'Content\__ExternalActors__'))){throw 'Missing complete World Partition external actors directory'}
 $report.newWorldAlreadyAuthored=$true
 $running=@(Get-Process -Name UnrealEditor,UnrealEditor-Cmd,AnomaliaZPrigimalia,AnomaliaPrimeval -ErrorAction SilentlyContinue)
 if($running.Count -gt 0){throw 'Unreal Editor/game active; refuse simultaneous file changes'}
 $stageContent=Join-Path $stage 'Content'
 $srcContent=Join-Path $src 'Content'
 $srcPlugins=Join-Path $src 'Plugins'
 $destPlugins=Join-Path $stage 'Plugins'
 $contents=Snapshot $srcContent;$plugins=Snapshot $srcPlugins
 $allBytes=[long]$contents.bytes+[long]$plugins.bytes
 $report.sourceBytes=$allBytes;$report.sourceFiles=$contents.files+$plugins.files
 $free=[long]([System.IO.DriveInfo]::new('C')).AvailableFreeSpace
 $report.cFreeGiB=[math]::Round($free/1GB,2)
 # Must leave 30GiB for shader compiles, Unreal intermediates and other user work.
 $reserve=[long](30GB)
 $report.bytesNeeded=$allBytes+$reserve
 Write-Host ("SKARVIK_COPY_PREFLIGHT_SOURCE_GIB={0:N2} FILES={1} C_FREE_GIB={2:N2} C_REQUIRED_GIB={3:N2}" -f ($allBytes/1GB),$report.sourceFiles,($free/1GB),($report.bytesNeeded/1GB))
 if($allBytes -lt (1GB)){throw 'Source City Sample looks incomplete (<1GiB); refuse artificial success'}
 if($free -lt $report.bytesNeeded){throw 'Insufficient C disk for full assets + 30GiB reserve; no partial copy'}
 # Refuse overwrites, including colliding named files from original ANOMALIA project.
 foreach($pair in @(@($srcContent,$stageContent),@($srcPlugins,$destPlugins))){
  $pRoot=$pair[0];$pDest=$pair[1]
  if(!(Test-Path -LiteralPath $pRoot -PathType Container)){continue}
  foreach($file in (Get-ChildItem -LiteralPath $pRoot -Recurse -File -Force)){
   $relative=$file.FullName.Substring($pRoot.Length).TrimStart('\')
   $d=Join-Path $pDest $relative
   if(Test-Path -LiteralPath $d -PathType Leaf){
    $other=Get-Item -LiteralPath $d
    if($other.Length -ne $file.Length -or (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $d -Algorithm SHA256).Hash){
      throw ('Conflicting preexisting asset; refuse overwrite: '+$relative)
    }
   }
  }
 }
 $report.copyAllowed=$true
 if(-not $Apply){$report.state='READY_TO_COPY_FULL_CITY_ASSETS';$report.next='Rerun with -Apply after reviewing disk and copy report';return}
 foreach($pair in @(@($srcContent,$stageContent),@($srcPlugins,$destPlugins))){
  $pRoot=$pair[0];$pDest=$pair[1]
  if(!(Test-Path -LiteralPath $pRoot -PathType Container)){continue}
  New-Item -ItemType Directory -Path $pDest -Force|Out-Null
  & robocopy.exe $pRoot $pDest /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /NP /NJH /NJS /NFL /NDL
  if($LASTEXITCODE -ge 8){throw ('City Sample Robocopy failed: '+$LASTEXITCODE)}
 }
 # Verify every source object matches an on-disk destination with the same size.
 $missing=0;$checked=0
 foreach($pair in @(@($srcContent,$stageContent),@($srcPlugins,$destPlugins))){
  $pRoot=$pair[0];$pDest=$pair[1]
  if(!(Test-Path -LiteralPath $pRoot -PathType Container)){continue}
  foreach($file in (Get-ChildItem -LiteralPath $pRoot -Recurse -File -Force)){
   $d=Join-Path $pDest $file.FullName.Substring($pRoot.Length).TrimStart('\')
   $checked++
   if(!(Test-Path -LiteralPath $d -PathType Leaf) -or (Get-Item -LiteralPath $d).Length -ne $file.Length){$missing++}
  }
 }
 if($missing -gt 0 -or $checked -ne $report.sourceFiles){throw "Copy incomplete: missing $missing of $checked"}
 $report.cityAssetsCopied=$true
 $report.state='FULL_CITY_BINARY_ASSETS_STAGED_WORLD_PARTITION_INTEGRATION_PENDING'
 $report.next='Resolve City Sample module/plugin dependencies, duplicate Big City via WorldPartitionRenameDuplicateBuilder into staging, disable Mass Traffic/Crowds and perform native SM5 PIE/packaged test'
 Write-Host ("SKARVIK_FULL_CITY_ASSET_FILES_STAGED=$checked")
} catch {
 $report.state='BLOCKED';$report.error=$_.Exception.Message
 Write-Host ('SKARVIK_ASSET_STAGING_BLOCKED='+$report.error)
} finally {
 $json=$report | ConvertTo-Json -Depth 8
 Write-Output $json
 if($ReportPath){
  $folder=Split-Path $ReportPath -Parent
  if(!(Test-Path -LiteralPath $folder)){New-Item -ItemType Directory -Path $folder -Force|Out-Null}
  [IO.File]::WriteAllText($ReportPath,$json,(New-Object System.Text.UTF8Encoding($false)))
 }
}
if($report.state -eq 'BLOCKED'){exit 2}
