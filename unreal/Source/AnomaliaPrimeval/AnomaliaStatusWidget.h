#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "AnomaliaStatusWidget.generated.h"

class AAnomaliaSurvivor;
class UTextBlock;

/** Local read-only HUD using the existing replicated native survival values. */
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaStatusWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    void InitializeForSurvivor(AAnomaliaSurvivor* InSurvivor);
    void RefreshFromSurvivor();
    FText GetVitalText(FName Id) const;
    FText GetConditionText() const;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;

private:
    TWeakObjectPtr<AAnomaliaSurvivor> Survivor;
    UPROPERTY() TMap<FName, TObjectPtr<UTextBlock>> VitalLabels;
    UPROPERTY() TObjectPtr<UTextBlock> Conditions;
    float RefreshElapsed = 0.f;
    void BuildLayout();
};
