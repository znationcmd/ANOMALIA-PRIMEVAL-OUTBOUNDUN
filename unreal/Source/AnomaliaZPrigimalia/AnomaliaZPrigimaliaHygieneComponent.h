#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AnomaliaZPrigimaliaHygieneComponent.generated.h"

UENUM(BlueprintType)
enum class EAnomaliaZPrigimaliaSanitaryFixture : uint8 { Toilet, Urinal, Shower, Bathtub, Sink };

USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaHygieneState
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere, BlueprintReadWrite) float Hygiene = 100.f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite) float Bladder = 0.f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite) float Bowel = 0.f;
};

UCLASS(ClassGroup=(AnomaliaZPrigimalia), meta=(BlueprintSpawnableComponent))
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaHygieneComponent : public UActorComponent
{
 GENERATED_BODY()
public:
 UAnomaliaZPrigimaliaHygieneComponent();
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="AnomaliaZPrigimalia|Hygiene")
 FAnomaliaZPrigimaliaHygieneState State;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="AnomaliaZPrigimalia|Hygiene")
 bool bPrivacyMode = true;
 UFUNCTION(BlueprintCallable, Category="AnomaliaZPrigimalia|Hygiene")
 bool UseFixture(EAnomaliaZPrigimaliaSanitaryFixture Fixture, bool bHasWater, FName& OutAnimation);
 UFUNCTION(BlueprintPure, Category="AnomaliaZPrigimalia|Hygiene")
 bool NeedsToUrinate() const { return State.Bladder >= 80.f; }
 UFUNCTION(BlueprintPure, Category="AnomaliaZPrigimalia|Hygiene")
 bool NeedsToDefecate() const { return State.Bowel >= 80.f; }
 UFUNCTION(BlueprintPure, Category="AnomaliaZPrigimalia|Hygiene")
 bool IsDirty() const { return State.Hygiene < 30.f; }
protected:
 virtual void BeginPlay() override;
 virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
};