#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "AnomaliaPowerUtilityWidget.generated.h"

class AActor;
class AAnomaliaSurvivor;
class UTextBlock;
class UButton;

UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaPowerUtilityWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    void InitializeForDevice(AAnomaliaSurvivor* InPlayer, AActor* InDevice);

    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

    UFUNCTION()
    void ExecutePrimary();

    UFUNCTION()
    void ExecuteSecondary();

    UFUNCTION()
    void ExecuteTertiary();

    UFUNCTION()
    void CloseRequested();

private:
    UPROPERTY()
    TObjectPtr<AAnomaliaSurvivor> Player;

    UPROPERTY()
    TObjectPtr<AActor> Device;

    UPROPERTY()
    TObjectPtr<UTextBlock> StatusText;

    UPROPERTY()
    TObjectPtr<UTextBlock> PrimaryLabel;

    UPROPERTY()
    TObjectPtr<UTextBlock> SecondaryLabel;

    UPROPERTY()
    TObjectPtr<UTextBlock> TertiaryLabel;

    UPROPERTY()
    TObjectPtr<UButton> SecondaryButton;

    UPROPERTY()
    TObjectPtr<UButton> TertiaryButton;

    float RefreshElapsed = 0.f;
    void Refresh();
};
