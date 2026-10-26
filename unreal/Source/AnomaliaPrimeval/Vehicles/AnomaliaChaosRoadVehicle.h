#pragma once

#include "CoreMinimal.h"
#include "../AnomaliaVehiclePawn.h"
#include "ChaosVehicleWheel.h"
#include "AnomaliaChaosRoadVehicle.generated.h"

class UChaosWheeledVehicleMovementComponent;
class USkeletalMeshComponent;
class USkeletalMesh;
class UStaticMesh;
class UStaticMeshComponent;
class UAnimInstance;
class UPhysicsAsset;

UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaRoadFrontWheel : public UChaosVehicleWheel
{
    GENERATED_BODY()
public:
    UAnomaliaRoadFrontWheel();
};

UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaRoadRearWheel : public UAnomaliaRoadFrontWheel
{
    GENERATED_BODY()
public:
    UAnomaliaRoadRearWheel();
};

/** Actual skeletal Chaos road simulation. Missing art/rig refuses driving; no block fallback. */
UCLASS(Blueprintable)
class ANOMALIAPRIMEVAL_API AAnomaliaChaosRoadVehicle : public AAnomaliaVehiclePawn
{
    GENERATED_BODY()
public:
    AAnomaliaChaosRoadVehicle();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos")
    TObjectPtr<USkeletalMeshComponent> Chassis;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos")
    TObjectPtr<UChaosWheeledVehicleMovementComponent> ChaosMovement;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos")
    TObjectPtr<USkeletalMesh> RoadMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos")
    TSubclassOf<UAnimInstance> RoadAnimation;
    /** Licensed modular art, assembled on the actual animated skeleton. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos") TObjectPtr<UStaticMesh> RoadBodyMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos") TObjectPtr<UStaticMesh> RoadWheelMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos") TObjectPtr<UStaticMesh> RoadGlassMesh;
    /** Optional individually modelled wheels, paired with authored chassis-space hubs. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos") TArray<TObjectPtr<UStaticMesh>> RoadWheelMeshes;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos") TArray<FVector> RoadWheelHubTargetsCm;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos") TObjectPtr<UStaticMeshComponent> RoadGlass;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos") TArray<TObjectPtr<UStaticMeshComponent>> RoadWheels;
    /** Front left, front right, rear left, rear right. Names come from the actual rig. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos")
    TArray<FName> WheelBones;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos", meta=(ClampMin="10",ClampMax="100"))
    float WheelRadiusCm=40.f;

    virtual UPawnMovementComponent* GetMovementComponent() const override;
    virtual bool ConfigureVehicle(FName NewVehicleId) override;
    virtual void OnConstruction(const FTransform& Transform) override;
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Chaos")
    bool HasValidRoadRig() const;
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Chaos")
    bool IsChaosDriveReady() const;
protected:
    virtual void BeginPlay() override;
    virtual bool UsesPhysicsRoadSimulation() const override { return true; }
    virtual bool IsDriveReady() const override;
    virtual bool CanDriverExitNow() const override;
    virtual float GetExpectedSupportFloorZ() const override;
    virtual void SimulateRoadDrive(float DeltaSeconds,float Throttle,float Steering,float Brake,
        bool bPowered,bool bDriverMissing) override;
private:
    /** Per-instance chassis collision; never modifies a shared source Physics Asset. */
    UPROPERTY(Transient) TObjectPtr<UPhysicsAsset> RuntimeChassisPhysics;
    FTransform ReferenceBoneTransform(FName Bone) const;
    void ApplyRoadRig();
};
