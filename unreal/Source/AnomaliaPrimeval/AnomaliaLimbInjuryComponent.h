#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AnomaliaLimbInjuryComponent.generated.h"

UENUM(BlueprintType)
enum class EAnomaliaLimb : uint8 { LeftArm, RightArm, LeftLeg, RightLeg };

USTRUCT(BlueprintType)
struct FAnomaliaLimbInjury
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere, BlueprintReadOnly) int32 Severity = 0;
 UPROPERTY(EditAnywhere, BlueprintReadOnly) bool bImmobilized = false;
 UPROPERTY(EditAnywhere, BlueprintReadOnly) float Healing = 0.f;
};

USTRUCT(BlueprintType)
struct FAnomaliaLimbEffects
{
 GENERATED_BODY()
 UPROPERTY(BlueprintReadOnly) float AimSway = 0.f;
 UPROPERTY(BlueprintReadOnly) float ReloadMultiplier = 1.f;
 UPROPERTY(BlueprintReadOnly) float MovementMultiplier = 1.f;
 UPROPERTY(BlueprintReadOnly) bool bCanUseTwoHandedWeapons = true;
 UPROPERTY(BlueprintReadOnly) bool bCanSprint = true;
 UPROPERTY(BlueprintReadOnly) bool bCanClimb = true;
};

UCLASS(ClassGroup=(Anomalia),meta=(BlueprintSpawnableComponent))
class ANOMALIAPRIMEVAL_API UAnomaliaLimbInjuryComponent : public UActorComponent
{
 GENERATED_BODY()
public:
 UAnomaliaLimbInjuryComponent();
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Anomalia|Injuries") TMap<EAnomaliaLimb,FAnomaliaLimbInjury> Injuries;
 UFUNCTION(BlueprintCallable, Category="Anomalia|Injuries") int32 ApplyImpact(EAnomaliaLimb Limb,float Force,float Protection);
 UFUNCTION(BlueprintCallable, Category="Anomalia|Injuries") bool ApplySplint(EAnomaliaLimb Limb);
 UFUNCTION(BlueprintPure, Category="Anomalia|Injuries") FAnomaliaLimbEffects GetEffects() const;
protected:
 virtual void BeginPlay() override;
 virtual void TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction) override;
};