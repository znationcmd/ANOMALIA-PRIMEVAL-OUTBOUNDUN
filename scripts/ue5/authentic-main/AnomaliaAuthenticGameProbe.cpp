#include "AnomaliaAuthenticGameProbe.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaDogCompanion.h"
#include "AnomaliaSessionWidget.h"
#include "Vehicles/AnomaliaChaosRoadVehicle.h"
#include "Vehicles/AnomaliaVehicleSurvival.h"
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
    FString Json;FJsonSerializer::Serialize(R.ToSharedRef(),TJsonWriterFactory<>::Create(&Json));
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
        if(!Car->RoadBodyMesh||!Car->RoadBodyMesh->GetPathName().StartsWith(TEXT("/Game/Anomalia/BMWE39Review_v7/"))||!Car->HasValidRoadRig()||!Car->IsChaosDriveReady())
        {Finish(TEXT("The genuine E39 v7 is not configured as a physical driveable vehicle"));return;}
        if(!Dog->GetMesh()->GetSkeletalMeshAsset()||!Dog->GetMesh()->GetSkeletalMeshAsset()->GetPathName().StartsWith(TEXT("/Game/German_Shepherd_3D_Model/")))
        {Finish(TEXT("The actual German shepherd mesh is not loaded"));return;}
        Checks.Add(TEXT("real_skarvik_with_citysample_geometry"));Checks.Add(TEXT("owned_survival_character_with_locomotion"));Checks.Add(TEXT("genuine_e39_v7_native_physics_rig"));Checks.Add(TEXT("owned_german_shepherd_assigned_to_player"));
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
        if(!Car->ExitDriverOnServer(PC)){if(Now<Next+10)return;Finish(TEXT("E39 safe exit failed after braking"));return;}
        if(PC->GetPawn()!=S){Finish(TEXT("E39 exit did not restore the real character"));return;}
        Checks.Add(TEXT("real_e39_braking_and_safe_exit"));Screenshot(TEXT("-gameplay.png"));Phase=6;Next=Now+2;return;
    }
    if(Phase==6&&Now>=Next)Finish();
#endif
}
