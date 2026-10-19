#include "AnomaliaGameMode.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaVehiclePawn.h"
#include "AnomaliaVehicleCatalog.h"
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
    FString ConfigError;
    if (!UAnomaliaConfigLibrary::LoadServerSettings(ServerId, ActiveServerSettings, ConfigError))
    {
        // Default values are safe; never overwrite invalid configuration automatically.
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA server %s: %s"), *ServerId, *ConfigError);
    }
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
    if (HasAuthority()) SpawnConfiguredVehicles();
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
