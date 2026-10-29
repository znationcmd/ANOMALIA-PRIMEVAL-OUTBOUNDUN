#pragma once
#include "CoreMinimal.h"
#include "GameFramework/PawnMovementComponent.h"
#include "AnomaliaZPrigimaliaTransportDynamics.h"
#include "../AnomaliaZPrigimaliaVehicleCatalog.h"
#include "AnomaliaZPrigimaliaTransportMovement.generated.h"
class AAnomaliaZPrigimaliaRailTrack;
class AAnomaliaZPrigimaliaNavigableWater;

/** Server-authoritative, swept prototype dynamics. Ground vehicles keep their existing movement. */
UCLASS(ClassGroup=(ANOMALIA), meta=(BlueprintSpawnableComponent))
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaTransportMovement : public UPawnMovementComponent
{
    GENERATED_BODY()
public:
    UAnomaliaZPrigimaliaTransportMovement();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    void Configure(const FAnomaliaZPrigimaliaVehicleDefinition& Definition,float SpeedMultiplier);
    bool IsTransport() const { return bTransport; }
    void Simulate(float DeltaSeconds,AnomaliaZPrigimaliaTransport::Controls Input,bool bPowered);
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Rail")
    bool AssignTrack(AAnomaliaZPrigimaliaRailTrack* Route,float DistanceCm);
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Rail")
    float GetTrackDistance() const { return RailDistanceCm; }
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Rail")
    float GetRailSpeed() const { return RailSpeedCm; }
    AAnomaliaZPrigimaliaRailTrack* GetRailTrack() const;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Transport", meta=(ClampMin="0",ClampMax="1000"))
    float WaterlineOffsetCm=0;
    /** Additional thrust acceleration, cm/s^2. Zero selects per-category defaults. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Transport", meta=(ClampMin="0",ClampMax="10000"))
    float ThrustAcceleration=0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Transport", meta=(ClampMin="100",ClampMax="20000"))
    float StallSpeedCm=3500;
private:
    bool bTransport=false;
    bool bUprightCabin=false;
    FQuat RouteRotation(const FQuat& Rotation) const;
    AnomaliaZPrigimaliaTransport::Mode Kind=AnomaliaZPrigimaliaTransport::Mode::Surface;
    AnomaliaZPrigimaliaTransport::Settings Parameters;
    TWeakObjectPtr<AAnomaliaZPrigimaliaRailTrack> Rail;
    TWeakObjectPtr<AAnomaliaZPrigimaliaNavigableWater> Water;
    double WaterSearchAt=0;
    UPROPERTY(Replicated)
    float RailDistanceCm=0;
    UPROPERTY(Replicated)
    float RailSpeedCm=0;
    bool SampleWater(double& Surface,double& Bottom);
    void Step(double Dt,AnomaliaZPrigimaliaTransport::Controls Input,bool bPowered);
    void StepRail(double Dt,AnomaliaZPrigimaliaTransport::Controls Input,bool bPowered);
};
