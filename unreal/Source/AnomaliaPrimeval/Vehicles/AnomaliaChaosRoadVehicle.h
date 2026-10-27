#pragma once

#include "CoreMinimal.h"
#include "../AnomaliaVehiclePawn.h"
#include "ChaosVehicleWheel.h"
#include "AnomaliaChaosRoadVehicle.generated.h"

class UAnomaliaVehicleSurvivalComponent;
class UAnomaliaInventoryComponent;
class UChaosWheeledVehicleMovementComponent;
class USkeletalMeshComponent;
class USkeletalMesh;
class UStaticMesh;
class UStaticMeshComponent;
class UAnimInstance;
class UPhysicsAsset;
class USpotLightComponent;
class UPointLightComponent;
class UAnomaliaVehiclePanelComponent;

UENUM(BlueprintType)
enum class EAnomaliaRoadAction : uint8
{
    GearUp, GearDown, ToggleGearMode, HandbrakeOn, HandbrakeOff,
    Headlights, IndicatorLeft, IndicatorRight, HazardLights, DriverDoor
};

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

/** Native/Blueprint reusable panel configuration; identity is stable within the vehicle. */
USTRUCT(BlueprintType)
struct ANOMALIAPRIMEVAL_API FAnomaliaRoadPanelDefinition
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="ANOMALIA|Panel") FName PanelId;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="ANOMALIA|Panel") TObjectPtr<UStaticMesh> Mesh=nullptr;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="ANOMALIA|Panel") FVector PivotCm=FVector::ZeroVector;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="ANOMALIA|Panel") FVector HingeAxis=FVector::UpVector;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="ANOMALIA|Panel") float OpenAngleDegrees=70.f;
};

/** Actual skeletal Chaos road simulation. Missing art/rig refuses driving; no block fallback. */
UCLASS(Blueprintable)
class ANOMALIAPRIMEVAL_API AAnomaliaChaosRoadVehicle : public AAnomaliaVehiclePawn
{
    GENERATED_BODY()
public:
    AAnomaliaChaosRoadVehicle();
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="ANOMALIA|Vehicle|Maintenance") TObjectPtr<UAnomaliaVehicleSurvivalComponent> SurvivalSystems;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="ANOMALIA|Vehicle|Cargo") TObjectPtr<UAnomaliaInventoryComponent> CargoInventory;
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
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos|Panels") TObjectPtr<UStaticMesh> DriverDoorMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos|Panels") FVector DriverDoorPivotCm=FVector(129,-88.5,94);
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos|Panels") TObjectPtr<UAnomaliaVehiclePanelComponent> DriverDoor;
    /** Five extra default subobjects keep replication identities stable on server and clients. */
    UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="ANOMALIA|Chaos|Panels") TArray<FAnomaliaRoadPanelDefinition> AdditionalPanelDefinitions;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="ANOMALIA|Chaos|Panels") TArray<TObjectPtr<UAnomaliaVehiclePanelComponent>> AdditionalPanels;
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
    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    /** Starts stopped. Only the current server-validated driver may change ignition. */
    UPROPERTY(ReplicatedUsing=OnRep_EngineRunning, VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos|Engine")
    bool bEngineRunning=false;
    bool SetEngineRunningOnServer(AController* Driver, bool bRunning);
    bool ExecuteRoadActionOnServer(AController* Driver, EAnomaliaRoadAction Action);
    UPROPERTY(ReplicatedUsing=OnRep_RoadControls, VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos|Controls") bool bManualGears=false;
    UPROPERTY(ReplicatedUsing=OnRep_RoadControls, VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos|Controls") bool bHandbrakeHeld=false;
    UPROPERTY(ReplicatedUsing=OnRep_RoadControls, VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos|Lights") bool bHeadlightsOn=false;
    /** 0 off, 1 left, 2 right, 3 hazards. Server owns this state. */
    UPROPERTY(ReplicatedUsing=OnRep_RoadControls, VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos|Lights") uint8 IndicatorMode=0;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos|Lights") TArray<TObjectPtr<USpotLightComponent>> Headlights;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Chaos|Lights") TArray<TObjectPtr<UPointLightComponent>> IndicatorLights;
    UFUNCTION(BlueprintImplementableEvent, Category="ANOMALIA|Chaos|Engine")
    void OnEngineRunningChanged(bool bRunning);
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Chaos") bool AreWheelVisualsUpright() const;
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Chaos")
    bool HasValidRoadRig() const;
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Chaos")
    bool IsChaosDriveReady() const;
protected:
    virtual void BeginPlay() override;
    virtual bool UsesPhysicsRoadSimulation() const override { return true; }
    virtual bool IsEngineProvidingPower() const override { return bEngineRunning; }
    virtual bool IsDriveReady() const override;
    virtual bool CanDriverExitNow() const override;
    virtual FVector GetDriverExitVelocity() const override;
    virtual float GetExpectedSupportFloorZ() const override;
    virtual void SimulateRoadDrive(float DeltaSeconds,float Throttle,float Steering,float Brake,
        bool bPowered,bool bDriverMissing) override;
private:
    void InputIgnition();
    UFUNCTION(Server, Reliable) void ServerToggleIgnition();
    UFUNCTION() void OnRep_EngineRunning();
    void SetEngineState(bool bRunning);
    UFUNCTION(Server, Reliable) void ServerRoadAction(EAnomaliaRoadAction Action);
    UFUNCTION() void OnRep_RoadControls();
    void SendRoadAction(EAnomaliaRoadAction Action);
    void InputGearUp(); void InputGearDown(); void InputGearMode();
    void InputHandbrakeOn(); void InputHandbrakeOff(); void InputHeadlights();
    void InputIndicatorLeft(); void InputIndicatorRight(); void InputHazardLights();
    void InputDriverDoor();
    void UpdateRoadLights();
    /** Per-instance chassis collision; never modifies a shared source Physics Asset. */
    UPROPERTY(Transient) TObjectPtr<UPhysicsAsset> RuntimeChassisPhysics;
    FTransform ReferenceBoneTransform(FName Bone) const;
    void UpdateWheelVisuals();
    void ApplyRoadRig();
    UFUNCTION() void UpdateCargoPhysicalMass();
    float LastCargoMassKg=-1.f;
};
