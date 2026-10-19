#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "AnomaliaVehicleCatalog.h"
#include "AnomaliaVehiclePawn.generated.h"

class USphereComponent;
class UStaticMeshComponent;
class USpringArmComponent;
class UCameraComponent;
class UFloatingPawnMovement;
class AAnomaliaSurvivor;
class AController;

/** Replicated, possessable prototype. Final Chaos wheel/flight/naval physics remain separate work. */
UCLASS(Blueprintable)
class ANOMALIAPRIMEVAL_API AAnomaliaVehiclePawn : public APawn
{
    GENERATED_BODY()

public:
    AAnomaliaVehiclePawn();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Vehicle")
    TObjectPtr<USphereComponent> Collision;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Vehicle")
    TObjectPtr<UStaticMeshComponent> Body;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Vehicle")
    TObjectPtr<USpringArmComponent> CameraBoom;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Vehicle")
    TObjectPtr<UCameraComponent> FollowCamera;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Vehicle")
    TObjectPtr<UFloatingPawnMovement> Movement;

    UPROPERTY(ReplicatedUsing=OnRep_VehicleId, EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Vehicle")
    FName VehicleId = FName(TEXT("car"));

    /** Server-owned fuel percentage. Replicated to passengers/UI and never writable by clients. */
    UPROPERTY(ReplicatedUsing=OnRep_Fuel, VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Vehicle|Fuel")
    float FuelPercent = 100.f;

    /** Fuel use per second at full throttle. Tunable on each vehicle Blueprint. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="ANOMALIA|Vehicle|Fuel", meta=(ClampMin="0.0", ClampMax="10.0"))
    float FuelConsumptionPerSecond = 0.045f;

    /** Server-only per-instance tuning, never set by an untrusted client. */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Vehicle|Tuning")
    bool ConfigureRuntimeTuning(float InitialFuelPercent, float ConsumptionPerSecond, float NewSpeedMultiplier);

    UPROPERTY(ReplicatedUsing=OnRep_Tuning, VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Vehicle|Tuning")
    float SpeedMultiplier = 1.f;

    /** Authoritative refuel; must only be called by trusted server logic. */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Vehicle|Fuel")
    bool RefuelOnServer(float AmountPercent);

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Vehicle|Fuel")
    bool HasFuel() const { return FuelPercent > KINDA_SMALL_NUMBER; }

    UFUNCTION(BlueprintImplementableEvent, Category="ANOMALIA|Vehicle|Fuel")
    void OnFuelChanged(float NewFuelPercent);

    /** Only the server may select a vehicle type. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Vehicle")
    bool ConfigureVehicle(FName NewVehicleId);

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Vehicle")
    FAnomaliaVehicleDefinition GetVehicleDefinition() const;

    /** Called only on server after range and occupancy checks. */
    bool EnterVehicle(AController* DriverController, AAnomaliaSurvivor* Survivor);

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Vehicle")
    bool HasDriver() const;

    UFUNCTION(BlueprintImplementableEvent, Category="ANOMALIA|Vehicle")
    void OnVehicleConfigured(const FAnomaliaVehicleDefinition& Definition);

    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    virtual void BeginPlay() override;

    UFUNCTION()
    void OnRep_VehicleId();

    UFUNCTION()
    void OnRep_Fuel();

    UFUNCTION()
    void OnRep_Tuning();

    UFUNCTION(Server, Unreliable)
    void ServerSetControls(float Forward, float Steering);

    void InputForward(float Value);
    void InputSteering(float Value);
    void InputExitVehicle();

    UFUNCTION(Server, Reliable)
    void ServerExitVehicle();

private:
    TWeakObjectPtr<AAnomaliaSurvivor> ParkedSurvivor;
    float ForwardAxis = 0.f;
    float SteeringAxis = 0.f;
    void ApplyDefinition();
};
