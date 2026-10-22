#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaPlayableProbe.generated.h"
class AAnomaliaSurvivor;
class AAnomaliaVehiclePawn;
/** Development-only packaged-game smoke runner. Spawned only in an isolated local test scope. */
UCLASS()
class ANOMALIAPRIMEVAL_API AAnomaliaPlayableProbe : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaPlayableProbe();
    virtual void Tick(float DeltaSeconds) override;
private:
    int32 Phase=0, VehicleIndex=0;
    int32 UsedStackId=0, UsedCount=0;
    double Started=0, Next=0;
    FVector Before=FVector::ZeroVector, House=FVector::ZeroVector;
    float DoorSign=1;
    TWeakObjectPtr<AAnomaliaSurvivor> Survivor;
    TArray<TWeakObjectPtr<AAnomaliaVehiclePawn>> Vehicles;
    TArray<FString> Checks;
    void Finish(const FString& Error=FString());
};
