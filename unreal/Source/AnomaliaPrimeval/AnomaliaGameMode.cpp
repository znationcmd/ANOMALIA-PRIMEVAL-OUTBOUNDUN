#include "AnomaliaGameMode.h"
#include "AnomaliaItemEffectsComponent.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaPlayableProbe.h"
#include "AnomaliaVisualReviewProbe.h"
#include "AnomaliaSessionWidget.h"
#include "AnomaliaLootSubsystem.h"
#include "AnomaliaEconomySubsystem.h"
#include "AnomaliaInventoryComponent.h"
#include "AnomaliaVitalsComponent.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "Misc/SecureHash.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "TimerManager.h"
#include "AnomaliaVehiclePawn.h"
#include "AnomaliaVehicleCatalog.h"
#include "Vehicles/AnomaliaTransportMovement.h"
#include "Vehicles/AnomaliaTransportEnvironment.h"
#include "EngineUtils.h"
#include "AnomaliaHomesteadStation.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Dom/JsonObject.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

AAnomaliaGameMode::AAnomaliaGameMode()
{
    DefaultPawnClass = AAnomaliaSurvivor::StaticClass();
}

void AAnomaliaGameMode::InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage)
{
    Super::InitGame(MapName, Options, ErrorMessage);
    // URL option: ?AnomaliaServerId=rp-corse. Each ID gets an isolated Saved/Servers folder.
    const FString RequestedId = UGameplayStatics::ParseOption(Options, TEXT("AnomaliaServerId"));
    if (!RequestedId.IsEmpty())
    {
        bool bValid = RequestedId.Len() <= 64;
        for (const TCHAR C : RequestedId)
        {
            if (C > 127 || !(FChar::IsAlnum(C) || C == TEXT('-') || C == TEXT('_'))) { bValid = false; break; }
        }
        if (bValid) ServerId = RequestedId;
        else UE_LOG(LogTemp, Warning, TEXT("ANOMALIA: invalid server ID rejected"));
    }
    if (RequestedId.IsEmpty() && GetNetMode() == NM_Standalone)
        ServerId = MapName.EndsWith(TEXT("ANOMALIA_Playable_v1")) ? TEXT("solo-playable-v1") : TEXT("solo-local");
#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR
    // A process-only test scope prevents automated PIE from touching a real local profile.
    // This is not a client URL option and is restricted to this review map while automation runs.
    FString AutomationScope;
    if (GIsAutomationTesting && GetNetMode() == NM_Standalone && MapName.EndsWith(TEXT("ANOMALIA_LootReview_v1")) &&
        FParse::Value(FCommandLine::Get(), TEXT("AnomaliaAutomationServerId="), AutomationScope))
    {
        bool Valid = !AutomationScope.IsEmpty() && AutomationScope.Len() <= 64;
        for (TCHAR C : AutomationScope)
            if (C > 127 || !(FChar::IsAlnum(C) || C == '-' || C == '_')) Valid = false;
        if (Valid) ServerId = AutomationScope;
    }
#endif
    FString EconomyError;
    if (auto* Economy = GetWorld()->GetSubsystem<UAnomaliaEconomySubsystem>())
        if (!Economy->Configure(ServerId, MapName, EconomyError))
            UE_LOG(LogTemp, Error, TEXT("ANOMALIA economy initialization stopped: %s"), *EconomyError);
    FString LootError;
    if (auto* Loot = GetWorld()->GetSubsystem<UAnomaliaLootSubsystem>())
        if (!Loot->Configure(ServerId, MapName, LootError))
            UE_LOG(LogTemp, Error, TEXT("ANOMALIA loot initialization stopped: %s"), *LootError);
    FString ConfigError;
    if (!UAnomaliaConfigLibrary::LoadServerSettings(ServerId, ActiveServerSettings, ConfigError))
    {
        // Default values are safe; never overwrite invalid configuration automatically.
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA server %s: %s"), *ServerId, *ConfigError);
    }
}


