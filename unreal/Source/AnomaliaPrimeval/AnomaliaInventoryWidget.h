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
class ACameraActor;
class APlayerController;
class UAnomaliaInventoryWidget;
class AAnomaliaChaosRoadVehicle;
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
    Rotate,
    VehicleService,
    SelectStack,
    CraftRecipe,
    ToggleContainer,
    StowInContainer
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
    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Inventory") TObjectPtr<UButton> Button;

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Inventory")
    void Execute();
};

/** Native inventory: proximity, live equipped survivor and spatial storage grids. */
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaInventoryWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Inventory")
    static UAnomaliaInventoryWidget* CreateForPlayerInventory(APlayerController* Player);
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Inventory") void ShowInventoryTab();
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Inventory") void ShowBankTab();
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Inventory") void ShowCraftTab();
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Inventory")
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

    UPROPERTY() TObjectPtr<UVerticalBox> DetailsList;
    UPROPERTY() TObjectPtr<UVerticalBox> HandsList;
    UPROPERTY() TObjectPtr<UVerticalBox> EquipmentList;
    UPROPERTY() TObjectPtr<UVerticalBox> BankPanel;
    UPROPERTY() TObjectPtr<UVerticalBox> BankWithdrawals;
    UPROPERTY() TObjectPtr<UVerticalBox> StoragePanel;
    UPROPERTY() TObjectPtr<UCanvasPanel> ActiveGrid;
    UPROPERTY() TObjectPtr<ACameraActor> PreviewCamera;
    UPROPERTY() TObjectPtr<AActor> PreviousViewTarget;
    UPROPERTY() TObjectPtr<UTextBlock> WeightStatus;
    UPROPERTY() TObjectPtr<UButton> InventoryTab;
    UPROPERTY() TObjectPtr<UButton> BankTab;
    UPROPERTY() TObjectPtr<UButton> CraftTab;
    UPROPERTY() TObjectPtr<UVerticalBox> CraftPanel;
    UPROPERTY() TObjectPtr<UVerticalBox> CraftList;
    UPROPERTY() TObjectPtr<UTextBlock> MoneyStatus;
    UPROPERTY() TObjectPtr<UTextBlock> BankBalanceStatus;
    TMap<FName,bool> ExpandedContainers;
    void RefreshCrafting();
    FString ContainerLabel(FName Id) const;
    int32 SelectedStackId=0;
    float GridCellSize=36.f;
    bool bBankTab=false;
    void BeginCharacterView();
    void EndCharacterView();
    void RefreshEquipment();
    void AddGridStack(const FAnomaliaInventoryStack& Stack);
    void StyleButton(UButton* Button,bool bSelected=false);

    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Inventory", meta=(AllowPrivateAccess="true"))
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
    UPROPERTY() TObjectPtr<UVerticalBox> ProximityList;
    UPROPERTY() TObjectPtr<AAnomaliaChaosRoadVehicle> NearbyVehicle;
    void RefreshVehicleProximity();
    void AddVehicleButton(const FString& Label,int32 ServiceAction,int32 StackId=0,int32 Count=0);
    UAnomaliaInventoryActionRelay* FocusedAction() const;
    virtual FReply NativeOnPreviewKeyDown(const FGeometry& Geometry,const FKeyEvent& Event) override;
    virtual FReply NativeOnKeyUp(const FGeometry& Geometry,const FKeyEvent& Event) override;
    int32 DraggedStackId=0,DraggedCount=0;
    bool bDraggingFromVehicle=false;
};


