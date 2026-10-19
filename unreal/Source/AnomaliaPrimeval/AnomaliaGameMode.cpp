#include "AnomaliaGameMode.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaVehiclePawn.h"
#include "AnomaliaVehicleCatalog.h"

AAnomaliaGameMode::AAnomaliaGameMode()
{
    DefaultPawnClass = AAnomaliaSurvivor::StaticClass();
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