FString AAnomaliaGameMode::GetPersistentPlayerId(const AController* Controller) const
{
    if (!Controller) return FString();
    if (GetNetMode() == NM_Standalone && Controller->IsLocalController()) return TEXT("local-owner");
    if (!Controller->PlayerState) return FString();
    const FUniqueNetIdRepl& NetId = Controller->PlayerState->GetUniqueId();
    if (!NetId.IsValid()) return FString();
    const FString RawIdentity = NetId.ToString();
    if (RawIdentity.IsEmpty()) return FString();
    FTCHARToUTF8 EncodedIdentity(*RawIdentity);
    return FSHA1::HashBuffer(EncodedIdentity.Get(), static_cast<uint64>(EncodedIdentity.Length())).ToString().ToLower();
}

void AAnomaliaGameMode::HandleStartingNewPlayer_Implementation(APlayerController* NewPlayer)
{
    Super::HandleStartingNewPlayer_Implementation(NewPlayer);
    if (!HasAuthority() || !NewPlayer) return;
    GetWorldTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(this, [this, NewPlayer]()
    {
        LoadPersistentPlayer(NewPlayer);
    }));
}

void AAnomaliaGameMode::LoadPersistentPlayer(APlayerController* PlayerController)
{
    if (!HasAuthority() || !PlayerController) return;
    AAnomaliaSurvivor* Survivor = Cast<AAnomaliaSurvivor>(PlayerController->GetPawn());
    const FString PlayerId = GetPersistentPlayerId(PlayerController);
    const auto* Loot = GetWorld()->GetSubsystem<UAnomaliaLootSubsystem>();
    const auto* Economy = GetWorld()->GetSubsystem<UAnomaliaEconomySubsystem>();
    if ((Loot && Loot->HasPendingPlayer(PlayerId)) || (Economy && Economy->HasPendingPlayer(PlayerId)))
    {
        PendingProfileLoads.Add(PlayerId);
        if (Survivor && Survivor->InventoryComponent) Survivor->InventoryComponent->SetProfileRecoveryPending(true);
        return;
    }
    if (Survivor && Survivor->InventoryComponent) Survivor->InventoryComponent->SetProfileRecoveryPending(false);
    PendingProfileLoads.Remove(PlayerId);
    if (!Survivor || PlayerId.IsEmpty())
    {
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA: player profile load skipped (pawn or authenticated network identity unavailable)"));
        return;
    }

    FString Raw, Error;
    if (!UAnomaliaConfigLibrary::LoadPlayerProfile(ServerId, PlayerId, Raw, Error))
    {
        if (Error != TEXT("Profile not found"))
            UE_LOG(LogTemp, Warning, TEXT("ANOMALIA %s: profile load rejected: %s"), *ServerId, *Error);
        return;
    }

    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Raw);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid()) return;

    if (Root->HasField(TEXT("inventory")) && Survivor->InventoryComponent)
    {
        FString InventoryError;
        if (!Survivor->InventoryComponent->LoadInventoryFromPlayerProfile(ServerId, PlayerId, InventoryError))
        {
            PendingProfileLoads.Add(PlayerId);
            Survivor->InventoryComponent->SetProfileRecoveryPending(true);
            UE_LOG(LogTemp, Warning, TEXT("ANOMALIA %s: inventory load rejected: %s"), *ServerId, *InventoryError);
            return;
        }
    }

    const TSharedPtr<FJsonObject>* SurvivalPtr = nullptr;
    if (!Root->TryGetObjectField(TEXT("survival"), SurvivalPtr) || !SurvivalPtr || !SurvivalPtr->IsValid()) return;
    const TSharedPtr<FJsonObject>& Survival = *SurvivalPtr;
    double Food = Survivor->Hunger, Water = Survivor->Thirst, HP = Survivor->Health;
    bool bHasValue = false;
    double Value = 0.0;
    if (Survival->TryGetNumberField(TEXT("hunger"), Value) && FMath::IsFinite(Value))
    {
        Food = FMath::Clamp(Value, 0.0, 100.0);
        bHasValue = true;
    }
    if (Survival->TryGetNumberField(TEXT("thirst"), Value) && FMath::IsFinite(Value))
    {
        Water = FMath::Clamp(Value, 0.0, 100.0);
        bHasValue = true;
    }
    if (Survival->TryGetNumberField(TEXT("health"), Value) && FMath::IsFinite(Value))
    {
        HP = FMath::Clamp(Value, 0.0, 100.0);
        bHasValue = true;
    }
    if (bHasValue) Survivor->RestoreSurvival(static_cast<float>(Food), static_cast<float>(Water), static_cast<float>(HP));
    // Older profiles have no fatigue key and safely retain the fresh-character default.
    if (Survival->TryGetNumberField(TEXT("fatigue"), Value) && FMath::IsFinite(Value) &&
        Value >= 0.0 && Value <= 100.0)
        Survivor->RestoreFatigue(static_cast<float>(Value));

    // Optional fields: legacy profiles without vitals remain valid and unchanged.
    if (Survivor->VitalsComponent)
    {
        double SavedStamina = Survivor->VitalsComponent->Stamina;
        double SavedTemperature = Survivor->VitalsComponent->BodyTemperatureC;
        bool bValidVitals = false;
        if (Survival->TryGetNumberField(TEXT("stamina"), Value) && FMath::IsFinite(Value) &&
            Value >= 0.0 && Value <= 100.0)
        {
            SavedStamina = Value;
            bValidVitals = true;
        }
        if (Survival->TryGetNumberField(TEXT("bodyTemperatureC"), Value) && FMath::IsFinite(Value) &&
            Value >= 25.0 && Value <= 45.0)
        {
            SavedTemperature = Value;
            bValidVitals = true;
        }
        if (bValidVitals)
            Survivor->VitalsComponent->RestoreVitals(static_cast<float>(SavedStamina), static_cast<float>(SavedTemperature));
    }
    if(Survivor->ItemEffectsComponent)
    {
        FAnomaliaItemEffectsState Effects;FString EffectsError;
        if(UAnomaliaItemEffectsComponent::ReadState(Survival,Effects,EffectsError)) Survivor->ItemEffectsComponent->ApplyState(Effects);
        else UE_LOG(LogTemp,Warning,TEXT("ANOMALIA effects were not restored: %s"),*EffectsError);
    }
    const TSharedPtr<FJsonObject>* Pose=nullptr;
    if(Root->TryGetObjectField(TEXT("pose"),Pose) && Pose && Pose->IsValid())
    {
        FString Map; double X=0,Y=0,Z=0,Yaw=0;
        if((*Pose)->TryGetStringField(TEXT("map"),Map) && Map==GetWorld()->GetMapName() &&
            (*Pose)->TryGetNumberField(TEXT("x"),X) && (*Pose)->TryGetNumberField(TEXT("y"),Y) &&
            (*Pose)->TryGetNumberField(TEXT("z"),Z) && (*Pose)->TryGetNumberField(TEXT("yaw"),Yaw) &&
            FMath::IsFinite(X) && FMath::IsFinite(Y) && FMath::IsFinite(Z) && FMath::IsFinite(Yaw) &&
            FMath::Abs(X)<=2400000 && FMath::Abs(Y)<=2400000 && Z>=-2400000 && Z<=2400000)
        {
            const FVector Position(X,Y,Z); FHitResult Floor; FCollisionQueryParams Query; Query.AddIgnoredActor(Survivor);
            if(GetWorld()->LineTraceSingleByChannel(Floor,Position+FVector(0,0,50),Position-FVector(0,0,500),ECC_Visibility,Query))
            {
                Survivor->TeleportTo(Position,FRotator(0,Yaw,0),false,false);
                PlayerController->SetControlRotation(FRotator(0,Yaw,0));
            }
        }
    }
}

