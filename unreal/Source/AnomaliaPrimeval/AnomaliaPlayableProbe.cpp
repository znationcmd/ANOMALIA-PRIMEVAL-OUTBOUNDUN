#include "AnomaliaPlayableProbe.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaVehiclePawn.h"
#include "AnomaliaStatusWidget.h"
#include "AnomaliaInventoryWidget.h"
#include "AnomaliaInventoryComponent.h"
#include "AnomaliaLootPickup.h"
#include "AnomaliaLootSubsystem.h"
#include "AnomaliaGameMode.h"
#include "AnomaliaSessionWidget.h"
#include "AnomaliaConfigLibrary.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Button.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerInput.h"
#include "Components/StaticMeshComponent.h"
#include "Camera/CameraComponent.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "HighResScreenshot.h"
#include "UnrealClient.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

AAnomaliaPlayableProbe::AAnomaliaPlayableProbe() { PrimaryActorTick.bCanEverTick=true; }
void AAnomaliaPlayableProbe::Finish(const FString& Error)
{
    FString File; FParse::Value(FCommandLine::Get(),TEXT("AnomaliaPlayableProbe="),File);
    TSharedPtr<FJsonObject> Report=MakeShared<FJsonObject>(); Report->SetStringField(TEXT("state"),Error.IsEmpty()?TEXT("PACKAGED_GAME_SMOKE_PASSED"):TEXT("FAILED"));
    Report->SetStringField(TEXT("error"),Error); Report->SetStringField(TEXT("savedDir"),FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()));
    Report->SetStringField(TEXT("map"),GetWorld()->GetMapName());
    TArray<TSharedPtr<FJsonValue>> Rows; for(const auto& Check:Checks) Rows.Add(MakeShared<FJsonValueString>(Check));
    Report->SetArrayField(TEXT("checks"),Rows); FString Json;
    FJsonSerializer::Serialize(Report.ToSharedRef(),TJsonWriterFactory<>::Create(&Json));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(File),true);
    FFileHelper::SaveStringToFile(Json,*File);
    SetActorTickEnabled(false);
    FGenericPlatformMisc::RequestExit(false);
}
void AAnomaliaPlayableProbe::Tick(float Dt)
{
    Super::Tick(Dt);
#if !UE_BUILD_SHIPPING
    const double Now=FPlatformTime::Seconds(); if(Started==0) { Started=Now; Next=Now+3; }
    if(Now-Started>90) { Finish(FString::Printf(TEXT("Timed out phase %d"),Phase)); return; }
    auto* PC=GetWorld()->GetFirstPlayerController(); if(!PC) return;
    auto Input=[PC](FKey Key,EInputEvent Event) { PC->InputKey(FInputKeyParams(Key,Event,Event==IE_Pressed?1.0:0.0,Key.IsGamepadKey(),FInputDeviceId::CreateFromInternalId(0))); };
    if(Phase==0)
    {
        if(Now<Next) return;
        Survivor=Cast<AAnomaliaSurvivor>(PC->GetPawn());
        auto* S=Survivor.Get(); auto* Loot=GetWorld()->GetSubsystem<UAnomaliaLootSubsystem>();
        if(!S || !S->StatusWidget || !Loot || !Loot->IsReady()) return;
        if(FParse::Param(FCommandLine::Get(),TEXT("AnomaliaPlayableResume")))
        {
            if(S->InventoryComponent->Stacks.IsEmpty() || FVector::Dist2D(S->GetActorLocation(),FVector(0,-400,0))<300)
            { Finish(TEXT("Saved inventory or map-scoped character position was not restored")); return; }
            Checks.Add(TEXT("restarted_executable_restored_inventory_and_character_position")); Finish(); return;
        }
        for(const FName Id:{FName(TEXT("health")),FName(TEXT("hunger")),FName(TEXT("thirst")),FName(TEXT("fatigue")),FName(TEXT("temperature")),FName(TEXT("stamina"))})
            if(S->StatusWidget->GetVitalText(Id).IsEmpty()) { Finish(TEXT("Missing native HUD field")); return; }
        for(TActorIterator<AAnomaliaVehiclePawn> It(GetWorld());It;++It)
            if(It->ActorHasTag(TEXT("ANOMALIA_Playable_v1_Owner")))
            { if(!It->Body->GetStaticMesh()) { Finish(TEXT("Vehicle art is missing from cooked game")); return; } Vehicles.Add(*It); }
        if(Vehicles.Num()!=3) { Finish(TEXT("Expected three cooked vehicles")); return; }
        auto* Menu=UAnomaliaSessionWidget::Open(PC,true);
        auto* Play=Menu && Menu->WidgetTree?Cast<UButton>(Menu->WidgetTree->FindWidget(TEXT("SessionPlay"))):nullptr;
        if(!Play || !GetWorld()->IsPaused()) { Finish(TEXT("Actual main menu did not pause the game")); return; }
        Play->OnClicked.Broadcast();
        if(Menu->IsInViewport() || GetWorld()->IsPaused()) { Finish(TEXT("Play button did not enter gameplay")); return; }
        Checks.Add(TEXT("main_menu_play_button"));
        Checks.Add(TEXT("native_world_HUD_and_three_vehicle_meshes"));
        Before=S->GetActorLocation(); PC->SetControlRotation(FRotator::ZeroRotator);
        Input(EKeys::W,IE_Pressed); Next=Now+1; Phase=1; return;
    }
    auto* S=Survivor.Get(); if(!S) { Finish(TEXT("Character destroyed")); return; }
    if(Phase==1)
    {
        if(Now<Next) return; Input(EKeys::W,IE_Released);
        if(FVector::Dist2D(Before,S->GetActorLocation())<100) { Finish(TEXT("Real keyboard movement failed")); return; }
        Checks.Add(TEXT("keyboard_character_movement"));
        AActor* Building=nullptr; for(TActorIterator<AActor> It(GetWorld());It;++It) if(It->ActorHasTag(TEXT("PlayableHouse"))) Building=*It;
        if(!Building) { Finish(TEXT("House missing")); return; } House=Building->GetActorLocation();
        FCollisionQueryParams Query; Query.AddIgnoredActor(S); FHitResult Hit;
        if(GetWorld()->LineTraceSingleByChannel(Hit,House+FVector(0,650,100),House+FVector(0,0,100),ECC_Visibility,Query)) DoorSign=-1;
        if(GetWorld()->LineTraceSingleByChannel(Hit,House+FVector(0,DoorSign*650,100),House+FVector(0,0,100),ECC_Visibility,Query))
        { Finish(TEXT("House doorway is blocked in cooked collision")); return; }
        S->SetActorLocation(House+FVector(0,DoorSign*650,110),false,nullptr,ETeleportType::TeleportPhysics);
        PC->SetControlRotation(FRotator(0,-DoorSign*90,0)); Input(EKeys::W,IE_Pressed); Next=Now+1.5; Phase=2; return;
    }
    if(Phase==2)
    {
        if(Now<Next) return; Input(EKeys::W,IE_Released);
        if(FVector::Dist2D(House,S->GetActorLocation())>360) { Finish(TEXT("Character could not enter house through doorway")); return; }
        Checks.Add(TEXT("walk_through_house_doorway"));
        AAnomaliaLootPickup* Item=nullptr; for(TActorIterator<AAnomaliaLootPickup> It(GetWorld());It;++It) if(It->SpawnId==TEXT("playable-supplies-0")) Item=*It;
        if(!Item) { Finish(TEXT("Cooked catalogue pickup is missing")); return; }
        S->SetActorLocation(Item->GetActorLocation()+FVector(0,-100,100),false,nullptr,ETeleportType::TeleportPhysics);
        Input(EKeys::E,IE_Pressed); Next=Now+.5; Phase=3; return;
    }
    if(Phase==3)
    {
        Input(EKeys::E,IE_Released); if(Now<Next) return;
        if(S->InventoryComponent->Stacks.IsEmpty()) { Finish(TEXT("Cooked Interact pickup failed")); return; }
        Checks.Add(TEXT("world_pickup_into_native_inventory")); Input(EKeys::I,IE_Pressed); Next=Now+.5; Phase=4; return;
    }
    if(Phase==4)
    {
        Input(EKeys::I,IE_Released); if(Now<Next) return;
        if(!S->InventoryWidget || !S->InventoryWidget->IsInViewport()) { Finish(TEXT("Cooked inventory UI failed")); return; }
        S->CloseInventory(); Checks.Add(TEXT("native_inventory_open_close"));
        auto* Mode=GetWorld()->GetAuthGameMode<AAnomaliaGameMode>(); FString Saved,Error;
        if(!Mode || !Mode->SaveLocalGame() || !UAnomaliaConfigLibrary::LoadPlayerProfile(Mode->ServerId,TEXT("local-owner"),Saved,Error))
        { Finish(TEXT("Explicit local profile save failed")); return; }
        Checks.Add(TEXT("explicit_local_profile_save")); Phase=5;
    }
    if(Phase==5)
    {
        if(VehicleIndex>=Vehicles.Num())
        {
            Checks.Add(TEXT("three_vehicle_enter_accelerate_steer_exit"));
            FString File; FParse::Value(FCommandLine::Get(),TEXT("AnomaliaPlayableProbe="),File);
            FScreenshotRequest::RequestScreenshot(FPaths::ChangeExtension(File,TEXT("png")),true,false); Next=Now+3; Phase=8; return;
        }
        auto* V=Vehicles[VehicleIndex].Get(); if(!V) { Finish(TEXT("Vehicle destroyed")); return; }
        S->SetActorLocation(V->GetActorLocation()+FVector(0,300,100),false,nullptr,ETeleportType::TeleportPhysics);
        Input(EKeys::E,IE_Pressed); Next=Now+.4; Phase=6; return;
    }
    if(Phase==6)
    {
        Input(EKeys::E,IE_Released); if(Now<Next) return;
        auto* V=Vehicles[VehicleIndex].Get(); if(PC->GetPawn()!=V) { Finish(FString::Printf(TEXT("Vehicle possession failed: index=%d id=%s controller=%s occupied=%d distance=%.1f pawn=%s"),VehicleIndex,*V->VehicleId.ToString(),*GetNameSafe(V->GetController()),V->HasDriver(),FVector::Dist(S->GetActorLocation(),V->GetActorLocation()),*GetNameSafe(PC->GetPawn()))); return; }
        Before=V->GetActorLocation(); Input(EKeys::W,IE_Pressed); Input(EKeys::D,IE_Pressed); Next=Now+.7; Phase=7; return;
    }
    if(Phase==7)
    {
        if(Now<Next) return; Input(EKeys::W,IE_Released); Input(EKeys::D,IE_Released);
        auto* V=Vehicles[VehicleIndex].Get(); if(FVector::Dist2D(Before,V->GetActorLocation())<30) { Finish(TEXT("Vehicle did not drive")); return; }
        Input(EKeys::V,IE_Pressed); Input(EKeys::V,IE_Released);
        Next=Now+.3; Phase=9; return;
    }
    if(Phase==9)
    {
        if(Now<Next) return;
        if(!Vehicles[VehicleIndex]->InteriorCamera->IsActive()) { Finish(TEXT("Vehicle interior camera did not activate")); return; }
        Input(EKeys::E,IE_Pressed); Next=Now+.3; Phase=10; return;
    }
    if(Phase==10)
    {
        Input(EKeys::E,IE_Released); if(Now<Next) return;
        if(PC->GetPawn()!=S) { Finish(TEXT("Vehicle exit failed")); return; }
        ++VehicleIndex; Phase=5; return;
    }
    if(Phase==8 && Now>=Next) Finish();
#endif
}
