#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "InputCoreTypes.h"
#include "Components/Button.h"
#include "AnomaliaZPrigimaliaStatusWidget.generated.h"

class AAnomaliaZPrigimaliaSurvivor;
class UTextBlock;
class UVerticalBox;
class UCanvasPanelSlot;

/** Touch actions must not steal keyboard/gamepad navigation focus. */
UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaTouchButton : public UButton
{
    GENERATED_BODY()
public:
    UAnomaliaZPrigimaliaTouchButton(const FObjectInitializer& ObjectInitializer);
};

/** Local status HUD and touch input relay using the existing replicated native survival values. */
UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaStatusWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    void InitializeForSurvivor(AAnomaliaZPrigimaliaSurvivor* InSurvivor);
    void RefreshFromSurvivor();
    FText GetVitalText(FName Id) const;
    FText GetConditionText() const;
    /** Also usable by editor automation to exercise the real touch buttons. */
    void SetTouchControlsEnabled(bool Enabled);
    virtual void NativeConstruct() override;
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeDestruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;
    virtual int32 NativePaint(const FPaintArgs& Args,const FGeometry& Geometry,const FSlateRect& CullingRect,
        FSlateWindowElementList& Elements,int32 LayerId,const FWidgetStyle& Style,bool ParentEnabled) const override;

private:
    TWeakObjectPtr<AAnomaliaZPrigimaliaSurvivor> Survivor;
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