bool AAnomaliaGameMode::SavePersistentPlayer(AController* Controller)
{
    if (!HasAuthority() || !Controller) return false;
    AAnomaliaSurvivor* Survivor = Cast<AAnomaliaSurvivor>(Controller->GetPawn());
    if(!Survivor) if(auto* Vehicle=Cast<AAnomaliaVehiclePawn>(Controller->GetPawn())) Survivor=Vehicle->GetStoredDriverSurvivor();
    const FString PlayerId = GetPersistentPlayerId(Controller);
    const auto* Loot = GetWorld()->GetSubsystem<UAnomaliaLootSubsystem>();
    const auto* Economy = GetWorld()->GetSubsystem<UAnomaliaEconomySubsystem>();
    if (PendingProfileLoads.Contains(PlayerId) || (Loot && Loot->HasPendingPlayer(PlayerId)) ||
        (Economy && Economy->HasPendingPlayer(PlayerId))) return false;
    if (!Survivor || PlayerId.IsEmpty()) return false;

    FString Error;
    if (Survivor->InventoryComponent &&
        !Survivor->InventoryComponent->SaveInventoryToPlayerProfile(ServerId, PlayerId, Error))
    {
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA %s: inventory save rejected: %s"), *ServerId, *Error);
        return false;
    }

    FString Raw;
    TSharedPtr<FJsonObject> Root;
    if (UAnomaliaConfigLibrary::LoadPlayerProfile(ServerId, PlayerId, Raw, Error))
    {
        const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Raw);
        if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
        {
            UE_LOG(LogTemp, Warning, TEXT("ANOMALIA %s: invalid player profile left untouched"), *ServerId);
            return false;
        }
    }
    else if (Error == TEXT("Profile not found"))
    {
        Root = MakeShared<FJsonObject>();
    }
    else
    {
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA %s: player profile save aborted: %s"), *ServerId, *Error);
        return false;
    }

    TSharedPtr<FJsonObject> Survival = MakeShared<FJsonObject>();
    const TSharedPtr<FJsonObject>* ExistingSurvival = nullptr;
    if (Root->TryGetObjectField(TEXT("survival"), ExistingSurvival) && ExistingSurvival && ExistingSurvival->IsValid())
        Survival = *ExistingSurvival;
    Survival->SetNumberField(TEXT("hunger"), FMath::Clamp(Survivor->Hunger, 0.f, 100.f));
    Survival->SetNumberField(TEXT("thirst"), FMath::Clamp(Survivor->Thirst, 0.f, 100.f));
    Survival->SetNumberField(TEXT("health"), FMath::Clamp(Survivor->Health, 0.f, 100.f));
    Survival->SetNumberField(TEXT("fatigue"), FMath::Clamp(Survivor->Fatigue, 0.f, 100.f));
    if (Survivor->VitalsComponent)
    {
        Survival->SetNumberField(TEXT("stamina"), FMath::Clamp(Survivor->VitalsComponent->Stamina, 0.f, 100.f));
        Survival->SetNumberField(TEXT("bodyTemperatureC"),
            FMath::Clamp(Survivor->VitalsComponent->BodyTemperatureC, 25.f, 45.f));
    }
    Root->SetNumberField(TEXT("schemaVersion"), 1);
    Root->SetObjectField(TEXT("survival"), Survival);
    if(Survivor->ItemEffectsComponent && !UAnomaliaItemEffectsComponent::WriteState(Survival,Survivor->ItemEffectsComponent->State,Error))
    { UE_LOG(LogTemp,Warning,TEXT("ANOMALIA effects save refused: %s"),*Error);return false; }
    FVector Position=Survivor->GetActorLocation();
    if(auto* Vehicle=Cast<AAnomaliaVehiclePawn>(Controller->GetPawn()))
        Position=Vehicle->GetActorLocation()+Vehicle->GetActorRightVector()*350.f+FVector(0,0,120.f);
    auto Pose=MakeShared<FJsonObject>(); Pose->SetStringField(TEXT("map"),GetWorld()->GetMapName());
    Pose->SetNumberField(TEXT("x"),Position.X); Pose->SetNumberField(TEXT("y"),Position.Y); Pose->SetNumberField(TEXT("z"),Position.Z);
    Pose->SetNumberField(TEXT("yaw"),Controller->GetControlRotation().Yaw); Root->SetObjectField(TEXT("pose"),Pose);

    FString Serialized;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Serialized);
    FJsonSerializer::Serialize(Root.ToSharedRef(), Writer);
    if (!UAnomaliaConfigLibrary::SavePlayerProfile(ServerId, PlayerId, Serialized, Error))
    {
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA %s: profile save failed: %s"), *ServerId, *Error);
        return false;
    }
    return true;
}

