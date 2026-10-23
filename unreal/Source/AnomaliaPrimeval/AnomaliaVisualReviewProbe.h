#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaVisualReviewProbe.generated.h"
class AAnomaliaSurvivor;
class AAnomaliaVehiclePawn;
class ACameraActor;
/** Isolated development probe for the real imported-art map, not an image generator. */
UCLASS()
class ANOMALIAPRIMEVAL_API AAnomaliaVisualReviewProbe : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaVisualReviewProbe();
    virtual void Tick(float DeltaSeconds) override;
private:
    int32 Phase=0,Shot=0;
    double Started=0,Next=0;
    double PreviousFrame=0,MeasuredSeconds=0,WorstFrame=0;
    int32 MeasuredFrames=0;
    FVector Before=FVector::ZeroVector,CarStart=FVector::ZeroVector;
    TWeakObjectPtr<AAnomaliaSurvivor> Survivor;
    TWeakObjectPtr<AAnomaliaVehiclePawn> Car;
    TArray<TWeakObjectPtr<AAnomaliaVehiclePawn>> Vehicles;
    int32 VehicleIndex=0;
    bool bNight=false;
    TArray<TWeakObjectPtr<ACameraActor>> Cameras;
    TArray<FString> Screenshots,Checks,MeshPaths;
    void Finish(const FString& Error=FString());
};
