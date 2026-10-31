# Safe F.A.L.C 26.5km photo-derived RAW16 native Unreal import on existing
# independent D: staging project. Requires the exact user-uploaded archive
# already present on Windows in Downloads/Desktop or stage root.
# Never changes original D:\ANOMALIA or any other map .umap.
$ErrorActionPreference='Stop'
$root='D:\ANOMALIAZ-PRIGIMALIA\unreal'
$original='D:\ANOMALIA\unreal\AnomaliaPrimeval.uproject'
$project=Join-Path $root 'AnomaliaZPrigimalia.uproject'
$marker=Join-Path $root 'Saved\BrandMigration\verified-source-backup.marker'
$master='FALC_26_5KM_MASTER_2017.r16'
$raw=Join-Path $root ('TerrainSource\FALC\'+$master)
$sha='1D3FF52ED30338B59E6130A37AACC7E2A34367B7BC3B28FAF4897B3BCFE6B5B7'
$zipSha='C389A367D26A5CDAB2D7E73B8129D45F9CF3E46BBE6E3B59A41BCA7FD9AC7DB5'
$archive='FALC_CARTE_10_REFERENCE_ET_HEIGHTMAP_26_5KM.zip'
$repoNative=Join-Path $env:GITHUB_WORKSPACE 'unreal\Source\AnomaliaZPrigimalia\World'
$stageNative=Join-Path $root 'Source\AnomaliaZPrigimalia\World'
$cpp=Join-Path $stageNative 'AnomaliaZPrigimaliaWorldImportLibrary.cpp'
$header=Join-Path $stageNative 'AnomaliaZPrigimaliaWorldImportLibrary.h'
$sourceCpp=Join-Path $repoNative 'AnomaliaZPrigimaliaWorldImportLibrary.cpp'
$sourceHeader=Join-Path $repoNative 'AnomaliaZPrigimaliaWorldImportLibrary.h'
$pythonSource=Join-Path $env:GITHUB_WORKSPACE 'unreal\Scripts\create_falc_from_user_raw16_native.py'
$pythonStage=Join-Path $root 'Scripts\create_falc_from_user_raw16_native.py'
$map=Join-Path $root 'Content\Maps\PRIGIMALIA_FALC.umap'
$build=Join-Path $env:UE_ROOT 'Engine\Build\BatchFiles\Build.bat'
$editor=Join-Path $env:UE_ROOT 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$out=Join-Path $env:RUNNER_TEMP ('FALC_NATIVE_IMPORT_'+$env:GITHUB_RUN_ID)
New-Item -ItemType Directory -Path $out -Force|Out-Null
$protected=@($original,
(Join-Path $root 'Content\Maps\ANOMALIA_Archipelago_v2.umap'),
(Join-Path $root 'Content\Maps\ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate.umap'),
(Join-Path $root 'Content\Maps\PRIGIMALIA_KOLCHIEM_ORIGINS_FULL.umap'))
foreach($file in @($project,$marker,$sourceCpp,$sourceHeader,$cpp,$header,$pythonSource,$build,$editor)+$protected){
 if(-not(Test-Path -LiteralPath $file -PathType Leaf)){throw ('Project/engine source missing: '+$file)}
}
if(@(Get-Process UnrealEditor,UnrealEditor-Cmd,UnrealBuildTool,robocopy -ErrorAction SilentlyContinue).Count -gt 0){throw 'Other native Unreal job active; cannot modify project'}
foreach($guard in @($map,(Join-Path $root 'Content\__ExternalActors__\Maps\PRIGIMALIA_FALC'),
(Join-Path $root 'Content\__ExternalObjects__\Maps\PRIGIMALIA_FALC'),$pythonStage)){
 if(Test-Path -LiteralPath $guard){throw ('FALC existing partial work protected: '+$guard)}
}
if((Get-PSDrive D).Free -lt 5GB){throw 'Low D: disk capacity, refusing native FALC import'}
$hashes=@{}
foreach($file in $protected){$hashes[$file]=(Get-FileHash $file -Algorithm SHA256).Hash}
$state='FAILED'
try{
 $candidate=$null
 if((Test-Path -LiteralPath $raw -PathType Leaf) -and (Get-FileHash $raw -Algorithm SHA256).Hash -eq $sha){$candidate=$raw}
 if(-not $candidate){
  $locations=@((Join-Path $env:USERPROFILE 'Downloads'),(Join-Path $env:USERPROFILE 'Desktop'),
    'D:\ANOMALIAZ-PRIGIMALIA','D:\ANOMALIAZ-PRIGIMALIA\unreal\TerrainSource\FALC')
  $zips=@()
  foreach($base in $locations){
   if(Test-Path -LiteralPath $base -PathType Container){
    $file=Join-Path $base $archive
    if(Test-Path -LiteralPath $file -PathType Leaf){$zips+=,$file}
   }
  }
  $verifiedZip=$null
  foreach($item in $zips){
    if((Get-FileHash -LiteralPath $item -Algorithm SHA256).Hash -eq $zipSha){$verifiedZip=$item;break}
  }
  if(-not $verifiedZip){
   $state='BLOCKED_USER_SOURCE_ZIP_NOT_ON_WINDOWS'
   Write-Host 'FALC_SOURCE_NOT_ON_WINDOWS_DOWNLOADS_OR_STAGE=true'
   throw 'Exact user F.A.L.C ZIP has not been downloaded to Windows. No native import attempted'
  }
  $extract=Join-Path $out 'user-zip-verified-extract'
  Expand-Archive -LiteralPath $verifiedZip -DestinationPath $extract
  $candidate=Join-Path $extract ('FALC_26_5KM\'+$master)
  if(-not(Test-Path -LiteralPath $candidate -PathType Leaf)){throw 'User archive missing master .r16'}
 }
 if((Get-Item -LiteralPath $candidate).Length -ne 2017*2017*2 -or (Get-FileHash $candidate -Algorithm SHA256).Hash -ne $sha){
  throw 'FALC heightfield is not byte-identical to user-provided approved RAW16'
 }
 if(-not(Test-Path -LiteralPath $raw)){
  $rawParent=Split-Path $raw -Parent
  if(-not(Test-Path -LiteralPath $rawParent)){New-Item -ItemType Directory -Path $rawParent -Force|Out-Null}
  Copy-Item -LiteralPath $candidate -Destination $raw
 }elseif((Get-FileHash $raw -Algorithm SHA256).Hash -ne $sha){
  throw 'Different source already installed at expected FALC path; refuse overwrite'
 }
 Write-Host 'FALC_USER_APPROVED_RAW16_HASH_VERIFIED=true'
 $sourceText=[IO.File]::ReadAllText($sourceCpp)
 $targetText=[IO.File]::ReadAllText($cpp)
 $startTag='AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateFalcReferenceLandscape()'
 $endTag='AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateArchipelagoLandscape()'
 $a=$sourceText.IndexOf($startTag,[StringComparison]::Ordinal)
 $b=$sourceText.IndexOf($endTag,$a,[StringComparison]::Ordinal)
 $at=$targetText.IndexOf($endTag,[StringComparison]::Ordinal)
 if($a -lt 0 -or $b -le $a -or $at -lt 0 -or $targetText.Contains($startTag)){throw 'Unexpected FALC native stage source layout'}
 $patch=$sourceText.Substring($a,$b-$a)
 if(-not $patch.Contains('InspectFalcReferenceComponents') -or
    -not $patch.Contains($master) -or $patch.Contains('Subsystem->ChangeGridSize(')){throw 'Unsafe native FALC source patch'}
 $targetText=$targetText.Substring(0,$at)+$patch+[Environment]::NewLine+$targetText.Substring($at)
 $sourceH=[IO.File]::ReadAllText($sourceHeader)
 $destH=[IO.File]::ReadAllText($header)
 $anchor='static AActor* CreateArchipelagoLandscape();'
 $decl='static AActor* CreateFalcReferenceLandscape();'
 $verify='static int32 InspectFalcReferenceComponents(AActor* Candidate);'
 if(-not $sourceH.Contains($decl) -or -not $sourceH.Contains($verify) -or
    -not $destH.Contains($anchor) -or $destH.Contains($decl)){throw 'FALC native header incompatible or previously installed'}
 $addition=[Environment]::NewLine+' UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")'+[Environment]::NewLine+' '+$decl
 $addition+=[Environment]::NewLine+' UFUNCTION(BlueprintPure, Category="ANOMALIA|World")'+[Environment]::NewLine+' '+$verify
 $destH=$destH.Replace($anchor,$anchor+$addition)
 $backup=Join-Path $root ('Saved\FALC\NativeSourceBackup_'+$env:GITHUB_RUN_ID)
 New-Item -ItemType Directory -Path $backup -Force|Out-Null
 Copy-Item -LiteralPath $cpp -Destination (Join-Path $backup 'WorldImportLibrary.cpp.bak')
 Copy-Item -LiteralPath $header -Destination (Join-Path $backup 'WorldImportLibrary.h.bak')
 [IO.File]::WriteAllText($cpp,$targetText,[Text.UTF8Encoding]::new($false))
 [IO.File]::WriteAllText($header,$destH,[Text.UTF8Encoding]::new($false))
 Copy-Item -LiteralPath $pythonSource -Destination $pythonStage
 & $build AnomaliaZPrigimaliaEditor Win64 Development "-Project=$project" -WaitMutex -NoHotReloadFromIDE -MaxParallelActions=2
 if($LASTEXITCODE -ne 0){throw 'FALC native C++ compilation failed'}
 $env:ANOMALIA_FALC_NATIVE_REPORT=Join-Path $out 'native-import.json'
 $log=Join-Path $out 'native-import.log'
 & $editor $project '-NullRHI' '-unattended' '-nopause' '-nosound' '-run=pythonscript' "-script=$pythonStage" "-abslog=$log"
 if($LASTEXITCODE -ne 0){throw 'FALC native RAW16 import failed, preserving partial new map for review'}
 if(-not(Test-Path -LiteralPath $env:ANOMALIA_FALC_NATIVE_REPORT -PathType Leaf)){throw 'Missing FALC native import receipt'}
 $nativeProof=Get-Content -LiteralPath $env:ANOMALIA_FALC_NATIVE_REPORT -Raw -Encoding UTF8|ConvertFrom-Json
 if($nativeProof.status -ne 'NATIVE_FALC_2017_RAW16_WORLD_SAVED_NOT_PLAYTESTED'){throw 'Native FALC importer did not validate full heightfield'}
 $state='FALC_USER_RAW16_NATIVE_MAP_SAVED_NOT_PLAYTESTED'
 Write-Host 'FALC_26_5KM_APPROVED_NATIVE_WORLD_IMPORTED=true'
}finally{
 $changes=@()
 foreach($f in $hashes.Keys){
  if(-not(Test-Path -LiteralPath $f -PathType Leaf) -or (Get-FileHash $f -Algorithm SHA256).Hash -ne $hashes[$f]){$changes+=,$f}
 }
 @{status=$state;verifiedMasterSha256=$sha;nativeWorldPackage='/Game/Maps/PRIGIMALIA_FALC';protectedMapHashChanges=@($changes);gameplayTested=$false}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $out 'summary.json') -Encoding UTF8
 if($changes.Count -gt 0){throw ('Protected worlds changed unexpectedly: '+($changes -join ', '))}
 Write-Host 'FALC_PROTECTED_DRAZOVIA_SKARVIK_KOLCHIEM_UNCHANGED=true'
}
