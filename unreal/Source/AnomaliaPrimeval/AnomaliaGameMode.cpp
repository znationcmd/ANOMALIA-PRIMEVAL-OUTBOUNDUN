#include "AnomaliaGameMode.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaVehiclePawn.h"
#include "AnomaliaVehicleCatalog.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

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
