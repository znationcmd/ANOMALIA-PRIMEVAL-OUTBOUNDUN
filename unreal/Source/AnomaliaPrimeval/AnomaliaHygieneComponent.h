#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AnomaliaHygieneComponent.generated.h"

UENUM(BlueprintType)
enum class EAnomaliaSanitaryFixture : uint8 { Toilet, Urinal, Shower, Bathtub, Sink };

USTRUCT(BlueprintType)
struct FAnomaliaHygieneState
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere, BlueprintReadWrite) float Hygiene = 100.f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite) float Bladder = 0.f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite) float Bowel = 0.f;
};

UCLASS(ClassGroup=(Anomalia), meta=(BlueprintSpawnableComponent))
class ANOMALIAPRIMEVAL_API UAnomaliaHygieneComponent : public UActorComponent
{
 GENERATED_BODY()
public:
 UAnomaliaHygieneComponent();
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Anomalia|Hygiene")
 FAnomaliaHygieneState State;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Anomalia|Hygiene")
 bool bPrivacyMode = true;
 UFUNCTION(BlueprintCallable, Category="Anomalia|Hygiene")
 bool UseFixture(EAnomaliaSanitaryFixture Fixture, bool bHasWater, FName& OutAnimation);
 UFUNCTION(BlueprintPure, Category="Anomalia|Hygiene")
 bool NeedsToUrinate() const { return State.Bladder >= 80.f; }
 UFUNCTION(BlueprintPure, Category="Anomalia|Hygiene")
 bool NeedsToDefecate() const { return State.Bowel >= 80.f; }
 UFUNCTION(BlueprintPure, Category="Anomalia|Hygiene")
 bool IsDirty() const { return State.Hygiene < 30.f; }
protected:
 virtual void BeginPlay() override;
 virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
};