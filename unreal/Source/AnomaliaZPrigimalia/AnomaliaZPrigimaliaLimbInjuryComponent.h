#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AnomaliaZPrigimaliaLimbInjuryComponent.generated.h"

UENUM(BlueprintType)
enum class EAnomaliaZPrigimaliaLimb : uint8 { LeftArm, RightArm, LeftLeg, RightLeg };

USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaLimbInjury
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere, BlueprintReadOnly) int32 Severity = 0;
 UPROPERTY(EditAnywhere, BlueprintReadOnly) bool bImmobilized = false;
 UPROPERTY(EditAnywhere, BlueprintReadOnly) float Healing = 0.f;
};

USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaLimbEffects
{
 GENERATED_BODY()
 UPROPERTY(BlueprintReadOnly) float AimSway = 0.f;
 UPROPERTY(BlueprintReadOnly) float ReloadMultiplier = 1.f;
 UPROPERTY(BlueprintReadOnly) float MovementMultiplier = 1.f;
 UPROPERTY(BlueprintReadOnly) bool bCanUseTwoHandedWeapons = true;
 UPROPERTY(BlueprintReadOnly) bool bCanSprint = true;
 UPROPERTY(BlueprintReadOnly) bool bCanClimb = true;
};

UCLASS(ClassGroup=(AnomaliaZPrigimalia),meta=(BlueprintSpawnableComponent))
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaLimbInjuryComponent : public UActorComponent
{
 GENERATED_BODY()
public:
 UAnomaliaZPrigimaliaLimbInjuryComponent();
 UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="AnomaliaZPrigimalia|Injuries") TMap<EAnomaliaZPrigimaliaLimb,FAnomaliaZPrigimaliaLimbInjury> Injuries;
 UFUNCTION(BlueprintCallable, Category="AnomaliaZPrigimalia|Injuries") int32 ApplyImpact(EAnomaliaZPrigimaliaLimb Limb,float Force,float Protection);
 UFUNCTION(BlueprintCallable, Category="AnomaliaZPrigimalia|Injuries") bool ApplySplint(EAnomaliaZPrigimaliaLimb Limb);
 UFUNCTION(BlueprintPure, Category="AnomaliaZPrigimalia|Injuries") FAnomaliaZPrigimaliaLimbEffects GetEffects() const;
protected:
 virtual void BeginPlay() override;
 virtual void TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction) override;
};