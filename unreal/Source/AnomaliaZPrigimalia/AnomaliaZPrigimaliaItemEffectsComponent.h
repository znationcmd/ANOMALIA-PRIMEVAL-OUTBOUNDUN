#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AnomaliaZPrigimaliaItemEffectsComponent.generated.h"
class FJsonObject;

/** Fictional game points, never medical doses or real-world substance simulation. */
USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaItemEffectsState
{
    GENERATED_BODY()
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) float Blood = 100.f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) float Bleeding = 0.f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) float Pain = 0.f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) float Infection = 0.f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) float Poison = 0.f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) float Intoxication = 0.f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) float Dependence = 0.f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) float RemainingSeconds = 0.f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) float Diagnosed = 0.f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) FString ActiveEffect;
};

UCLASS(ClassGroup=(ANOMALIA), meta=(BlueprintSpawnableComponent))
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaItemEffectsComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UAnomaliaZPrigimaliaItemEffectsComponent();
    UPROPERTY(ReplicatedUsing=OnRep_State, BlueprintReadOnly, Category="ANOMALIA|ItemEffects")
    FAnomaliaZPrigimaliaItemEffectsState State;
    static bool IsKnownEffect(const FString& Effect);
    static bool IsValidState(const FAnomaliaZPrigimaliaItemEffectsState& Value);
    static bool ReadState(const TSharedPtr<FJsonObject>& Survival, FAnomaliaZPrigimaliaItemEffectsState& Out, FString& Error);
    static bool WriteState(const TSharedPtr<FJsonObject>& Survival, const FAnomaliaZPrigimaliaItemEffectsState& Value, FString& Error);
    bool PreviewUse(const FString& Effect, FAnomaliaZPrigimaliaItemEffectsState& Out) const;
    bool HasChange(const FAnomaliaZPrigimaliaItemEffectsState& Value) const;
    void ApplyState(const FAnomaliaZPrigimaliaItemEffectsState& Value);
    float GetMovementScale() const;
    float GetStaminaRecoveryScale() const;
    void AdvanceSimulation(float DeltaSeconds);
    /** Trusted server combat hook, not a client RPC. */
    void AddInjury(float Severity);
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* Function) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
protected:
    UFUNCTION() void OnRep_State();
private:
    void ApplyLocalVisuals();
    bool bCapturedVignette = false;
    float BaseVignette = .4f;
};
