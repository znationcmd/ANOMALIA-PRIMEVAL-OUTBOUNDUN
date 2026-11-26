$ErrorActionPreference='Stop'
$root='D:\ANOMALIA\unreal'
$project=Join-Path $root 'AnomaliaPrimeval.uproject'
$editor='C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
if(!(Test-Path -LiteralPath $project -PathType Leaf)){throw 'ANOMALIA Unreal project not found'}
$busy=@(Get-Process -Name UnrealEditor,UnrealEditor-Cmd,UnrealBuildTool,AnomaliaPrimeval,AnomaliaZPrigimalia -ErrorAction SilentlyContinue|Where-Object{-not $_.HasExited})
if($busy.Count){throw 'Existing Unreal session preserved'}
foreach($rel in @('Content\Anomalia\Vehicles\dirt_bike\SM_dirt_bike.uasset','Content\Anomalia\Vehicles\motorcycle\SM_motorcycle.uasset','Content\Anomalia\Vehicles\scooter\SM_scooter.uasset','Content\Anomalia\Vehicles\quad\SM_quad.uasset')){
  if(!(Test-Path -LiteralPath (Join-Path $root $rel) -PathType Leaf)){throw "Original mesh package missing: $rel"}
}
$cppPath=Join-Path $root 'Source\AnomaliaPrimeval\AnomaliaVehiclePawn.cpp'
$cppText=Get-Content -LiteralPath $cppPath -Raw
if(!$cppText.Contains('const float ModelScale=VehicleId==FName(TEXT("scooter"))?0.1f:1.0f;')){
  $a='Body->SetStaticMesh(Mesh);'
  if(!$cppText.Contains($a)){throw 'Vehicle visual mesh assignment anchor missing'}
  $cppText=$cppText.Replace($a,$a+[Environment]::NewLine+'    const float ModelScale=VehicleId==FName(TEXT("scooter"))?0.1f:1.0f;'+[Environment]::NewLine+'    Body->SetRelativeScale3D(OriginalBodyTransform.GetScale3D()*ModelScale);')
  $a='const FVector BottomCenter(Bounds.Origin.X,Bounds.Origin.Y,Bounds.Origin.Z-Bounds.BoxExtent.Z);'
  if(!$cppText.Contains($a)){throw 'Vehicle mesh bounds anchor missing'}
  $cppText=$cppText.Replace($a,'const FVector BottomCenter=FVector(Bounds.Origin.X,Bounds.Origin.Y,Bounds.Origin.Z-Bounds.BoxExtent.Z)*ModelScale;')
  $cppText=$cppText.Replace('Bounds.BoxExtent.GetMax()*2.5','Bounds.BoxExtent.GetMax()*ModelScale*2.5')
  Set-Content -LiteralPath $cppPath -Value $cppText -Encoding utf8
}
$build='C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat'
$busy=@(Get-Process -Name UnrealEditor,UnrealEditor-Cmd,UnrealBuildTool,AnomaliaPrimeval,AnomaliaZPrigimalia -ErrorAction SilentlyContinue|Where-Object{-not $_.HasExited})
if($busy.Count){throw 'Existing Unreal session preserved'}
& $build AnomaliaPrimevalEditor Win64 Development "-Project=$project" -WaitMutex -NoHotReloadFromIDE
if($LASTEXITCODE -ne 0){throw "Unreal incremental build failed: $LASTEXITCODE"}
Write-Output 'SCOOTER_SCALE_COMPILED=0.1'
$out='D:\ANOMALIA\Exports\Vehicles-four-restored'
New-Item -ItemType Directory -Path $out -Force|Out-Null
$env:VEHICLE_EXPORT_OUT=$out
$py=Join-Path $env:GITHUB_WORKSPACE 'scripts\vehicle-assets\export_four_vehicles.py'
if(!(Test-Path -LiteralPath $py -PathType Leaf)){throw 'Vehicle FBX export script missing'}
& $editor $project '-run=pythonscript' "-script=$py" -nullrhi -unattended -NoAssetRegistryCache -SkipAssetScan "-abslog=$out\export-editor.log"
if($LASTEXITCODE -ne 0 -or !(Test-Path -LiteralPath (Join-Path $out 'exports.json') -PathType Leaf)){throw "Unreal FBX export failed: $LASTEXITCODE"}
$zip=Join-Path $out 'ANOMALIA_Cross_Moto_Scooter_Quad_FBX.zip'
Compress-Archive -LiteralPath (Join-Path $out 'ANOMALIA_dirt_bike.fbx'),(Join-Path $out 'ANOMALIA_motorcycle.fbx'),(Join-Path $out 'ANOMALIA_scooter.fbx'),(Join-Path $out 'ANOMALIA_quad.fbx'),(Join-Path $out 'exports.json') -DestinationPath $zip -CompressionLevel Optimal
if((Get-Item -LiteralPath $zip).Length -lt 1024){throw 'Vehicle export archive is empty'}
Write-Output 'FOUR_VEHICLE_EXPORT_OK'
Get-Content -LiteralPath (Join-Path $out 'exports.json')
