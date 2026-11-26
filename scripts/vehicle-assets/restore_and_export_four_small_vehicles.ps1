$ErrorActionPreference='Stop'
$root='D:\ANOMALIA\unreal'
$project=Join-Path $root 'AnomaliaPrimeval.uproject'
$editor='C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$build='C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat'
if(!(Test-Path -LiteralPath $project -PathType Leaf)){throw 'ANOMALIA Unreal project not found'}
$busy=@(Get-Process -Name UnrealEditor,UnrealEditor-Cmd,UnrealBuildTool,AnomaliaPrimeval,AnomaliaZPrigimalia -ErrorAction SilentlyContinue|Where-Object{-not $_.HasExited})
if($busy.Count){throw 'Existing Unreal session preserved'}
$freeC=(Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace
$freeD=(Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='D:'").FreeSpace
if($freeC -lt 6GB -or $freeD -lt 6GB){throw "Disk preflight: C=$([math]::Round($freeC/1GB,1))GB D=$([math]::Round($freeD/1GB,1))GB"}
$nl=[Environment]::NewLine
$catalog=Join-Path $root 'Source\AnomaliaPrimeval\AnomaliaVehicleCatalog.cpp'
$header=Join-Path $root 'Source\AnomaliaPrimeval\AnomaliaVehiclePawn.h'
$pawn=Join-Path $root 'Source\AnomaliaPrimeval\AnomaliaVehiclePawn.cpp'
$catText=Get-Content -LiteralPath $catalog -Raw
$moto='        MakeVehicle(TEXT("motorcycle"), TEXT("Moto"), D::Ground, 190, 2, 6),'
if(!$catText.Contains($moto)){throw 'Expected existing motorcycle row missing'}
if(!$catText.Contains('MakeVehicle(TEXT("scooter"),')){
  $catText=$catText.Replace($moto,$moto+$nl+'        MakeVehicle(TEXT("scooter"), TEXT("Scooter"), D::Ground, 90, 2, 8),')
  Set-Content -LiteralPath $catalog -Value $catText -Encoding utf8
}
$headText=Get-Content -LiteralPath $header -Raw
if(!$headText.Contains('class UAudioComponent;')){$headText=$headText.Replace('class UFloatingPawnMovement;','class UAudioComponent;'+$nl+'class UFloatingPawnMovement;')}
if(!$headText.Contains('TObjectPtr<UAudioComponent> EngineAudio;')){
  $anchor='    TObjectPtr<UStaticMeshComponent> Body;'
  if(!$headText.Contains($anchor)){throw 'Vehicle pawn mesh declaration changed'}
  $headText=$headText.Replace($anchor,$anchor+$nl+$nl+'    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Vehicle|Audio")'+$nl+'    TObjectPtr<UAudioComponent> EngineAudio;')
}
Set-Content -LiteralPath $header -Value $headText -Encoding utf8
$cppText=Get-Content -LiteralPath $pawn -Raw
if(!$cppText.Contains('#include "Components/AudioComponent.h"')){
  $cppText=$cppText.Replace('#include "Components/StaticMeshComponent.h"','#include "Components/StaticMeshComponent.h"'+$nl+'#include "Components/AudioComponent.h"'+$nl+'#include "Sound/SoundBase.h"')
}
if(!$cppText.Contains('CreateDefaultSubobject<UAudioComponent>(TEXT("EngineAudio"))')){
  $anchor='    Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);'
  if(!$cppText.Contains($anchor)){throw 'Vehicle pawn body initialization changed'}
  $cppText=$cppText.Replace($anchor,$anchor+$nl+'    EngineAudio=CreateDefaultSubobject<UAudioComponent>(TEXT("EngineAudio"));'+$nl+'    EngineAudio->SetupAttachment(Body);'+$nl+'    EngineAudio->bAutoActivate=false;')
}
if(!$cppText.Contains('ANOMALIA_SMALL_VEHICLE_ENGINE_AUDIO')){
  $anchor='    ApplyDefinition();'
  $first=$cppText.IndexOf($anchor)
  if($first -lt 0){throw 'BeginPlay anchor missing'}
  $audio=@(
'    if(VehicleId==FName(TEXT("dirt_bike")) || VehicleId==FName(TEXT("motorcycle")) ||',
'       VehicleId==FName(TEXT("scooter")) || VehicleId==FName(TEXT("quad")))',
'    {',
'        USoundBase* EngineSound=LoadObject<USoundBase>(nullptr,TEXT("/Game/Audio/MetaSounds/Ambient/sfx_Amb_VEH_CityMotorcycle_meta.sfx_Amb_VEH_CityMotorcycle_meta"));',
'        if(!EngineSound) EngineSound=LoadObject<USoundBase>(nullptr,TEXT("/Game/Audio/MetaSounds/NPC/sfx_NPC_VehEngine_Hatchback_Meta.sfx_NPC_VehEngine_Hatchback_Meta"));',
'        if(EngineSound && EngineAudio)',
'        {',
'            EngineAudio->SetSound(EngineSound);',
'            EngineAudio->SetVolumeMultiplier(0.55f);',
'            EngineAudio->SetPitchMultiplier(VehicleId==FName(TEXT("quad"))?0.88f:1.0f);',
'            EngineAudio->Play();',
'            UE_LOG(LogTemp,Display,TEXT("ANOMALIA_SMALL_VEHICLE_ENGINE_AUDIO id=%s sound=%s"),*VehicleId.ToString(),*EngineSound->GetName());',
'        }',
'        else UE_LOG(LogTemp,Warning,TEXT("ANOMALIA_SMALL_VEHICLE_ENGINE_AUDIO_MISSING id=%s"),*VehicleId.ToString());',
'    }'
  ) -join $nl
  $cppText=$cppText.Insert($first+$anchor.Length,$nl+$audio)
}
Set-Content -LiteralPath $pawn -Value $cppText -Encoding utf8
Write-Output 'SOURCE_READY scooter_catalog=true native_engine_audio=true'
$busy=@(Get-Process -Name UnrealEditor,UnrealEditor-Cmd,UnrealBuildTool,AnomaliaPrimeval,AnomaliaZPrigimalia -ErrorAction SilentlyContinue|Where-Object{-not $_.HasExited})
if($busy.Count){throw 'Existing Unreal session preserved'}
& $build AnomaliaPrimevalEditor Win64 Development "-Project=$project" -WaitMutex -NoHotReloadFromIDE
if($LASTEXITCODE -ne 0){throw "Unreal editor module build failed with exit code $LASTEXITCODE"}
$out='D:\ANOMALIA\Exports\Vehicles-four-restored'
New-Item -ItemType Directory -Path $out -Force|Out-Null
$env:VEHICLE_EXPORT_OUT=$out
$pyPath=Join-Path $env:RUNNER_TEMP 'export-anomalia-small-vehicles.py'
$py=@(
'import json, os, hashlib',
'from pathlib import Path',
'import unreal',
'output=Path(os.environ["VEHICLE_EXPORT_OUT"])',
'models=[',
'("dirt_bike","/Game/Anomalia/Vehicles/dirt_bike/SM_dirt_bike.SM_dirt_bike"),',
'("motorcycle","/Game/Anomalia/Vehicles/motorcycle/SM_motorcycle.SM_motorcycle"),',
'("scooter","/Game/Anomalia/Vehicles/scooter/SM_scooter.SM_scooter"),',
'("quad","/Game/Anomalia/Vehicles/quad/SM_quad.SM_quad"),',
']',
'report=[]',
'for name,path in models:',
'    mesh=unreal.EditorAssetLibrary.load_asset(path)',
'    if not isinstance(mesh,unreal.StaticMesh): raise RuntimeError("Saved model missing: "+path)',
'    box=mesh.get_bounds().box_extent',
'    task=unreal.AssetExportTask()',
'    task.object=mesh',
'    task.filename=str(output/("ANOMALIA_"+name+".fbx"))',
'    task.automated=True',
'    task.prompt=False',
'    task.replace_identical=True',
'    task.options=unreal.FbxExportOption()',
'    task.options.ascii=False',
'    task.options.export_materials=True',
'    if not unreal.Exporter.run_asset_export_task(task): raise RuntimeError("FBX export failed: "+name)',
'    target=Path(task.filename)',
'    if not target.is_file() or target.stat().st_size<1024: raise RuntimeError("Empty FBX: "+name)',
'    report.append({"vehicle":name,"asset":path,"export":target.name,"bytes":target.stat().st_size,"dimensions_cm":[round(2*box.x,1),round(2*box.y,1),round(2*box.z,1)],"sha256":hashlib.sha256(target.read_bytes()).hexdigest()})',
'(output/"exports.json").write_text(json.dumps(report,indent=2),encoding="utf-8")',
'print("ANOMALIA_FOUR_VEHICLE_EXPORT_OK")'
);
Set-Content -LiteralPath $pyPath -Value $py -Encoding utf8
& $editor $project '-run=pythonscript' "-script=$pyPath" -nullrhi -unattended -NoAssetRegistryCache -SkipAssetScan "-abslog=$out\export-editor.log"
if($LASTEXITCODE -ne 0 -or !(Test-Path -LiteralPath (Join-Path $out 'exports.json') -PathType Leaf)){throw 'Unreal FBX export failed'}
$zip=Join-Path $out 'ANOMALIA_Cross_Moto_Scooter_Quad_FBX.zip'
Compress-Archive -LiteralPath (Join-Path $out 'ANOMALIA_dirt_bike.fbx'),(Join-Path $out 'ANOMALIA_motorcycle.fbx'),(Join-Path $out 'ANOMALIA_scooter.fbx'),(Join-Path $out 'ANOMALIA_quad.fbx'),(Join-Path $out 'exports.json') -DestinationPath $zip -CompressionLevel Optimal
if((Get-Item -LiteralPath $zip).Length -lt 1024){throw 'Export archive empty'}
Write-Output 'EXPORT_ARCHIVE_READY'
Get-Content -LiteralPath (Join-Path $out 'exports.json')
