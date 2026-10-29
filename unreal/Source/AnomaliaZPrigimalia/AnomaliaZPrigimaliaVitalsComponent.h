#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AnomaliaZPrigimaliaVitalsComponent.generated.h"

class AAnomaliaZPrigimaliaSurvivor;

/**
 * Server-authoritative stamina, sprint and body temperature.
 * The owner may request sprint, never set stamina or temperature.
 * Values are replicated to all clients and Blueprint UI.
 */
UCLASS(ClassGroup=(ANOMALIA), meta=(BlueprintSpawnableComponent))
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaVitalsComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UAnomaliaZPrigimaliaVitalsComponent();

    UPROPERTY(ReplicatedUsing=OnRep_Vitals, BlueprintReadOnly, Category="ANOMALIA|Survival")
    float Stamina = 100.f;

    UPROPERTY(ReplicatedUsing=OnRep_Vitals, BlueprintReadOnly, Category="ANOMALIA|Survival")
    float BodyTemperatureC = 37.f;

    UPROPERTY(ReplicatedUsing=OnRep_Sprinting, BlueprintReadOnly, Category="ANOMALIA|Survival")
    bool bIsSprinting = false;

    /** 0-6 tactical pace. Sprint is still controlled by the existing stamina system. */
    UPROPERTY(ReplicatedUsing=OnRep_PaceStep, BlueprintReadOnly, Category="ANOMALIA|Movement")
    uint8 PaceStep = 4;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="ANOMALIA|Survival", meta=(ClampMin="0.0", ClampMax="40.0"))
    float SprintDrainPerSecond = 12.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="ANOMALIA|Survival", meta=(ClampMin="0.0", ClampMax="40.0"))
    float StaminaRecoveryPerSecond = 8.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="ANOMALIA|Survival", meta=(ClampMin="300.0", ClampMax="1200.0"))
    float SprintWalkSpeed = 680.f;

    UFUNCTION(BlueprintImplementableEvent, Category="ANOMALIA|Survival")
    void OnVitalsChanged();

    /** Called only by owning player input; validates requests on server. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Survival")
    void RequestSprint(bool bWanted);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Movement")
    void RequestPaceStep(uint8 RequestedStep);

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Movement")
    float GetPlannedWalkSpeed() const;

    /** Pure deterministic function shared by gameplay and native automation tests. */
    static float CalculateTacticalSpeed(uint8 Step, float LoadKg, float FatiguePercent, float InjuryScale);

    /** Only trusted server-side lifecycle restoration is allowed. */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Survival")
    void RestoreVitals(float SavedStamina, float SavedTemperatureC);
    void RefreshMovementSpeed() { ApplyMovementSpeed(); }

    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    UFUNCTION()
    void OnRep_Vitals();

    UFUNCTION()
    void OnRep_Sprinting();

    UFUNCTION()
    void OnRep_PaceStep();

    UFUNCTION(Server, Reliable)
    void ServerRequestPaceStep(uint8 RequestedStep);

    UFUNCTION(Server, Reliable)
    void ServerRequestSprint(bool bWanted);

private:
    bool bSprintRequested = false;
    UPROPERTY(ReplicatedUsing=OnRep_PaceStep)
    bool bExhausted = false;
    void ApplyMovementSpeed();
};