bool AAnomaliaGameMode::SaveLocalGame()
{
    if(!HasAuthority() || GetNetMode()!=NM_Standalone) return false;
    auto* PC=GetWorld()->GetFirstPlayerController();
    auto* S=PC?Cast<AAnomaliaSurvivor>(PC->GetPawn()):nullptr;
    if(!S && PC) if(auto* V=Cast<AAnomaliaVehiclePawn>(PC->GetPawn())) S=V->GetStoredDriverSurvivor();
    if(!S || !S->InventoryComponent || S->InventoryComponent->IsPersistenceLocked()) return false;
    return SavePersistentPlayer(PC);
}

void AAnomaliaGameMode::SaveAllPlayerProfiles()
{
    if (!HasAuthority() || !GetWorld()) return;
    for (FConstPlayerControllerIterator It = GetWorld()->GetPlayerControllerIterator(); It; ++It)
        SavePersistentPlayer(It->Get());
}

void AAnomaliaGameMode::Logout(AController* Exiting)
{
    SavePersistentPlayer(Exiting);
    Super::Logout(Exiting);
}

AAnomaliaVehiclePawn* AAnomaliaGameMode::SpawnServerVehicle(FName VehicleId, const FTransform& SpawnTransform)
{
    if (!HasAuthority() || !GetWorld()) return nullptr;
    FAnomaliaVehicleDefinition Definition;
    if (!UAnomaliaVehicleCatalog::FindVehicleDefinition(VehicleId, Definition)) return nullptr;
    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButDontSpawnIfColliding;
    AAnomaliaVehiclePawn* Vehicle = GetWorld()->SpawnActor<AAnomaliaVehiclePawn>(
        AAnomaliaVehiclePawn::StaticClass(), SpawnTransform, Params);
    if (!Vehicle) return nullptr;
    if (!Vehicle->ConfigureVehicle(VehicleId))
    {
        Vehicle->Destroy();
        return nullptr;
    }
    return Vehicle;
}

