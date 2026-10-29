#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaZPrigimaliaPlayableProbe.generated.h"
class AAnomaliaZPrigimaliaSurvivor;
class AAnomaliaZPrigimaliaVehiclePawn;
/** Development-only packaged-game smoke runner. Spawned only in an isolated local test scope. */
UCLASS()
class ANOMALIAZPRIGIMALIA_API AAnomaliaZPrigimaliaPlayableProbe : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaZPrigimaliaPlayableProbe();
    virtual void Tick(float DeltaSeconds) override;
private:
    int32 Phase=0, VehicleIndex=0;
    int32 UsedStackId=0, UsedCount=0;
    double Started=0, Next=0;
    FVector Before=FVector::ZeroVector, House=FVector::ZeroVector;
    float DoorSign=1;
    TWeakObjectPtr<AAnomaliaZPrigimaliaSurvivor> Survivor;
    TArray<TWeakObjectPtr<AAnomaliaZPrigimaliaVehiclePawn>> Vehicles;
    TArray<FString> Checks;
    void Finish(const FString& Error=FString());
};
