#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Dom/JsonValue.h"
#include "AnomaliaChaosRoadProbe.generated.h"
class AAnomaliaChaosRoadVehicle;
class AAnomaliaSurvivor;

/** Runs only with an explicit command line, isolated server ID and dedicated review map. */
UCLASS()
class ANOMALIAPRIMEVAL_API AAnomaliaChaosRoadProbe : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaChaosRoadProbe();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
private:
    bool bEnabled=false;
    int32 Phase=0;
    double Started=0, PhaseStarted=0, LastSample=0;
    float StraightSpeed=0, TurnYaw=0, BrakeStartSpeed=0;
    FVector StartLocation=FVector::ZeroVector;
    FString ReportFile;
    TWeakObjectPtr<AAnomaliaChaosRoadVehicle> Car;
    TWeakObjectPtr<AAnomaliaSurvivor> Survivor;
    TArray<TSharedPtr<FJsonValue>> Samples;
    TArray<FString> Checks;
    void Finish(const FString& Error=FString());
};
