#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "AnomaliaGameMode.generated.h"

class AAnomaliaVehiclePawn;

UCLASS()
class ANOMALIAPRIMEVAL_API AAnomaliaGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AAnomaliaGameMode();

    /** Called by trusted server logic only. Not a client spawn RPC. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Server|Vehicles")
    AAnomaliaVehiclePawn* SpawnServerVehicle(FName VehicleId, const FTransform& SpawnTransform);
};
