#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "AnomaliaInventoryWidget.generated.h"

class UAnomaliaInventoryComponent;
class UCanvasPanel;
class UVerticalBox;
class UButton;
class UTextBlock;
class UEditableTextBox;
class UAnomaliaInventoryWidget;
struct FAnomaliaInventoryStack;

UENUM()
enum class EAnomaliaInventoryAction : uint8
{
    MoveToHands,
    SplitHalf,
    Merge,
    Use,
    DepositNote,
    WithdrawNote,
    Stow,
    Rotate
};

UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaInventoryActionRelay : public UObject
{
    GENERATED_BODY()

public:
    UPROPERTY()
    TObjectPtr<UAnomaliaInventoryWidget> TargetWidget;

    EAnomaliaInventoryAction Action = EAnomaliaInventoryAction::MoveToHands;
    int32 StackId = 0;
    int32 Count = 0;
    int32 OtherStackId = 0;

    UFUNCTION()
    void Execute();
};

/** Native UMG inventory panel. It is a functional first interface pass, not a 3D character paper-doll. */
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaInventoryWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    void InitializeForInventory(UAnomaliaInventoryComponent* InInventory);
    virtual void NativeConstruct() override;
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeDestruct() override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
    void FocusFirstAction();
    static constexpr int32 ItemsPerPage=32;
    int32 GetCurrentPage() const { return CurrentPage; }
    int32 GetPageCount() const { return PageCount; }

private:
    friend class UAnomaliaInventoryActionRelay;

    UPROPERTY()
    TObjectPtr<UAnomaliaInventoryComponent> Inventory;

    UPROPERTY()
    TObjectPtr<UCanvasPanel> RootCanvas;

    UPROPERTY()
    TObjectPtr<UVerticalBox> ItemList;

    UPROPERTY()
    TArray<TObjectPtr<UAnomaliaInventoryActionRelay>> ActionRelays;

    UFUNCTION()
    void RefreshInventory();

    void AddStackRow(const FAnomaliaInventoryStack& Stack);
    void BindAction(UButton* Button, EAnomaliaInventoryAction Action, int32 StackId, int32 Count=0, int32 OtherStackId=0);
    void PerformAction(EAnomaliaInventoryAction Action, int32 StackId, int32 Count, int32 OtherStackId);

    UPROPERTY() TObjectPtr<UTextBlock> BankStatus;
    UPROPERTY() TObjectPtr<UTextBlock> UseStatus;
    UPROPERTY() TObjectPtr<UEditableTextBox> BankRecipient;
    UPROPERTY() TObjectPtr<UEditableTextBox> BankAmount;
    UPROPERTY() TObjectPtr<UButton> TransferButton;
    UPROPERTY() TObjectPtr<UButton> CloseButton;
    UPROPERTY() TObjectPtr<UButton> PreviousPageButton;
    UPROPERTY() TObjectPtr<UButton> NextPageButton;
    UPROPERTY() TObjectPtr<UTextBlock> PageStatus;
    int32 CurrentPage=0;
    int32 PageCount=1;
    UFUNCTION() void CloseInventory();
    UFUNCTION() void TransferMoney();
    UFUNCTION() void PreviousPage();
    UFUNCTION() void NextPage();
    void BuildLayout();
};