void AAnomaliaGameMode::BeginPlay()
{
    Super::BeginPlay();
    if (HasAuthority())
    {
        SpawnConfiguredHomestead();
        SpawnConfiguredVehicles();
#if !UE_BUILD_SHIPPING
        FString ProbeFile;
        if (GetNetMode()==NM_Standalone && ServerId.StartsWith(TEXT("playable-smoke-")) &&
            GetWorld()->GetMapName().EndsWith(TEXT("ANOMALIA_Playable_v1")) &&
            FParse::Value(FCommandLine::Get(),TEXT("AnomaliaPlayableProbe="),ProbeFile) && !ProbeFile.IsEmpty())
            GetWorld()->SpawnActor<AAnomaliaPlayableProbe>();
        if(GetNetMode()==NM_Standalone && ServerId.StartsWith(TEXT("visual-smoke-")) &&
            GetWorld()->GetMapName().EndsWith(TEXT("ANOMALIA_VisualValidation_v1")) &&
            FParse::Value(FCommandLine::Get(),TEXT("AnomaliaVisualReview="),ProbeFile) && !ProbeFile.IsEmpty())
            GetWorld()->SpawnActor<AAnomaliaVisualReviewProbe>();
#endif
        if(GetNetMode()==NM_Standalone && GetWorld()->GetMapName().EndsWith(TEXT("ANOMALIA_Playable_v1")) && !ServerId.StartsWith(TEXT("playable-smoke-")))
            GetWorldTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(this,[this]()
            {
                auto* PC=GetWorld()->GetFirstPlayerController();
                if(PC) { PC->SetControlRotation(FRotator(0,90,0)); UAnomaliaSessionWidget::Open(PC,true); }
            }));
        GetWorldTimerManager().SetTimer(ProfileRecoveryTimer, this, &AAnomaliaGameMode::RetryPendingProfileLoads, 1.f, true);
        GetWorldTimerManager().SetTimer(ProfileSaveTimer, this, &AAnomaliaGameMode::SaveAllPlayerProfiles, 120.f, true);
    }
}

