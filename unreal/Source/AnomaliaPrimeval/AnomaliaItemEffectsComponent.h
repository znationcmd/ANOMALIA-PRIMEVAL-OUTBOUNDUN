#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AnomaliaItemEffectsComponent.generated.h"
class FJsonObject;

/** Fictional game points, never medical doses or real-world substance simulation. */
USTRUCT(BlueprintType)
struct FAnomaliaItemEffectsState
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
class ANOMALIAPRIMEVAL_API UAnomaliaItemEffectsComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UAnomaliaItemEffectsComponent();
    UPROPERTY(ReplicatedUsing=OnRep_State, BlueprintReadOnly, Category="ANOMALIA|ItemEffects")
    FAnomaliaItemEffectsState State;
    static bool IsKnownEffect(const FString& Effect);
    static bool IsValidState(const FAnomaliaItemEffectsState& Value);
    static bool ReadState(const TSharedPtr<FJsonObject>& Survival, FAnomaliaItemEffectsState& Out, FString& Error);
    static bool WriteState(const TSharedPtr<FJsonObject>& Survival, const FAnomaliaItemEffectsState& Value, FString& Error);
    bool PreviewUse(const FString& Effect, FAnomaliaItemEffectsState& Out) const;
    bool HasChange(const FAnomaliaItemEffectsState& Value) const;
    void ApplyState(const FAnomaliaItemEffectsState& Value);
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
