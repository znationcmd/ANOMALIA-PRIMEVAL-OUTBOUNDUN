[CmdletBinding()]
param([string]$ReportPath=(Join-Path $env:RUNNER_TEMP 'anomaliaz-falc-native-original-source-prep.json'))
$ErrorActionPreference='Stop'
$stage='C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal'
$root=Join-Path $stage 'TerrainSource\FALC'
$zipName='FALC_CARTE_10_REFERENCE_ET_HEIGHTMAP_26_5KM*.zip'
$expectedZipSHA256='c389a367d26a5cdab2d7e73b8129d45f9cf3e46bbe6e3b59a41bca7fd9ac7db5'
$expected='1d3ff52ed30338b59e6130a37aacc7e2a34367b7bcfe6b5b7'
$expectedReference='d31548b922e251ca06e06cb2d05359089685932e347a6237bb3f8e1782ca4222'
$manifestName='FALC_IMPORT_MANIFEST.json'
$result=[ordered]@{state='NOT_STARTED';worldName='F.A.L.C';worldSizeKm=26.5;
   sourceZip=$null;original2017RawSHA256=$expected;originalReferenceSHA256=$expectedReference;
   original14WorldsUntouched=$true;projectDModified=$false;sourceVerified=$false;error=$null}
function Save {
  $parent=Split-Path -Parent $ReportPath
  if(!(Test-Path $parent)){New-Item -ItemType Directory -Force -Path $parent|Out-Null}
  $result|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $ReportPath -Encoding UTF8
}
function Hash([string]$path){(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
try{
  $marker=Join-Path $stage '.skarvik-ci-stage-marker'
  if(!(Test-Path -LiteralPath $marker) -or (Get-Content -LiteralPath $marker -Raw).Trim() -ne '41188816555'){throw 'Untrusted final seven-island SKARVIK project'}
  if(!(Test-Path -LiteralPath (Join-Path $stage 'AnomaliaZPrigimalia.uproject'))){throw 'Native UE5 project missing'}
  if(Test-Path (Join-Path $stage 'Content\Maps\PRIGIMALIA_FALC.umap')){throw 'Original FALC World already exists, require re-open test not recreation'}
  if(@(Get-Process -Name UnrealEditor,UnrealEditor-Cmd,UnrealBuildTool,ShaderCompileWorker,MSBuild -ErrorAction SilentlyContinue).Count){throw 'Unreal Editor or build active: refuse touching source'}
  foreach($n in @('PRIGIMALIA_SKARVIK_FINAL_v1','ANOMALIA_Inhabited_v2','PRIGIMALIA_KARSKOV',
      'PRIGIMALIA_VORGRAD','PRIGIMALIA_NEMORIS','PRIGIMALIA_DRAKHEIM',
      'PRIGIMALIA_SOLYNACALYRA','PRIGIMALIA_NEXAVARKHOS',
      'PRIGIMALIA_CHERNASKALUXRIA','PRIGIMALIA_KOLCHIEM_ORIGINS',
      'PRIGIMALIA_ROSKATVIA_B1','PRIGIMALIA_NOGOKV_51',
      'PRIGIMALIA_PARADISIOMANIA','PRIGIMALIA_DEADROOT')){
     if(!(Test-Path -LiteralPath (Join-Path $stage ('Content\Maps\'+$n+'.umap')))){throw ('One of 14 genuine native worlds missing: '+$n)}
  }
  $candidateRoot=@(
    (Join-Path $env:USERPROFILE 'Downloads'),(Join-Path $env:USERPROFILE 'Desktop'),
    'C:\Users\Public\Downloads','D:\ANOMALIAZ','D:\ANOMALIAZ\TerrainSource\FALC',
    'D:\Downloads',(Join-Path $env:GITHUB_WORKSPACE 'source-artifacts')
  )
  foreach($u in (Get-ChildItem 'C:\Users' -Directory -ErrorAction SilentlyContinue)){
    foreach($sub in @('Downloads','Desktop','OneDrive\Downloads','OneDrive\Desktop')){
      $candidateRoot+=Join-Path $u.FullName $sub
    }
  }
  $raw=Join-Path $root 'FALC_26_5KM_MASTER_2017.r16'
  $reference=Join-Path $root 'FALC_REFERENCE_ORIGINALE.jpeg'
  $manifest=Join-Path $root $manifestName
  $hasOriginalOnStage = (Test-Path -LiteralPath $raw -PathType Leaf) -and
    (Test-Path -LiteralPath $reference -PathType Leaf) -and
    (Test-Path -LiteralPath $manifest -PathType Leaf)
  if ($hasOriginalOnStage) {
    $hasOriginalOnStage = (((Hash $raw) -eq $expected) -and ((Hash $reference) -eq $expectedReference))
  }
  if ($hasOriginalOnStage) {
    $result.state='ORIGINAL_FALC_USER_RAW16_ALREADY_STAGED_AND_HASH_VERIFIED'
    $result.sourceVerified=$true
  }else{
    $found=$null
    foreach($directory in @($candidateRoot | Select-Object -Unique)){
      if(!(Test-Path -LiteralPath $directory -PathType Container)){continue}
      $entry=Get-Item -LiteralPath $directory -Force
      if(($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){continue}
      foreach($file in @((Get-ChildItem -LiteralPath $directory -Filter $zipName -File -Recurse -ErrorAction SilentlyContinue))){
        if($file.Length -gt 9000000 -and $file.Length -lt 17000000 -and (Hash $file.FullName) -eq $expectedZipSHA256){$found=$file.FullName;break}
      }
      if($found){break}
    }
    if(!$found){throw 'FALC_ORIGINAL_ZIP_NOT_ON_PC: download the existing FALC_CARTE_10_REFERENCE_ET_HEIGHTMAP_26_5KM.zip into Windows Downloads; no substitute map will be generated.'}
    $result.sourceZip=$found
    $result.originalZipSHA256=$expectedZipSHA256
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip=[System.IO.Compression.ZipFile]::OpenRead($found)
    try{
      $files=@(
        @{entry='FALC_26_5KM/FALC_26_5KM_MASTER_2017.r16';dst=$raw;sha=$expected;bytes=8136578},
        @{entry='FALC_26_5KM/FALC_REFERENCE_ORIGINALE.jpeg';dst=$reference;sha=$expectedReference;bytes=1040567},
        @{entry='FALC_26_5KM/FALC_IMPORT_MANIFEST.json';dst=$manifest;sha=$null;bytes=1811}
      )
      $need=0
      foreach($item in $files){
        $zipEntry=$zip.GetEntry($item.entry)
        if(!$zipEntry -or $zipEntry.Length -ne $item.bytes){throw ('Untrusted original ZIP has missing or wrong entry '+$item.entry)}
        if(Test-Path -LiteralPath $item.dst){
          if($item.sha -and (Hash $item.dst) -eq $item.sha){continue}
          throw ('Original FALC source directory contains different existing file; do not overwrite: '+$item.dst)
        }
        $need+=$item.bytes
      }
      if(([IO.DriveInfo]::new('C')).AvailableFreeSpace -lt $need+15GB){throw 'Not enough C disk space for authentic FALC source and UE5 build reserve'}
      if(!(Test-Path -LiteralPath $root)){New-Item -ItemType Directory -Path $root -Force|Out-Null}
      foreach($item in $files){
        if(Test-Path -LiteralPath $item.dst){continue}
        $temp=$item.dst+'.extract-'+$env:GITHUB_RUN_ID+'.tmp'
        $stream=[IO.File]::Create($temp)
        try{
          $inStream=($zip.GetEntry($item.entry)).Open()
          try{$inStream.CopyTo($stream)}finally{$inStream.Dispose()}
        }finally{$stream.Dispose()}
        if((Get-Item -LiteralPath $temp).Length -ne $item.bytes){Remove-Item -LiteralPath $temp -Force;throw 'Extracted original size mismatch'}
        if($item.sha -and (Hash $temp) -ne $item.sha){Remove-Item -LiteralPath $temp -Force;throw 'Extracted original SHA mismatch'}
        Move-Item -LiteralPath $temp -Destination $item.dst -ErrorAction Stop
      }
    }finally{$zip.Dispose()}
    if((Hash $raw) -ne $expected -or (Hash $reference) -ne $expectedReference){
      throw 'The original FALC source is not SHA256-identical to the 31 Oct version'
    }
    $result.sourceVerified=$true
    $result.state='EXACT_ORIGINAL_FALC_RAW16_2017_AND_PHOTO_STAGED_IN_C_ONLY'
  }
  $m=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json
  if($m.masterSha256 -ne $expected -or $m.referenceImageSha256 -ne $expectedReference -or $m.masterAxis -ne 2017){
    throw 'FALC manifest not authentic after extraction'
  }
}catch{
  $result.error=$_.Exception.Message
  $result.state='FALC_SOURCE_NOT_READY_OR_SAFETY_GUARD_STOPPED'
}finally{
  Save
  Write-Host ('ANOMALIAZ_FALC_ORIGINAL_SOURCE_STATUS='+$result.state)
  Write-Host ('ANOMALIAZ_FALC_ORIGINAL_SOURCE_ZIP='+$result.sourceZip)
  Write-Host ('ANOMALIAZ_FALC_SOURCE_SHA256_VERIFIED='+$result.sourceVerified)
  Write-Host 'ANOMALIAZ_FALC_ORIGINAL_14_MAPS_MODIFIED=false'
  if($result.error){Write-Host ('ANOMALIAZ_FALC_SOURCE_BLOCKER='+$result.error)}
}
if(!$result.sourceVerified){exit 2}
