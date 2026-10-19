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

    /** Only the server may select a vehicle type. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Vehicle")
    bool ConfigureVehicle(FName NewVehicleId);

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Vehicle")
    FAnomaliaVehicleDefinition GetVehicleDefinition() const;

    UFUNCTION(BlueprintImplementableEvent, Category="ANOMALIA|Vehicle")
    void OnVehicleConfigured(const FAnomaliaVehicleDefinition& Definition);

    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    virtual void BeginPlay() override;

    UFUNCTION()
    void OnRep_VehicleId();

    UFUNCTION(Server, Unreliable)
    void ServerSetControls(float Forward, float Steering);

    void InputForward(float Value);
    void InputSteering(float Value);

private:
    float ForwardAxis = 0.f;
    float SteeringAxis = 0.f;
    void ApplyDefinition();
};