void AAnomaliaGameMode::SpawnConfiguredVehicles()
{
    // Server-owned only. No player RPC and no cross-server fallback.
    const FString File = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Servers"), ServerId, TEXT("vehicles.json"));
    if (!IFileManager::Get().FileExists(*File)) return;
    const int64 Bytes = IFileManager::Get().FileSize(*File);
    if (Bytes < 0 || Bytes > 262144)
    {
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA vehicles.json rejected: invalid file size for %s"), *ServerId);
        return;
    }
    FString Raw;
    if (!FFileHelper::LoadFileToString(Raw, *File)) return;
    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Raw);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA vehicles.json invalid for server %s"), *ServerId);
        return;
    }
    const TArray<TSharedPtr<FJsonValue>>* Rows = nullptr;
    if (!Root->TryGetArrayField(TEXT("vehicles"), Rows) || !Rows) return;
    int32 Spawned = 0;
    for (const TSharedPtr<FJsonValue>& RowValue : *Rows)
    {
        if (Spawned >= 64) break;
        const TSharedPtr<FJsonObject> Row = RowValue.IsValid() ? RowValue->AsObject() : nullptr;
        if (!Row.IsValid()) continue;
        FString VehicleName;
        double X = 0, Y = 0, Z = 0, Yaw = 0;
        if (!Row->TryGetStringField(TEXT("id"), VehicleName) ||
            !Row->TryGetNumberField(TEXT("x"), X) ||
            !Row->TryGetNumberField(TEXT("y"), Y) ||
            !Row->TryGetNumberField(TEXT("z"), Z)) continue;
        Row->TryGetNumberField(TEXT("yaw"), Yaw);
        // Unreal centimetres; the map is intended to be 48 km across.
        if (!FMath::IsFinite(X) || !FMath::IsFinite(Y) || !FMath::IsFinite(Z) ||
            !FMath::IsFinite(Yaw) || FMath::Abs(X) > 2400000.0 ||
            FMath::Abs(Y) > 2400000.0 || FMath::Abs(Z) > 2400000.0) continue;
        FAnomaliaVehicleDefinition Definition;
        const FName VehicleId(*VehicleName);
        if (!UAnomaliaVehicleCatalog::FindVehicleDefinition(VehicleId, Definition)) continue;
        const FTransform Transform(FRotator(0.f, static_cast<float>(Yaw), 0.f),
            FVector(X, Y, Z));
        // Optional server-local tuning. Invalid entries are rejected, not silently clamped.
        double Fuel = 100.0, Consumption = 0.045, SpeedScale = 1.0;
        Row->TryGetNumberField(TEXT("fuelPercent"), Fuel);
        Row->TryGetNumberField(TEXT("fuelConsumptionPerSecond"), Consumption);
        Row->TryGetNumberField(TEXT("speedMultiplier"), SpeedScale);
        if (!FMath::IsFinite(Fuel) || Fuel < 0.0 || Fuel > 100.0 ||
            !FMath::IsFinite(Consumption) || Consumption < 0.0 || Consumption > 10.0 ||
            !FMath::IsFinite(SpeedScale) || SpeedScale < 0.1 || SpeedScale > 3.0)
        {
            UE_LOG(LogTemp, Warning, TEXT("ANOMALIA %s: invalid vehicle tuning for %s"), *ServerId, *VehicleName);
            continue;
        }
        // Transport settings are server-local and validated before creating an actor.
        double Thrust=0, Stall=3500, Waterline=0, TrackDistance=0;
        const auto ReadOptionalNumber=[&Row](const TCHAR* Name,double& Value)
        { return !Row->HasField(Name)||Row->TryGetNumberField(Name,Value); };
        if(!ReadOptionalNumber(TEXT("thrustAcceleration"),Thrust)||!ReadOptionalNumber(TEXT("stallSpeedCm"),Stall)||
            !ReadOptionalNumber(TEXT("waterlineOffsetCm"),Waterline)||!ReadOptionalNumber(TEXT("trackDistanceCm"),TrackDistance)) continue;
        if(!FMath::IsFinite(Thrust)||Thrust<0||Thrust>10000||!FMath::IsFinite(Stall)||Stall<100||Stall>20000||
            !FMath::IsFinite(Waterline)||Waterline<0||Waterline>1000||!FMath::IsFinite(TrackDistance)||TrackDistance<0) continue;
        AAnomaliaRailTrack* Route=nullptr;
        if(Definition.Domain==EAnomaliaVehicleDomain::Rail)
        {
            FString RouteName;
            if(!Row->TryGetStringField(TEXT("routeId"),RouteName)||RouteName.IsEmpty()||RouteName.Len()>128) continue;
            bool bDuplicate=false;
            for(TActorIterator<AAnomaliaRailTrack> It(GetWorld());It;++It)
                if(It->RouteId==FName(*RouteName)) { if(Route) { bDuplicate=true; break; } Route=*It; }
            if(!Route||bDuplicate) { UE_LOG(LogTemp,Warning,TEXT("ANOMALIA rail route missing or ambiguous: %s"),*RouteName); continue; }
        }
        AAnomaliaVehiclePawn* Vehicle = SpawnServerVehicle(VehicleId, Transform);
        if (Vehicle)
        {
            if (!Vehicle->ConfigureRuntimeTuning(static_cast<float>(Fuel), static_cast<float>(Consumption),
                static_cast<float>(SpeedScale))) { Vehicle->Destroy(); continue; }
            Vehicle->TransportMovement->ThrustAcceleration=Thrust;
            Vehicle->TransportMovement->StallSpeedCm=Stall;
            Vehicle->TransportMovement->WaterlineOffsetCm=Waterline;
            if(Route && !Vehicle->TransportMovement->AssignTrack(Route,TrackDistance))
            {
                UE_LOG(LogTemp,Warning,TEXT("ANOMALIA train spawn is not near its rail position"));
                Vehicle->Destroy(); continue;
            }
            ++Spawned;
        }
    }
    UE_LOG(LogTemp, Log, TEXT("ANOMALIA %s: spawned %d initial vehicles"), *ServerId, Spawned);
}


