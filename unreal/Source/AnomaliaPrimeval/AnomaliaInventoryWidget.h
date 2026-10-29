#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "AnomaliaInventoryWidget.generated.h"

class UAnomaliaInventoryComponent;
class UCanvasPanel;
class UVerticalBox;
class UHorizontalBox;
class UButton;
class UTextBlock;
class UEditableTextBox;
class ACameraActor;
class APlayerController;
class UAnomaliaInventoryWidget;
class AAnomaliaChaosRoadVehicle;
class AAnomaliaLootPickup;
class AAnomaliaDogCompanion;
class AAnomaliaSurvivor;
class ASceneCapture2D;
class UTextureRenderTarget2D;
class UPrimitiveComponent;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class USkeletalMeshComponent;
class UWidget;
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
    StowInContainer,
    CollectNearby,
    DogCommand,
    QuickbarActivate,
    CombineCraft
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
    UFUNCTION() void BeginPointerDrag();
    UFUNCTION() void EndPointerDrag();
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
    virtual void NativeTick(const FGeometry& Geometry,float DeltaTime) override;
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
    void AddAttachmentSlots(FName ParentId);
    void BeginPointerDrag(int32 StackId);
    void DropPointerDraggedStack();
    void RefreshQuickbar();
    UPROPERTY() TMap<TObjectPtr<UCanvasPanel>,FName> GridContainerByPanel;
    UPROPERTY() TMap<TObjectPtr<UCanvasPanel>,float> GridCellSizeByPanel;
    UPROPERTY() TMap<TObjectPtr<UButton>,FName> AttachmentContainerByButton;
    UPROPERTY() TObjectPtr<UHorizontalBox> QuickbarPanel;
    UPROPERTY() TMap<TObjectPtr<UButton>,int32> QuickbarDropTargets;
    int32 PointerDraggedStackId=0;
    FIntPoint PointerGrabOffset=FIntPoint::ZeroValue;
    bool PointerDraggedRotated=false;
    int32 SelectedStackId=0;
    float GridCellSize=36.f;
    bool bBankTab=false;
    void BeginCharacterView();
    void EndCharacterView();
    void RefreshEquipment();
    void AddGridStack(const FAnomaliaInventoryStack& Stack);
    void StyleButton(UButton* Button,bool bSelected=false);
    USkeletalMeshComponent* WornMesh(FName ContainerId) const;
    UTextureRenderTarget2D* GarmentIcon(FName ContainerId);
    UTextureRenderTarget2D* ItemIcon(FName ItemId);
    UTextureRenderTarget2D* QueueIcon(FName Key,UPrimitiveComponent* Source,const FString& Signature);
    UWidget* Thumbnail(UTextureRenderTarget2D* Texture,float Size);
    void CaptureNextIcon();
    void ReleaseIcons();
    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Inventory", meta=(AllowPrivateAccess="true"))
    TMap<FName,TObjectPtr<UTextureRenderTarget2D>> IconTextures;
    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Inventory", meta=(AllowPrivateAccess="true"))
    TMap<FName,TObjectPtr<UMaterialInstanceDynamic>> IconMaterials;
    UPROPERTY() TObjectPtr<UMaterialInterface> IconBaseMaterial;
    UPROPERTY() TMap<FName,TObjectPtr<UPrimitiveComponent>> IconComponents;
    UPROPERTY() TObjectPtr<ASceneCapture2D> IconCapture;
    UPROPERTY() TObjectPtr<AActor> IconPreviewActor;
    TArray<TWeakObjectPtr<AActor>> PreviewHiddenPickups;
    void HidePreviewPickupPrompts();
    TMap<FName,FString> IconSignatures;
    TSet<FName> MissingIconItems;
    TArray<FName> PendingIcons;
    float IconDelay=0;
    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Inventory", meta=(AllowPrivateAccess="true"))
    int32 IconCaptureCount=0;

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
    UPROPERTY() TArray<TObjectPtr<AAnomaliaLootPickup>> NearbyPickups;
    TWeakObjectPtr<AAnomaliaDogCompanion> NearbyDog;
    float ProximityElapsed=0;
    FString ProximitySignature;
    TArray<AAnomaliaLootPickup*> FindNearbyPickups() const;
    void RefreshVehicleProximity();
    void AddVehicleButton(const FString& Label,int32 ServiceAction,int32 StackId=0,int32 Count=0);
    UAnomaliaInventoryActionRelay* FocusedAction() const;
    virtual FReply NativeOnPreviewKeyDown(const FGeometry& Geometry,const FKeyEvent& Event) override;
    virtual FReply NativeOnKeyUp(const FGeometry& Geometry,const FKeyEvent& Event) override;
    int32 DraggedStackId=0,DraggedCount=0;
    bool bDraggingFromVehicle=false;
};





