#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "InputCoreTypes.h"
#include "AnomaliaStatusWidget.generated.h"

class AAnomaliaSurvivor;
class UTextBlock;
class UVerticalBox;
class UCanvasPanelSlot;

/** Local status HUD and touch input relay using the existing replicated native survival values. */
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaStatusWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    void InitializeForSurvivor(AAnomaliaSurvivor* InSurvivor);
    void RefreshFromSurvivor();
    FText GetVitalText(FName Id) const;
    FText GetConditionText() const;
    /** Also usable by editor automation to exercise the real touch buttons. */
    void SetTouchControlsEnabled(bool Enabled);
    virtual void NativeConstruct() override;
    virtual void NativeDestruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;

private:
    TWeakObjectPtr<AAnomaliaSurvivor> Survivor;
    UPROPERTY() TMap<FName, TObjectPtr<UTextBlock>> VitalLabels;
    UPROPERTY() TObjectPtr<UTextBlock> Conditions;
    UPROPERTY() TObjectPtr<UVerticalBox> TouchControls;
    UPROPERTY() TObjectPtr<UCanvasPanelSlot> StatusFrameSlot;
    float RefreshElapsed = 0.f;
    void BuildLayout();
    void SendLocalInput(FKey Key, EInputEvent Event);
    UFUNCTION() void TouchInteract();
    UFUNCTION() void TouchInventory();
    UFUNCTION() void TouchRest();
    UFUNCTION() void TouchJumpPressed();
    UFUNCTION() void TouchJumpReleased();
    UFUNCTION() void TouchSprintPressed();
    UFUNCTION() void TouchSprintReleased();
};