namespace
{
    bool ParseHomesteadKind(const FString& Text, EAnomaliaHomesteadObject& OutKind)
    {
        using K = EAnomaliaHomesteadObject;
        if      (Text == TEXT("bed")) OutKind = K::Bed;
        else if (Text == TEXT("table")) OutKind = K::Table;
        else if (Text == TEXT("chair")) OutKind = K::Chair;
        else if (Text == TEXT("sofa")) OutKind = K::Sofa;
        else if (Text == TEXT("wardrobe")) OutKind = K::Wardrobe;
        else if (Text == TEXT("kitchen")) OutKind = K::Kitchen;
        else if (Text == TEXT("lamp")) OutKind = K::Lamp;
        else if (Text == TEXT("cow")) OutKind = K::Cow;
        else if (Text == TEXT("chicken")) OutKind = K::Chicken;
        else if (Text == TEXT("beehive")) OutKind = K::Beehive;
        else if (Text == TEXT("doghouse")) OutKind = K::Doghouse;
        else if (Text == TEXT("barn")) OutKind = K::Barn;
        else if (Text == TEXT("fence")) OutKind = K::Fence;
        else if (Text == TEXT("tractor_shed")) OutKind = K::TractorShed;
        else return false;
        return true;
    }

    bool SafePlacementId(const FString& Id)
    {
        if (Id.IsEmpty() || Id.Len() > 64) return false;
        for (const TCHAR C : Id)
            if (C > 127 || !(FChar::IsAlnum(C) || C == TEXT('-') || C == TEXT('_'))) return false;
        return true;
    }

    struct FAnomaliaPlacementToSpawn
    {
        EAnomaliaHomesteadObject Kind;
        FTransform Transform;
    };
}

