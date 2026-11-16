#include "AnomaliaGameMode.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaInventoryComponent.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "Misc/SecureHash.h"
#include "TimerManager.h"
#include "AnomaliaVehiclePawn.h"
#include "AnomaliaVehicleCatalog.h"
#include "AnomaliaPowerGenerator.h"
#include "AnomaliaRefrigerator.h"
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
    GeneratorClass = AAnomaliaPowerGenerator::StaticClass();
    RefrigeratorClass = AAnomaliaRefrigerator::StaticClass();
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
    FString ConfigError;
    if (!UAnomaliaConfigLibrary::LoadServerSettings(ServerId, ActiveServerSettings, ConfigError))
    {
        // Default values are safe; never overwrite invalid configuration automatically.
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA server %s: %s"), *ServerId, *ConfigError);
    }
}


FString AAnomaliaGameMode::GetPersistentPlayerId(const AController* Controller) const
{
    if (!Controller || !Controller->PlayerState) return FString();
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
            UE_LOG(LogTemp, Warning, TEXT("ANOMALIA %s: inventory load rejected: %s"), *ServerId, *InventoryError);
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
}

void AAnomaliaGameMode::SavePersistentPlayer(AController* Controller)
{
    if (!HasAuthority() || !Controller) return;
    AAnomaliaSurvivor* Survivor = Cast<AAnomaliaSurvivor>(Controller->GetPawn());
    const FString PlayerId = GetPersistentPlayerId(Controller);
    if (!Survivor || PlayerId.IsEmpty()) return;

    FString Error;
    if (Survivor->InventoryComponent &&
        !Survivor->InventoryComponent->SaveInventoryToPlayerProfile(ServerId, PlayerId, Error))
    {
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA %s: inventory save rejected: %s"), *ServerId, *Error);
        return;
    }

    FString Raw;
    TSharedPtr<FJsonObject> Root;
    if (UAnomaliaConfigLibrary::LoadPlayerProfile(ServerId, PlayerId, Raw, Error))
    {
        const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Raw);
        if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
        {
            UE_LOG(LogTemp, Warning, TEXT("ANOMALIA %s: invalid player profile left untouched"), *ServerId);
            return;
        }
    }
    else if (Error == TEXT("Profile not found"))
    {
        Root = MakeShared<FJsonObject>();
    }
    else
    {
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA %s: player profile save aborted: %s"), *ServerId, *Error);
        return;
    }

    TSharedPtr<FJsonObject> Survival = MakeShared<FJsonObject>();
    const TSharedPtr<FJsonObject>* ExistingSurvival = nullptr;
    if (Root->TryGetObjectField(TEXT("survival"), ExistingSurvival) && ExistingSurvival && ExistingSurvival->IsValid())
        Survival = *ExistingSurvival;
    Survival->SetNumberField(TEXT("hunger"), FMath::Clamp(Survivor->Hunger, 0.f, 100.f));
    Survival->SetNumberField(TEXT("thirst"), FMath::Clamp(Survivor->Thirst, 0.f, 100.f));
    Survival->SetNumberField(TEXT("health"), FMath::Clamp(Survivor->Health, 0.f, 100.f));
    Root->SetNumberField(TEXT("schemaVersion"), 1);
    Root->SetObjectField(TEXT("survival"), Survival);

    FString Serialized;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Serialized);
    FJsonSerializer::Serialize(Root.ToSharedRef(), Writer);
    if (!UAnomaliaConfigLibrary::SavePlayerProfile(ServerId, PlayerId, Serialized, Error))
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA %s: profile save failed: %s"), *ServerId, *Error);
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
        SpawnConfiguredVehicles();
        SpawnConfiguredAppliances();
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
        AAnomaliaVehiclePawn* Vehicle = SpawnServerVehicle(VehicleId, Transform);
        if (Vehicle)
        {
            if (!Vehicle->ConfigureRuntimeTuning(static_cast<float>(Fuel), static_cast<float>(Consumption),
                static_cast<float>(SpeedScale))) { Vehicle->Destroy(); continue; }
            ++Spawned;
        }
    }
    UE_LOG(LogTemp, Log, TEXT("ANOMALIA %s: spawned %d initial vehicles"), *ServerId, Spawned);
}


