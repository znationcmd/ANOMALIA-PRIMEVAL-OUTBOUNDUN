#include "AnomaliaPlayableProbe.h"
#include "AnomaliaItemEffectsComponent.h"
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
#include "Components/WidgetSwitcher.h"
#include "Components/Image.h"
#include "Components/Border.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerInput.h"
#include "Components/StaticMeshComponent.h"
#include "Components/LightComponentBase.h"
#include "Materials/MaterialInterface.h"
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

AAnomaliaPlayableProbe::AAnomaliaPlayableProbe() { PrimaryActorTick.bCanEverTick=true; PrimaryActorTick.bTickEvenWhenPaused=true; }
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
    if(Now-Started>90)
    {
        const auto* WaitingSurvivor=Survivor.Get(); const auto* WaitingLoot=GetWorld()->GetSubsystem<UAnomaliaLootSubsystem>();
        Finish(FString::Printf(TEXT("Timed out phase %d (character=%s HUD=%d lootReady=%d)"),Phase,*GetNameSafe(WaitingSurvivor),WaitingSurvivor && WaitingSurvivor->StatusWidget?1:0,WaitingLoot && WaitingLoot->IsReady()?1:0)); return;
    }
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
            if(!S->ItemEffectsComponent || S->ItemEffectsComponent->State.Dependence<1)
            { Finish(TEXT("Saved item effects were not restored"));return; }
            Checks.Add(TEXT("restarted_executable_restored_item_effects"));
            Checks.Add(TEXT("restarted_executable_restored_inventory_and_character_position")); Finish(); return;
        }
        for(const FName Id:{FName(TEXT("health")),FName(TEXT("hunger")),FName(TEXT("thirst")),FName(TEXT("fatigue")),FName(TEXT("temperature")),FName(TEXT("stamina")),FName(TEXT("blood"))})
            if(S->StatusWidget->GetVitalText(Id).IsEmpty()) { Finish(TEXT("Missing native HUD field")); return; }
        int32 VisualActors=0,DynamicLights=0; bool Meadow=false;
        for(TActorIterator<AActor> It(GetWorld());It;++It)
        {
            if(It->ActorHasTag(TEXT("PlayableLook_v2"))) ++VisualActors;
            if(It->ActorHasTag(TEXT("PlayableGround")))
            {
                auto* Mesh=It->FindComponentByClass<UStaticMeshComponent>();
                auto* Material=Mesh?Mesh->GetMaterial(0):nullptr;
                Meadow=Material && Material->GetPathName().Contains(TEXT("/PlayableLook_v2/M_Meadow"));
            }
            if(It->ActorHasTag(TEXT("PlayableSun")) || It->ActorHasTag(TEXT("PlayableSky")))
                if(auto* Light=It->FindComponentByClass<ULightComponentBase>())
                    if(Light->GetMobility()==EComponentMobility::Movable) ++DynamicLights;
        }
        if(!Meadow || DynamicLights!=2 || VisualActors<120)
        { Finish(FString::Printf(TEXT("Cooked visual update missing: meadow=%d dynamicLights=%d decorations=%d"),Meadow,DynamicLights,VisualActors)); return; }
        Checks.Add(TEXT("native_playable_look_v2_cooked_materials_and_lights"));
        if(FParse::Param(FCommandLine::Get(),TEXT("AnomaliaProgressArt")))
        {
            int32 Houses=0,Trees=0,HiddenCrowns=0;
            for(TActorIterator<AActor> It(GetWorld());It;++It)
            {
                if(!It->ActorHasTag(TEXT("ANOMALIA_ProgressArt_v1")))continue;
                auto* Component=It->FindComponentByClass<UStaticMeshComponent>();
                if(It->ActorHasTag(TEXT("ANOMALIA_ProgressHiddenCrown_v1")))
                {
                    if(!Component || Component->IsVisible()) { Finish(TEXT("Provisional spherical canopy is still visible")); return; }
                    ++HiddenCrowns; continue;
                }
                const FString Path=Component && Component->GetStaticMesh()?Component->GetStaticMesh()->GetPathName():FString();
                if(It->ActorHasTag(TEXT("ANOMALIA_ProgressTree_v1")))
                {if(Path.StartsWith(TEXT("/Game/Anomalia/VerifiedProps_v1/"))||Path.Contains(TEXT("/island_tree_02/")))++Trees;}
                else if(Path.StartsWith(TEXT("/Game/Anomalia/ResidentialPhotogrammetryReview_v1/")))++Houses;
            }
            if(Houses!=2||Trees!=20||HiddenCrowns!=60){Finish(TEXT("New cooked art missing or provisional crowns still present"));return;}
            Checks.Add(TEXT("validated_progress_houses_and_twenty_real_trees"));
        }
        for(TActorIterator<AAnomaliaVehiclePawn> It(GetWorld());It;++It)
            if(It->ActorHasTag(TEXT("ANOMALIA_Playable_v1_Owner")))
            { if(!It->Body->GetStaticMesh()) { Finish(TEXT("Vehicle art is missing from cooked game")); return; } Vehicles.Add(*It); }
        if(Vehicles.Num()!=3) { Finish(TEXT("Expected three cooked vehicles")); return; }
        auto* Menu=UAnomaliaSessionWidget::Open(PC,true);
        auto* Play=Menu && Menu->WidgetTree?Cast<UButton>(Menu->WidgetTree->FindWidget(TEXT("SessionPlay"))):nullptr;
        if(!Play || !GetWorld()->IsPaused()) { Finish(TEXT("Actual main menu did not pause the game")); return; }
        auto* Art=Cast<UImage>(Menu->WidgetTree->FindWidget(TEXT("SessionMenuArtwork")));
        if(!Art || !Art->GetBrush().GetResourceObject() || !Art->GetBrush().GetResourceObject()->GetPathName().Contains(TEXT("/Branding/T_MenuBackdrop")))
        { Finish(TEXT("User-provided main menu artwork is missing from the cooked game")); return; }
        Next=Now+1;Phase=19;return;
    }
    if(Phase==19)
    {
        if(Now<Next)return;
        auto* Menu=UAnomaliaSessionWidget::Open(PC,true);
        auto* Art=Menu && Menu->WidgetTree?Cast<UImage>(Menu->WidgetTree->FindWidget(TEXT("SessionMenuArtwork"))):nullptr;
        if(!Art || Art->GetRenderOpacity()<=0.f) { Finish(TEXT("Startup artwork animation did not advance while paused"));return; }
        FString IntroReport;FParse::Value(FCommandLine::Get(),TEXT("AnomaliaPlayableProbe="),IntroReport);
        FScreenshotRequest::RequestScreenshot(FPaths::ChangeExtension(IntroReport,TEXT(""))+TEXT("-intro.png"),true,false);
        Next=Now+5;Phase=20;return;
    }
    if(Phase==20)
    {
        if(Now<Next)return;
        auto* Menu=UAnomaliaSessionWidget::Open(PC,true);
        auto* Play=Menu && Menu->WidgetTree?Cast<UButton>(Menu->WidgetTree->FindWidget(TEXT("SessionPlay"))):nullptr;
        auto* Rail=Menu && Menu->WidgetTree?Cast<UBorder>(Menu->WidgetTree->FindWidget(TEXT("SessionNavigation"))):nullptr;
        if(!Play || !Rail || Rail->GetVisibility()!=ESlateVisibility::Visible)
        { Finish(TEXT("Startup animation did not reveal the main menu"));return; }
        Checks.Add(TEXT("user_branding_intro_animates_and_reveals_main_menu"));
        auto* Pages=Cast<UWidgetSwitcher>(Menu->WidgetTree->FindWidget(TEXT("SessionPages")));
        auto* Mods=Cast<UButton>(Menu->WidgetTree->FindWidget(TEXT("SessionMods")));
        auto* Options=Cast<UButton>(Menu->WidgetTree->FindWidget(TEXT("SessionOptions")));
        auto* Home=Cast<UButton>(Menu->WidgetTree->FindWidget(TEXT("SessionHome")));
        auto* Refresh=Cast<UButton>(Menu->WidgetTree->FindWidget(TEXT("SessionRefreshMods")));
        auto* WorldEditor=Cast<UButton>(Menu->WidgetTree->FindWidget(TEXT("SessionWorldEditor")));
        if(!Pages || !Mods || !Options || !Home || !Refresh || !WorldEditor || Pages->GetActiveWidgetIndex()!=0)
        { Finish(TEXT("Main menu navigation or local mods page missing")); return; }
        Mods->OnClicked.Broadcast(); Refresh->OnClicked.Broadcast();
        const auto* Workshop=Cast<UBorder>(Menu->WidgetTree->FindWidget(TEXT("WorkshopFullScreen")));
        const auto* WorkshopCards=Cast<UVerticalBox>(Menu->WidgetTree->FindWidget(TEXT("WorkshopCards")));
        auto* WorkshopReturn=Cast<UButton>(Menu->WidgetTree->FindWidget(TEXT("WorkshopReturn")));
        auto* WorkshopCategory=Menu->WidgetTree->FindWidget(TEXT("WorkshopCategory"));
        auto* WorkshopSearch=Menu->WidgetTree->FindWidget(TEXT("WorkshopSearch"));
        auto* WorkshopTools=Cast<UButton>(Menu->WidgetTree->FindWidget(TEXT("WorkshopOpenTools")));
        auto* WorkshopHosting=Cast<UButton>(Menu->WidgetTree->FindWidget(TEXT("WorkshopOpenHosting")));
        if(Pages->GetActiveWidgetIndex()!=2 || !GetWorld()->IsPaused() ||
            !Workshop || Workshop->GetVisibility()!=ESlateVisibility::Visible || !WorkshopCards ||
            WorkshopCards->GetChildrenCount()==0 || !WorkshopReturn || !WorkshopSearch ||
            !WorkshopCategory || !WorkshopTools || !WorkshopHosting)
        { Finish(TEXT("Native in-game Workshop missing or not visible when Mods is clicked"));return; }
        Checks.Add(TEXT("real_unreal_workshop_opened_inside_game_with_search_categories_and_cards"));
        FString WorkshopReport;FParse::Value(FCommandLine::Get(),TEXT("AnomaliaPlayableProbe="),WorkshopReport);
        FScreenshotRequest::RequestScreenshot(FPaths::ChangeExtension(WorkshopReport,TEXT(""))+TEXT("-workshop.png"),true,false);
        WorkshopReturn->OnClicked.Broadcast();
        if(Workshop->GetVisibility()!=ESlateVisibility::Collapsed)
        { Finish(TEXT("Native Workshop return button failed to close"));return; }
        Mods->OnClicked.Broadcast();
        if(Workshop->GetVisibility()!=ESlateVisibility::Visible)
        { Finish(TEXT("Native Workshop did not reopen"));return; }
        Options->OnClicked.Broadcast();
        if(Pages->GetActiveWidgetIndex()!=1) { Finish(TEXT("Options navigation failed")); return; }
        Home->OnClicked.Broadcast();
        if(Pages->GetActiveWidgetIndex()!=0) { Finish(TEXT("Return from mods/options failed")); return; }
        auto* Close=Cast<UButton>(Menu->WidgetTree->FindWidget(TEXT("SessionClosePage")));
        if(!Close) { Finish(TEXT("Return-to-menu control missing"));return; }
        Close->OnClicked.Broadcast();
        Checks.Add(TEXT("main_menu_mods_refresh_options_and_return"));
        FString MenuReport; FParse::Value(FCommandLine::Get(),TEXT("AnomaliaPlayableProbe="),MenuReport);
        FScreenshotRequest::RequestScreenshot(FPaths::ChangeExtension(MenuReport,TEXT(""))+TEXT("-menu.png"),true,false);
        Next=Now+2; Phase=18; return;
    }
    auto* S=Survivor.Get(); if(!S) { Finish(TEXT("Character destroyed")); return; }
    if(Phase==18)
    {
        if(Now<Next) return;
        auto* Menu=UAnomaliaSessionWidget::Open(PC,true);
        auto* Play=Menu && Menu->WidgetTree?Cast<UButton>(Menu->WidgetTree->FindWidget(TEXT("SessionPlay"))):nullptr;
        if(!Play) { Finish(TEXT("Main menu vanished before play")); return; }
        Play->OnClicked.Broadcast();
        if(Menu->IsInViewport() || GetWorld()->IsPaused() || PC->GetViewTarget()!=PC->GetPawn()) { Finish(TEXT("Play button did not restore gameplay and its camera")); return; }
        Checks.Add(TEXT("main_menu_play_button"));
        Checks.Add(TEXT("native_world_HUD_and_three_vehicle_meshes"));
        Before=S->GetActorLocation(); PC->SetControlRotation(FRotator::ZeroRotator);
        Input(EKeys::W,IE_Pressed); Next=Now+1; Phase=1; return;
    }
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
        Checks.Add(TEXT("world_pickup_into_native_inventory"));
        AAnomaliaLootPickup* Drink=nullptr;
        for(TActorIterator<AAnomaliaLootPickup> It(GetWorld());It;++It) if(It->SpawnId==TEXT("playable-supplies-1")) Drink=*It;
        if(!Drink) { Finish(TEXT("Second world pickup missing"));return; }
        S->SetActorLocation(Drink->GetActorLocation()+FVector(0,-100,100),false,nullptr,ETeleportType::TeleportPhysics);
        Input(EKeys::E,IE_Pressed);Next=Now+.5;Phase=11;return;
    }
    if(Phase==11)
    {
        Input(EKeys::E,IE_Released);if(Now<Next)return;
        if(S->InventoryComponent->Stacks.Num()<2) { Finish(TEXT("Second pickup did not enter inventory"));return; }
        Input(EKeys::I,IE_Pressed);Next=Now+.5;Phase=4;return;
    }
    if(Phase==4)
    {
        Input(EKeys::I,IE_Released); if(Now<Next) return;
        if(!S->InventoryWidget || !S->InventoryWidget->IsInViewport()) { Finish(TEXT("Cooked inventory UI failed")); return; }
        const auto* Food=S->InventoryComponent->Stacks.FindByPredicate([&](const auto& Stack){return S->InventoryComponent->GetUseActionLabel(Stack.ItemId)==TEXT("Manger");});
        if(!Food) { Finish(TEXT("Collected food has no native use rule"));return; }
        UsedStackId=Food->StackId;UsedCount=Food->Count;
        S->RestoreSurvival(20.f,20.f,70.f);
        TArray<UWidget*> Widgets;S->InventoryWidget->WidgetTree->GetAllWidgets(Widgets);
        UButton* Eat=nullptr;
        const FString Prefix=FString::Printf(TEXT("UseStack_%d_action"),UsedStackId);
        for(auto* Widget:Widgets)
            if(auto* Button=Cast<UButton>(Widget)) if(Button->GetName().StartsWith(Prefix)) Eat=Button;
        if(!Eat) { Finish(TEXT("Actual inventory food-use button missing"));return; }
        Eat->OnClicked.Broadcast();Next=Now+.4;Phase=12;return;
    }
    if(Phase==12)
    {
        if(Now<Next)return;
        const auto* Remaining=S->InventoryComponent->Stacks.FindByPredicate([&](const auto& Stack){return Stack.StackId==UsedStackId;});
        if((Remaining?Remaining->Count:0)!=UsedCount-1 || S->Hunger<=20.1f || S->InventoryComponent->Stacks.IsEmpty())
        { Finish(TEXT("Native inventory food use failed to consume exactly one unit and restore hunger"));return; }
        Checks.Add(TEXT("native_inventory_food_use_consumes_one_and_restores_hunger"));
        if(!S->InventoryComponent->TryAddItem(TEXT("cigarette"),1) || !S->InventoryComponent->TryAddItem(TEXT("lighter"),1))
        { Finish(TEXT("Isolated tobacco test supplies unavailable"));return; }
        const auto* Cigarette=S->InventoryComponent->Stacks.FindByPredicate([](const auto& Stack){return Stack.ItemId==TEXT("cigarette");});
        if(!Cigarette) { Finish(TEXT("Isolated cigarette missing"));return; }
        UsedStackId=Cigarette->StackId;
        TArray<UWidget*> Widgets;S->InventoryWidget->WidgetTree->GetAllWidgets(Widgets);UButton* Smoke=nullptr;
        const FString Prefix=FString::Printf(TEXT("UseStack_%d_action"),UsedStackId);
        for(auto* Widget:Widgets) if(auto* Button=Cast<UButton>(Widget)) if(Button->GetName().StartsWith(Prefix)) Smoke=Button;
        if(!Smoke) { Finish(TEXT("Actual cigarette inventory button missing"));return; }
        Smoke->OnClicked.Broadcast();Next=Now+.4;Phase=13;return;
    }
    if(Phase==13)
    {
        if(Now<Next)return;
        const auto* Effects=S->ItemEffectsComponent.Get();
        if(!Effects || Effects->State.Intoxication<4 || Effects->State.Dependence<7 ||
            S->InventoryComponent->Stacks.ContainsByPredicate([&](const auto& Stack){return Stack.StackId==UsedStackId;}) ||
            !S->InventoryComponent->Stacks.ContainsByPredicate([](const auto& Stack){return Stack.ItemId==TEXT("cigarette_butt");}))
        { Finish(TEXT("Actual cigarette UI use did not consume source, apply risks and retain waste"));return; }
        Checks.Add(TEXT("native_inventory_tobacco_use_has_risk_and_returns_waste"));
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
