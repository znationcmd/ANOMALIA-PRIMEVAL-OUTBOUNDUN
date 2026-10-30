#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaZPrigimaliaVisualReviewProbe.generated.h"
class AAnomaliaZPrigimaliaSurvivor;
class AAnomaliaZPrigimaliaVehiclePawn;
class ACameraActor;
/** Isolated development probe for the real imported-art map, not an image generator. */
UCLASS()
class ANOMALIAZPRIGIMALIA_API AAnomaliaZPrigimaliaVisualReviewProbe : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaZPrigimaliaVisualReviewProbe();
    virtual void Tick(float DeltaSeconds) override;
private:
    int32 Phase=0,Shot=0;
    double Started=0,Next=0;
    double PreviousFrame=0,MeasuredSeconds=0,WorstFrame=0;
    int32 MeasuredFrames=0;
    FVector Before=FVector::ZeroVector,CarStart=FVector::ZeroVector;
    TWeakObjectPtr<AAnomaliaZPrigimaliaSurvivor> Survivor;
    TWeakObjectPtr<AAnomaliaZPrigimaliaVehiclePawn> Car;
    TArray<TWeakObjectPtr<AAnomaliaZPrigimaliaVehiclePawn>> Vehicles;
    int32 VehicleIndex=0;
    bool bNight=false;
    TArray<TWeakObjectPtr<ACameraActor>> Cameras;
    TArray<FString> Screenshots,Checks,MeshPaths;
    void Finish(const FString& Error=FString());
};
