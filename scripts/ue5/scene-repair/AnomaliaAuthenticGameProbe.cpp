#include "AnomaliaAuthenticGameProbe.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaDogCompanion.h"
#include "AnomaliaSessionWidget.h"
#include "Vehicles/AnomaliaChaosRoadVehicle.h"
#include "Vehicles/AnomaliaVehicleSurvival.h"
#include "Vehicles/AnomaliaVehiclePanelComponent.h"
#include "World/AnomaliaCityBlock.h"
#include "Camera/CameraComponent.h"
#include "Camera/CameraActor.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/PlayerInput.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Button.h"
#include "Components/Border.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformTime.h"
#include "HAL/PlatformMisc.h"
#include "UnrealClient.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

AAnomaliaAuthenticGameProbe::AAnomaliaAuthenticGameProbe()
{PrimaryActorTick.bCanEverTick=true;PrimaryActorTick.bTickEvenWhenPaused=true;}
void AAnomaliaAuthenticGameProbe::Screenshot(const TCHAR* Suffix)
{
    FString File;FParse::Value(FCommandLine::Get(),TEXT("AnomaliaAuthenticProbe="),File);
    FScreenshotRequest::RequestScreenshot(FPaths::ChangeExtension(File,TEXT(""))+Suffix,true,false);
}
void AAnomaliaAuthenticGameProbe::Finish(const FString& Error)
{
    FString File;FParse::Value(FCommandLine::Get(),TEXT("AnomaliaAuthenticProbe="),File);
    auto R=MakeShared<FJsonObject>();R->SetStringField(TEXT("state"),Error.IsEmpty()?TEXT("AUTHENTIC_GAMEPLAY_VERIFIED"):TEXT("FAILED"));
    R->SetStringField(TEXT("error"),Error);R->SetStringField(TEXT("map"),GetWorld()->GetMapName());
    R->SetNumberField(TEXT("phase"),Phase);R->SetNumberField(TEXT("cityMeshComponents"),CityMeshes);
    R->SetNumberField(TEXT("playerMovementCm"),Walked);R->SetNumberField(TEXT("dogMovementCm"),DogWalked);R->SetNumberField(TEXT("bmwMovementCm"),Driven);
    if(Survivor.IsValid()&&Survivor->GetMesh()->GetSkeletalMeshAsset())R->SetStringField(TEXT("playerMesh"),Survivor->GetMesh()->GetSkeletalMeshAsset()->GetPathName());
    TArray<TSharedPtr<FJsonValue>> Rows;for(const auto& C:Checks)Rows.Add(MakeShared<FJsonValueString>(C));R->SetArrayField(TEXT("checks"),Rows);
    FString Json;FJsonSerializer::Serialize(R,TJsonWriterFactory<>::Create(&Json));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(File),true);FFileHelper::SaveStringToFile(Json,*File);
    SetActorTickEnabled(false);FGenericPlatformMisc::RequestExit(false);
}
void AAnomaliaAuthenticGameProbe::Tick(float Dt)
{
    Super::Tick(Dt);
#if !UE_BUILD_SHIPPING
    const double Now=FPlatformTime::Seconds();if(Started==0){Started=Now;Next=Now+8;}
    if(Now-Started>180){Finish(TEXT("Authentic gameplay validation timed out"));return;}
    auto* PC=GetWorld()->GetFirstPlayerController();if(!PC)return;
    if(!Survivor.IsValid())Survivor=Cast<AAnomaliaSurvivor>(PC->GetPawn());
    auto* S=Survivor.Get();if(!S)return;
    AAnomaliaChaosRoadVehicle* Car=nullptr;AAnomaliaDogCompanion* Dog=nullptr;
    for(TActorIterator<AAnomaliaChaosRoadVehicle> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("ANOMALIA_AUTHENTIC_E39"))){Car=*It;break;}
    for(TActorIterator<AAnomaliaDogCompanion> It(GetWorld());It;++It)if(It->SurvivorOwner==S){Dog=*It;break;}
    auto Input=[PC](FKey Key,EInputEvent Event){PC->InputKey(FInputKeyParams(Key,Event,Event==IE_Pressed?1.:0.,false,FInputDeviceId::CreateFromInternalId(0)));};
    auto View=[this,PC](const FVector& Eye,const FVector& Target,float Fov)
    {
        if(!ReviewCamera.IsValid())ReviewCamera=GetWorld()->SpawnActor<ACameraActor>();
        ReviewCamera->SetActorLocation(Eye);ReviewCamera->SetActorRotation((Target-Eye).Rotation());
        ReviewCamera->GetCameraComponent()->SetFieldOfView(Fov);PC->SetViewTarget(ReviewCamera.Get());
    };
    if(Phase==0)
    {
        if(Now<Next)return;
        if(!GetWorld()->GetMapName().EndsWith(TEXT("PRIGIMALIA_SKARVIK_FINAL_v1"))){Finish(TEXT("The actual SKARVIK world is not running"));return;}
        auto* Body=S->GetMesh()->GetSkeletalMeshAsset();
        if(!Body||!Body->GetPathName().StartsWith(TEXT("/Game/Survival_Character/Meshes/SK_Survival_Character."))||!S->GetMesh()->GetAnimInstance())
        {Finish(TEXT("The owned animated Survival Character is not the possessed player"));return;}
        CityMeshes=0;
        for(TActorIterator<AActor> It(GetWorld());It;++It)
        {
            TArray<UStaticMeshComponent*> Components;It->GetComponents<UStaticMeshComponent>(Components);
            for(auto* C:Components)if(C&&C->GetStaticMesh())
            {
                const FString Path=C->GetStaticMesh()->GetPathName();
                if(Path.StartsWith(TEXT("/Game/Building/"))||Path.StartsWith(TEXT("/Game/City/")))++CityMeshes;
            }
        }
        if(!Car||!Dog||CityMeshes<10){if(Now-Started<90)return;Finish(TEXT("City Sample geometry, owned shepherd or native E39 is missing"));return;}
        if(!Car->RoadBodyMesh||!Car->RoadBodyMesh->GetPathName().StartsWith(TEXT("/Game/Anomalia/BMWE39RoadPresentation_v8/"))||!Car->HasValidRoadRig()||!Car->IsChaosDriveReady())
        {Finish(TEXT("The genuine E39 v7 is not configured as a physical driveable vehicle"));return;}
        if(!Dog->GetMesh()->GetSkeletalMeshAsset()||!Dog->GetMesh()->GetSkeletalMeshAsset()->GetPathName().StartsWith(TEXT("/Game/German_Shepherd_3D_Model/")))
        {Finish(TEXT("The actual German shepherd mesh is not loaded"));return;}
        Checks.Add(TEXT("real_skarvik_with_citysample_geometry"));Checks.Add(TEXT("owned_survival_character_with_locomotion"));Checks.Add(TEXT("genuine_e39_corrected_art_native_physics_rig"));Checks.Add(TEXT("owned_german_shepherd_assigned_to_player"));
        bool OriginalBlock=false,OriginalGroundFloor=false,OriginalRoad=false;
        for(TActorIterator<AAnomaliaCityBlock> It(GetWorld());It;++It)
        {
            if(It->SourceWorld!=TEXT("/Game/Map/Big_City_LVL") || It->GetOriginalInstanceCount()<1000)continue;
            OriginalBlock=true;
            for(const auto& Batch:It->Batches)if(Batch.Mesh)
            {
                const FString Path=Batch.Mesh->GetPathName();
                OriginalGroundFloor|=Path.Contains(TEXT("_L1_"));OriginalRoad|=Path.Contains(TEXT("/Road/"));
            }
        }
        if(!OriginalBlock||!OriginalGroundFloor||!OriginalRoad){Finish(TEXT("Complete original City Sample street block, ground floors or roads missing"));return;}
        if(!Car->bUseAuthoredRoadCameras||!Car->EngineBayMesh||!Car->EngineBayDetails->GetStaticMesh())
        {Finish(TEXT("Authored cameras or actual engine-bay geometry missing"));return;}
        Checks.Add(TEXT("original_citysample_block_including_ground_floors_and_roads"));
        auto* Menu=UAnomaliaSessionWidget::Open(PC,true);
        auto* Mods=Menu&&Menu->WidgetTree?Cast<UButton>(Menu->WidgetTree->FindWidget(TEXT("SessionMods"))):nullptr;
        if(!Mods){Finish(TEXT("Real main-menu WorkForge entry missing"));return;}
        Mods->OnClicked.Broadcast();
        auto* Forge=Cast<UBorder>(Menu->WidgetTree->FindWidget(TEXT("WorkshopFullScreen")));
        if(!Forge||Forge->GetVisibility()!=ESlateVisibility::Visible){Finish(TEXT("WorkForge failed to open in the real game's main menu"));return;}
        Screenshot(TEXT("-workforge.png"));Phase=1;Next=Now+2;return;
    }
    if(!Car||!Dog){Finish(TEXT("A genuine gameplay actor disappeared"));return;}
    if(Phase==1)
    {
        if(Now<Next)return;auto* Menu=UAnomaliaSessionWidget::Open(PC,true);
        auto* Back=Menu&&Menu->WidgetTree?Cast<UButton>(Menu->WidgetTree->FindWidget(TEXT("WorkshopReturn"))):nullptr;
        if(!Back){Finish(TEXT("WorkForge return button missing"));return;}Back->OnClicked.Broadcast();
        Screenshot(TEXT("-main-menu.png"));Phase=2;Next=Now+2;return;
    }
    if(Phase==2)
    {
        if(Now<Next)return;auto* Menu=UAnomaliaSessionWidget::Open(PC,true);
        auto* Play=Menu&&Menu->WidgetTree?Cast<UButton>(Menu->WidgetTree->FindWidget(TEXT("SessionPlay"))):nullptr;
        if(!Play){Finish(TEXT("Real game Play button missing"));return;}Play->OnClicked.Broadcast();
        auto* Pause=UAnomaliaSessionWidget::Open(PC,false);
        if(!Pause||Pause->WidgetTree->FindWidget(TEXT("SessionMods"))||Pause->WidgetTree->FindWidget(TEXT("WorkshopFullScreen")))
        {Finish(TEXT("WorkForge leaked into gameplay pause"));return;}
        auto* Resume=Cast<UButton>(Pause->WidgetTree->FindWidget(TEXT("SessionPlay")));
        if(!Resume){Finish(TEXT("Gameplay resume button missing"));return;}Resume->OnClicked.Broadcast();
        Checks.Add(TEXT("main_menu_workforge_and_separate_gameplay_pause"));
        Before=S->GetActorLocation();DogBefore=Dog->GetActorLocation();Dog->RequestCommand(EAnomaliaDogCommand::Follow);
        Phase=3;Next=Now+8;return;
    }
    if(Phase==3)
    {
        FVector Direction=Car->DriverEntryPoint->GetComponentLocation()-S->GetActorLocation();Direction.Z=0;
        if(Direction.Size2D()>80)S->AddMovementInput(Direction.GetSafeNormal(),.6f,true);
        if(Now<Next)return;
        Walked=FVector::Dist2D(Before,S->GetActorLocation());DogWalked=FVector::Dist2D(DogBefore,Dog->GetActorLocation());
        if(Walked<50||DogWalked<20){Finish(TEXT("Actual character movement or shepherd following failed"));return;}
        Checks.Add(TEXT("real_player_walk_and_shepherd_follow"));
        FString Error;if(!Car->SurvivalSystems->Execute(S,EAnomaliaVehicleServiceAction::TakeInitialKey,0,0,Error))
        {Finish(TEXT("Cannot collect real E39 initial key: ")+Error);return;}
        if(!Car->EnterVehicle(PC,S)||!Car->SetEngineRunningOnServer(PC,true))
        {Finish(TEXT("Native E39 entry or engine start failed"));return;}
        PC->SetControlRotation(Car->GetActorRotation()+FRotator(-12,0,0));
        Phase=30;Next=Now+3;return;
    }
    if(Phase==30)
    {
        if(Now<Next)return;
        if(!Car->FollowCamera->IsActive()||Car->InteriorCamera->IsActive()||Car->CameraBoom->GetRelativeLocation().Z<100)
        {Finish(TEXT("Exterior driver camera is not above the chassis"));return;}
        Screenshot(TEXT("-driver-exterior.png"));Phase=31;Next=Now+2;return;
    }
    if(Phase==31)
    {
        if(Now<Next)return;Input(EKeys::V,IE_Pressed);Input(EKeys::V,IE_Released);
        PC->SetControlRotation(Car->GetActorRotation());Phase=32;Next=Now+3;return;
    }
    if(Phase==32)
    {
        if(Now<Next)return;
        if(!Car->InteriorCamera->IsActive()||Car->FollowCamera->IsActive())
        {Finish(TEXT("Real V camera input did not activate the cockpit camera"));return;}
        Screenshot(TEXT("-driver-cockpit.png"));Checks.Add(TEXT("exterior_and_cockpit_cameras_switched_by_real_V_input"));
        Phase=33;Next=Now+2;return;
    }
    if(Phase==33)
    {
        if(Now<Next)return;Input(EKeys::V,IE_Pressed);Input(EKeys::V,IE_Released);
        Before=Car->GetActorLocation();Phase=4;Next=Now+4;return;
    }
    if(Phase==4)
    {
        Car->SetDriverControlsOnServer(PC,.35f,0,0);if(Now<Next)return;
        Driven=FVector::Dist2D(Before,Car->GetActorLocation());
        if(Driven<50){Finish(TEXT("E39 did not physically move under real driver controls"));return;}
        Checks.Add(TEXT("real_e39_entry_engine_and_physical_driving"));Phase=5;Next=Now+5;return;
    }
    if(Phase==5)
    {
        Car->SetDriverControlsOnServer(PC,0,0,1);if(Now<Next)return;
        if(!bHoodOpened)
        {
            Car->SetEngineRunningOnServer(PC,false);
            for(const auto& Reference:Car->AdditionalPanels)if(auto* Panel=Reference.Get();Panel&&Panel->PanelId==TEXT("hood"))
            {if(!Panel->TryToggleFromDriver(PC)){Finish(TEXT("Driver-owned bonnet mechanism rejected"));return;}bHoodOpened=true;}
            if(!bHoodOpened){Finish(TEXT("Real bonnet component missing"));return;}
        }
        if(!Car->ExitDriverOnServer(PC)){if(Now<Next+10)return;Finish(TEXT("E39 safe exit failed after braking"));return;}
        if(PC->GetPawn()!=S){Finish(TEXT("E39 exit did not restore the real character"));return;}
        Checks.Add(TEXT("real_e39_braking_and_safe_exit"));Screenshot(TEXT("-gameplay.png"));Phase=6;Next=Now+2;return;
    }
    if(Phase==6)
    {
        if(Now<Next)return;
        bool Open=false;for(const auto& Reference:Car->AdditionalPanels)if(auto* Panel=Reference.Get();Panel&&Panel->PanelId==TEXT("hood"))Open=FMath::Abs(Panel->AngleDegrees)>50.f&&!Panel->bObstructed;
        if(!Open){Finish(TEXT("Bonnet did not physically open far enough to expose the engine"));return;}
        const FTransform T=Car->GetActorTransform();
        View(T.TransformPosition(FVector(345,-220,230)),T.TransformPosition(FVector(150,0,70)),62.f);
        Phase=7;Next=Now+4;return;
    }
    if(Phase==7)
    {
        if(Now<Next)return;Screenshot(TEXT("-engine-bay.png"));Checks.Add(TEXT("actual_engine_mesh_and_animated_open_bonnet"));Phase=8;Next=Now+2;return;
    }
    if(Phase==8)
    {
        if(Now<Next)return;
        const FVector P=Car->GetActorLocation();View(P+FVector(-550,-450,170),P+FVector(1600,600,300),76.f);
        Phase=9;Next=Now+4;return;
    }
    if(Phase==9)
    {
        if(Now<Next)return;Screenshot(TEXT("-street-ground-floors.png"));Phase=10;Next=Now+2;return;
    }
    if(Phase==10)
    {
        if(Now<Next)return;
        const FVector P=Car->GetActorLocation();View(P+FVector(700,600,180),P+FVector(-1700,-500,400),76.f);
        Phase=11;Next=Now+4;return;
    }
    if(Phase==11)
    {
        if(Now<Next)return;Screenshot(TEXT("-street-reverse.png"));Phase=12;Next=Now+2;return;
    }
    if(Phase==12&&Now>=Next)Finish();
#endif
}
