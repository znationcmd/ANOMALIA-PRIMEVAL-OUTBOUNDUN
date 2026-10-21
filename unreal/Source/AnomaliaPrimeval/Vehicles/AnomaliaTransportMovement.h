#pragma once
#include "CoreMinimal.h"
#include "GameFramework/PawnMovementComponent.h"
#include "AnomaliaTransportDynamics.h"
#include "../AnomaliaVehicleCatalog.h"
#include "AnomaliaTransportMovement.generated.h"
class AAnomaliaRailTrack;
class AAnomaliaNavigableWater;

/** Server-authoritative, swept prototype dynamics. Ground vehicles keep their existing movement. */
UCLASS(ClassGroup=(ANOMALIA), meta=(BlueprintSpawnableComponent))
class ANOMALIAPRIMEVAL_API UAnomaliaTransportMovement : public UPawnMovementComponent
{
    GENERATED_BODY()
public:
    UAnomaliaTransportMovement();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    void Configure(const FAnomaliaVehicleDefinition& Definition,float SpeedMultiplier);
    bool IsTransport() const { return bTransport; }
    void Simulate(float DeltaSeconds,AnomaliaTransport::Controls Input,bool bPowered);
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Rail")
    bool AssignTrack(AAnomaliaRailTrack* Route,float DistanceCm);
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Rail")
    float GetTrackDistance() const { return RailDistanceCm; }
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Rail")
    float GetRailSpeed() const { return RailSpeedCm; }
    AAnomaliaRailTrack* GetRailTrack() const;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Transport", meta=(ClampMin="0",ClampMax="1000"))
    float WaterlineOffsetCm=0;
    /** Additional thrust acceleration, cm/s^2. Zero selects per-category defaults. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Transport", meta=(ClampMin="0",ClampMax="10000"))
    float ThrustAcceleration=0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Transport", meta=(ClampMin="100",ClampMax="20000"))
    float StallSpeedCm=3500;
private:
    bool bTransport=false;
    AnomaliaTransport::Mode Kind=AnomaliaTransport::Mode::Surface;
    AnomaliaTransport::Settings Parameters;
    TWeakObjectPtr<AAnomaliaRailTrack> Rail;
    TWeakObjectPtr<AAnomaliaNavigableWater> Water;
    double WaterSearchAt=0;
    UPROPERTY(Replicated)
    float RailDistanceCm=0;
    UPROPERTY(Replicated)
    float RailSpeedCm=0;
    bool SampleWater(double& Surface,double& Bottom);
    void Step(double Dt,AnomaliaTransport::Controls Input,bool bPowered);
    void StepRail(double Dt,AnomaliaTransport::Controls Input,bool bPowered);
};