void AAnomaliaGameMode::SpawnConfiguredAppliances()
{
    if (!HasAuthority() || !GetWorld()) return;
    // Optional, map-specific configuration. No file is auto-created or overwritten.
    const FString File = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Servers"), ServerId, TEXT("appliances.json"));
    if (!IFileManager::Get().FileExists(*File)) return;
    const int64 Bytes = IFileManager::Get().FileSize(*File);
    if (Bytes < 0 || Bytes > 262144) { UE_LOG(LogTemp, Warning, TEXT("ANOMALIA appliances.json: invalid size")); return; }
    FString Raw;
    if (!FFileHelper::LoadFileToString(Raw, *File)) return;
    TSharedPtr<FJsonObject> Root;
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw), Root) || !Root.IsValid())
    { UE_LOG(LogTemp, Warning, TEXT("ANOMALIA appliances.json: invalid JSON")); return; }

    auto ValidId = [](const FString& Id) -> bool
    {
        if (Id.IsEmpty() || Id.Len() > 64) return false;
        for (TCHAR C : Id)
            if (C > 127 || !(FChar::IsAlnum(C) || C == TEXT('_') || C == TEXT('-'))) return false;
        return true;
    };
    auto TransformFromRow = [](const TSharedPtr<FJsonObject>& Row, FTransform& OutTransform) -> bool
    {
        if (!Row.IsValid()) return false;
        double X=0, Y=0, Z=0, Yaw=0;
        if (!Row->TryGetNumberField(TEXT("x"), X) || !Row->TryGetNumberField(TEXT("y"), Y) ||
            !Row->TryGetNumberField(TEXT("z"), Z)) return false;
        Row->TryGetNumberField(TEXT("yaw"), Yaw);
        if (!FMath::IsFinite(X) || !FMath::IsFinite(Y) || !FMath::IsFinite(Z) || !FMath::IsFinite(Yaw) ||
            FMath::Abs(X) > 2400000 || FMath::Abs(Y) > 2400000 || FMath::Abs(Z) > 2400000) return false;
        OutTransform = FTransform(FRotator(0.f, static_cast<float>(Yaw), 0.f), FVector(X, Y, Z));
        return true;
    };

    TMap<FString, AAnomaliaPowerGenerator*> Generators;
    TSet<FString> UsedGeneratorIds;
    const TArray<TSharedPtr<FJsonValue>>* GeneratorRows = nullptr;
    if (Root->TryGetArrayField(TEXT("generators"), GeneratorRows) && GeneratorRows)
    {
        for (const TSharedPtr<FJsonValue>& Value : *GeneratorRows)
        {
            if (Generators.Num() >= 32) break;
            const TSharedPtr<FJsonObject> Row = Value.IsValid() ? Value->AsObject() : nullptr;
            FString Id;
            FTransform Placement;
            double Fuel = 10;
            bool bRun = false;
            if (!Row.IsValid() || !Row->TryGetStringField(TEXT("id"), Id) ||
                !ValidId(Id) || UsedGeneratorIds.Contains(Id) || !TransformFromRow(Row, Placement)) continue;
            Row->TryGetNumberField(TEXT("fuelLitres"), Fuel);
            Row->TryGetBoolField(TEXT("running"), bRun);
            if (!FMath::IsFinite(Fuel) || Fuel < 0 || Fuel > 30) continue;
            UsedGeneratorIds.Add(Id);
            UClass* Class = GeneratorClass ? GeneratorClass.Get() : AAnomaliaPowerGenerator::StaticClass();
            AAnomaliaPowerGenerator* Generator = GetWorld()->SpawnActorDeferred<AAnomaliaPowerGenerator>(
                Class, Placement, nullptr, nullptr, ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButDontSpawnIfColliding);
            if (!Generator) continue;
            Generator->PersistentId = Id;
            Generator->FuelLitres = static_cast<float>(Fuel);
            Generator->bRunning = bRun && Fuel > 0;
            UGameplayStatics::FinishSpawningActor(Generator, Placement);
            Generators.Add(Id, Generator);
        }
    }

    TSet<FString> UsedFridgeIds;
    const TArray<TSharedPtr<FJsonValue>>* FridgeRows = nullptr;
    int32 SpawnedFridges = 0;
    if (Root->TryGetArrayField(TEXT("refrigerators"), FridgeRows) && FridgeRows)
    {
        for (const TSharedPtr<FJsonValue>& Value : *FridgeRows)
        {
            if (SpawnedFridges >= 128) break;
            const TSharedPtr<FJsonObject> Row = Value.IsValid() ? Value->AsObject() : nullptr;
            FString Id, GeneratorId;
            FTransform Placement;
            double Target = 4, Ambient = 22;
            bool bOn = true;
            if (!Row.IsValid() || !Row->TryGetStringField(TEXT("id"), Id) ||
                !ValidId(Id) || UsedFridgeIds.Contains(Id) || !TransformFromRow(Row, Placement)) continue;
            Row->TryGetStringField(TEXT("generatorId"), GeneratorId);
            Row->TryGetNumberField(TEXT("targetC"), Target);
            Row->TryGetNumberField(TEXT("ambientC"), Ambient);
            Row->TryGetBoolField(TEXT("switchedOn"), bOn);
            if (!FMath::IsFinite(Target) || Target < 0 || Target > 12 ||
                !FMath::IsFinite(Ambient) || Ambient < -15 || Ambient > 45) continue;
            UsedFridgeIds.Add(Id);
            UClass* Class = RefrigeratorClass ? RefrigeratorClass.Get() : AAnomaliaRefrigerator::StaticClass();
            AAnomaliaRefrigerator* Fridge = GetWorld()->SpawnActorDeferred<AAnomaliaRefrigerator>(
                Class, Placement, nullptr, nullptr, ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButDontSpawnIfColliding);
            if (!Fridge) continue;
            Fridge->PersistentId = Id;
            Fridge->PowerGenerator = Generators.FindRef(GeneratorId);
            Fridge->SetPointC = static_cast<float>(Target);
            Fridge->AmbientTemperatureC = static_cast<float>(Ambient);
            Fridge->bSwitchedOn = bOn;
            UGameplayStatics::FinishSpawningActor(Fridge, Placement);
            ++SpawnedFridges;
        }
    }
    UE_LOG(LogTemp, Log, TEXT("ANOMALIA %s: spawned %d generators and %d fridges from appliances.json"),
        *ServerId, Generators.Num(), SpawnedFridges);
}
