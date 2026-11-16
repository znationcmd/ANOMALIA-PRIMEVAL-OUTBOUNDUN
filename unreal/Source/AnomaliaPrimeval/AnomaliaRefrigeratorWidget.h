#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "AnomaliaRefrigeratorWidget.generated.h"

class AAnomaliaRefrigerator;
class AAnomaliaSurvivor;
class UVerticalBox;
class UTextBlock;
class UButton;
class UAnomaliaRefrigeratorWidget;

UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaFridgeActionRelay : public UObject
{
    GENERATED_BODY()
public:
    UPROPERTY()
    TObjectPtr<UAnomaliaRefrigeratorWidget> Widget;

    FName ItemId;
    bool bDeposit = true;

    UFUNCTION()
    void Execute();
};

/** Native fridge UMG screen for depositing and withdrawing single units. */
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaRefrigeratorWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    void InitializeForFridge(AAnomaliaSurvivor* InPlayer, AAnomaliaRefrigerator* InFridge);
    virtual void NativeConstruct() override;
    virtual void NativeDestruct() override;
    virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

    UFUNCTION()
    void CloseRequested();

private:
    friend class UAnomaliaFridgeActionRelay;

    UPROPERTY()
    TObjectPtr<AAnomaliaSurvivor> Player;

    UPROPERTY()
    TObjectPtr<AAnomaliaRefrigerator> Fridge;

    UPROPERTY()
    TObjectPtr<UVerticalBox> StorageList;

    UPROPERTY()
    TObjectPtr<UVerticalBox> PlayerList;

    UPROPERTY()
    TObjectPtr<UTextBlock> PowerStatus;

    UPROPERTY()
    TArray<TObjectPtr<UAnomaliaFridgeActionRelay>> Relays;

    float RefreshSeconds = 0.f;

    UFUNCTION()
    void RefreshContents();

    void UpdateStatus();
    void AddRow(UVerticalBox* List, FName ItemId, int32 Count, float Freshness01, bool bDeposit);
    void PerformTransfer(FName ItemId, bool bDeposit);
};