void AAnomaliaGameMode::SpawnConfiguredHomestead()
{
    if (!HasAuthority() || !GetWorld()) return;
    // No global/shared layout fallback: a single server's saved Editor/ world only.
    const FString File = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Servers"), ServerId,
        TEXT("Editor"), TEXT("world.json"));
    if (!IFileManager::Get().FileExists(*File)) return;
    const int64 Bytes = IFileManager::Get().FileSize(*File);
    if (Bytes <= 0 || Bytes > 262144) return;

    FString Raw;
    if (!FFileHelper::LoadFileToString(Raw, *File)) return;
    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Raw);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid()) return;

    FString StoredServer;
    double Version = 0.0;
    if (!Root->TryGetStringField(TEXT("serverId"), StoredServer) ||
        StoredServer != ServerId ||
        !Root->TryGetNumberField(TEXT("schemaVersion"), Version) || Version != 1.0) return;

    const TArray<TSharedPtr<FJsonValue>>* Rows = nullptr;
    if (!Root->TryGetArrayField(TEXT("placements"), Rows) || !Rows || Rows->Num() > 256) return;
    TSet<FString> SeenIds;
    TArray<FAnomaliaPlacementToSpawn> Validated;
    Validated.Reserve(Rows->Num());

    // Validate the entire file first: malformed entries produce no partial world updates.
    for (const TSharedPtr<FJsonValue>& Value : *Rows)
    {
        const TSharedPtr<FJsonObject> Row = Value.IsValid() ? Value->AsObject() : nullptr;
        if (!Row.IsValid() || Row->Values.Num() != 6) return;
        FString ObjectId, KindName;
        double X = 0.0, Y = 0.0, Z = 0.0, Yaw = 0.0;
        if (!Row->TryGetStringField(TEXT("id"), ObjectId) || !SafePlacementId(ObjectId) ||
            SeenIds.Contains(ObjectId) ||
            !Row->TryGetStringField(TEXT("type"), KindName) ||
            !Row->TryGetNumberField(TEXT("x"), X) ||
            !Row->TryGetNumberField(TEXT("y"), Y) ||
            !Row->TryGetNumberField(TEXT("z"), Z) ||
            !Row->TryGetNumberField(TEXT("yaw"), Yaw)) return;

        EAnomaliaHomesteadObject Kind;
        if (!ParseHomesteadKind(KindName, Kind) ||
            !FMath::IsFinite(X) || !FMath::IsFinite(Y) ||
            !FMath::IsFinite(Z) || !FMath::IsFinite(Yaw) ||
            FMath::Abs(X) > 2400000.0 || FMath::Abs(Y) > 2400000.0 ||
            FMath::Abs(Z) > 2400000.0 || FMath::Abs(Yaw) > 360.0) return;
        SeenIds.Add(ObjectId);
        Validated.Add({Kind, FTransform(FRotator(0.f, static_cast<float>(Yaw), 0.f),
            FVector(X, Y, Z))});
    }

    int32 Spawned = 0;
    for (const FAnomaliaPlacementToSpawn& Placement : Validated)
    {
        FActorSpawnParameters Params;
        Params.SpawnCollisionHandlingOverride =
            ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
        AAnomaliaHomesteadStation* Station = GetWorld()->SpawnActor<AAnomaliaHomesteadStation>(
            AAnomaliaHomesteadStation::StaticClass(), Placement.Transform, Params);
        if (!Station) continue;
        Station->ObjectType = Placement.Kind;
        Station->ForceNetUpdate();
        ++Spawned;
    }
    UE_LOG(LogTemp, Log, TEXT("ANOMALIA server %s: %d homestead placeables loaded"),
        *ServerId, Spawned);
}

void AAnomaliaGameMode::RetryPendingProfileLoads()
{
    if (!HasAuthority() || !GetWorld() || PendingProfileLoads.IsEmpty()) return;
    const auto* Loot = GetWorld()->GetSubsystem<UAnomaliaLootSubsystem>();
    const auto* Economy = GetWorld()->GetSubsystem<UAnomaliaEconomySubsystem>();
    for (FConstPlayerControllerIterator It = GetWorld()->GetPlayerControllerIterator(); It; ++It)
    {
        APlayerController* Controller = It->Get();
        const FString PlayerId = GetPersistentPlayerId(Controller);
        if (PendingProfileLoads.Contains(PlayerId) && (!Loot || !Loot->HasPendingPlayer(PlayerId)) &&
            (!Economy || !Economy->HasPendingPlayer(PlayerId)))
            LoadPersistentPlayer(Controller);
    }
}
