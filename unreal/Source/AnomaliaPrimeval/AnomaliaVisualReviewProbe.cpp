#include "AnomaliaVisualReviewProbe.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaVehiclePawn.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Camera/CameraActor.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerInput.h"
#include "GameFramework/FloatingPawnMovement.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "UnrealClient.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

AAnomaliaVisualReviewProbe::AAnomaliaVisualReviewProbe(){PrimaryActorTick.bCanEverTick=true;}
void AAnomaliaVisualReviewProbe::Finish(const FString& Error)
{
    FString File;FParse::Value(FCommandLine::Get(),TEXT("AnomaliaVisualReview="),File);
    auto Report=MakeShared<FJsonObject>();Report->SetStringField(TEXT("state"),Error.IsEmpty()?TEXT("PACKAGED_VISUAL_REVIEW_PASSED"):TEXT("FAILED"));
    Report->SetStringField(TEXT("error"),Error);Report->SetStringField(TEXT("map"),GetWorld()->GetMapName());
    Report->SetStringField(TEXT("rendererRequest"),TEXT("DX11/SM5 compatibility; Lumen and Nanite not verified by this run"));
    auto Array=[](const TArray<FString>& Values){TArray<TSharedPtr<FJsonValue>> Result;for(const auto& V:Values)Result.Add(MakeShared<FJsonValueString>(V));return Result;};
    Report->SetArrayField(TEXT("screenshots"),Array(Screenshots));Report->SetArrayField(TEXT("checks"),Array(Checks));Report->SetArrayField(TEXT("loadedMeshPaths"),Array(MeshPaths));
    Report->SetBoolField(TEXT("finalPhotorealismApproved"),false);
    Report->SetNumberField(TEXT("measuredCameraFrames"),MeasuredFrames);
    Report->SetNumberField(TEXT("averageFrameMs"),MeasuredFrames>0?MeasuredSeconds*1000/MeasuredFrames:0);
    Report->SetNumberField(TEXT("worstFrameMs"),WorstFrame*1000);
    Report->SetNumberField(TEXT("averageFps"),MeasuredSeconds>0?MeasuredFrames/MeasuredSeconds:0);
    Report->SetStringField(TEXT("performanceScope"),TEXT("Observed wall-clock frames during the three settled review camera views; not GPU timings or a performance certification"));
    FString Raw;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Raw));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(File),true);FFileHelper::SaveStringToFile(Raw,*File);
    SetActorTickEnabled(false);FGenericPlatformMisc::RequestExit(false);
}
void AAnomaliaVisualReviewProbe::Tick(float Dt)
{
    Super::Tick(Dt);
#if !UE_BUILD_SHIPPING
    const double Now=FPlatformTime::Seconds();if(Started==0){Started=Now;Next=Now+8;}
    if(Phase==5 && PreviousFrame>0)
    { const double Frame=Now-PreviousFrame;MeasuredSeconds+=Frame;WorstFrame=FMath::Max(WorstFrame,Frame);++MeasuredFrames; }
    PreviousFrame=Now;
    if(Now-Started>150){Finish(FString::Printf(TEXT("Visual review timed out phase %d"),Phase));return;}
    auto* PC=GetWorld()->GetFirstPlayerController();if(!PC||Now<Next)return;
    auto Input=[PC](FKey Key,EInputEvent Event){PC->InputKey(FInputKeyParams(Key,Event,Event==IE_Pressed?1.:0.,false,FInputDeviceId::CreateFromInternalId(0)));};
    if(Phase==0)
    {
        Survivor=Cast<AAnomaliaSurvivor>(PC->GetPawn());if(!Survivor.IsValid())return;
        int32 Trees=0,Grass=0,Rocks=0;bool House=false,Terrain=false,Road=false;
        for(TActorIterator<AActor> It(GetWorld());It;++It)
        {
            if(!It->ActorHasTag(TEXT("ANOMALIA_VisualValidation_v1_Owner")))continue;
            // Editor camera visualization meshes are not visible scene art.
            if(auto* Camera=Cast<ACameraActor>(*It)){Cameras.Add(Camera);continue;}
            if(auto* Vehicle=Cast<AAnomaliaVehiclePawn>(*It))Car=Vehicle;
            if(auto* Component=It->FindComponentByClass<UStaticMeshComponent>())
            {
                UStaticMesh* Mesh=Component->GetStaticMesh();if(!Mesh){Finish(TEXT("Missing cooked review art"));return;}
                const FString Path=Mesh->GetPathName();
                if(!Path.StartsWith(TEXT("/Game/Anomalia/VisualValidation_v1/"))){Finish(TEXT("Review map contains fallback geometry: ")+Path);return;}
                MeshPaths.AddUnique(Path);
                if(It->GetName().IsEmpty()||Component->GetNumMaterials()<1){Finish(TEXT("Review material missing"));return;}
                if(Path.Contains(TEXT("/island_tree_02/")))++Trees;
                if(Path.Contains(TEXT("/grass_medium_01/")))++Grass;
                if(Path.Contains(TEXT("/rock_moss_set_01/")))++Rocks;
                House|=Path.Contains(TEXT("/detached_house/"));Terrain|=Path.Contains(TEXT("/forest_ground_04/"));Road|=Path.Contains(TEXT("/asphalt_02/"));
            }
        }
        if(!House||!Terrain||!Road||Trees<18||Grass<24||Rocks<3||MeshPaths.Num()!=7||Cameras.Num()!=3||!Car.IsValid()||Car->Body->GetStaticMesh()!=Car->PresentationMeshOverride.Get())
        {Finish(TEXT("Incomplete imported-art review scene or vehicle binding"));return;}
        Checks.Add(TEXT("cooked_house_tree_grass_rock_terrain_road_and_detailed_car"));
        Checks.Add(TEXT("no_engine_basic_shape_fallbacks_in_review_scene"));
        Before=Survivor->GetActorLocation();PC->SetControlRotation(FRotator::ZeroRotator);Input(EKeys::W,IE_Pressed);Next=Now+1;Phase=1;return;
    }
    if(Phase==1)
    {
        Input(EKeys::W,IE_Released);
        if(FVector::Dist2D(Before,Survivor->GetActorLocation())<100){Finish(TEXT("Character cannot explore review terrain"));return;}
        Checks.Add(TEXT("keyboard_walk_on_textured_review_terrain"));CarStart=Car->GetActorLocation();
        Survivor->SetActorLocation(CarStart+FVector(0,220,100),false,nullptr,ETeleportType::TeleportPhysics);
        if(!Car->EnterVehicle(PC,Survivor.Get())){Finish(TEXT("Detailed vehicle cannot be entered"));return;}
        Input(EKeys::W,IE_Pressed);Next=Now+1;Phase=2;return;
    }
    if(Phase==2)
    {
        Input(EKeys::W,IE_Released);
        if(FVector::Dist2D(CarStart,Car->GetActorLocation())<100){Finish(TEXT("Detailed vehicle did not move"));return;}
        Input(EKeys::E,IE_Pressed);Input(EKeys::E,IE_Released);Next=Now+.2;Phase=3;return;
    }
    if(Phase==3)
    {
        if(PC->GetPawn()!=Survivor.Get()){Finish(TEXT("Detailed vehicle exit failed"));return;}
        Checks.Add(TEXT("detailed_vehicle_enter_accelerate_exit_preserves_survivor"));
        Car->Movement->StopMovementImmediately();Car->SetActorLocation(CarStart,false,nullptr,ETeleportType::TeleportPhysics);
        Survivor->SetActorLocation(FVector(6000,-6000,150),false,nullptr,ETeleportType::TeleportPhysics);
        Phase=4;
    }
    if(Phase==4)
    {
        if(Shot>=Cameras.Num()){Finish();return;}
        PC->SetViewTarget(Cameras[Shot].Get());Next=Now+4;Phase=5;return;
    }
    if(Phase==5)
    {
        FString File;FParse::Value(FCommandLine::Get(),TEXT("AnomaliaVisualReview="),File);
        const FString Image=FPaths::Combine(FPaths::GetPath(File),FString::Printf(TEXT("visual-review-%d.png"),Shot));
        FScreenshotRequest::RequestScreenshot(Image,false,false);Screenshots.Add(Image);Next=Now+2;Phase=6;return;
    }
    if(Phase==6)
    {
        if(IFileManager::Get().FileSize(*Screenshots.Last())<10000){Finish(TEXT("Fresh actual game screenshot missing"));return;}
        ++Shot;Phase=4;
    }
#endif
}
