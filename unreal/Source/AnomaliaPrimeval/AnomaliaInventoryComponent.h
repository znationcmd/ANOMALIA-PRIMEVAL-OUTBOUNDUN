#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AnomaliaEconomySubsystem.h"
#include "AnomaliaInventoryComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FAnomaliaInventoryUpdated);
struct FAnomaliaItemUseRule;
class FJsonObject;
class UAnomaliaSharedStorageSubsystem;

USTRUCT(BlueprintType)
struct FAnomaliaInventoryStack
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Inventory")
    int32 StackId = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Inventory")
    FName ItemId;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Inventory")
    int32 Count = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Inventory")
    FName ContainerId = TEXT("pockets");

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Inventory")
    int32 X = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Inventory")
    int32 Y = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Inventory")
    bool bRotated = false;
};

USTRUCT(BlueprintType)
struct FAnomaliaInventoryCompartment
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Inventory")
    FName Id;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Inventory")
    int32 Width = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Inventory")
    int32 Height = 0;

    /** Migration overflow: existing items may be removed, never added through normal placement. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Inventory")
    bool bRecoveryOnly = false;
};

/** Server-authoritative inventory data model. A UMG screen and item-world actors remain separate tasks. */
UCLASS(ClassGroup=(ANOMALIA), BlueprintType, Blueprintable, meta=(BlueprintSpawnableComponent))
class ANOMALIAPRIMEVAL_API UAnomaliaInventoryComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UAnomaliaInventoryComponent();
    /** Current persistence/replication bound. Cell capacity and number of stacks are distinct. */
    static constexpr int32 MaxStacks = 512;

    UPROPERTY(ReplicatedUsing=OnRep_Stacks, VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Inventory")
    TArray<FAnomaliaInventoryStack> Stacks;

    UPROPERTY(ReplicatedUsing=OnRep_Compartments, VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Inventory")
    TArray<FAnomaliaInventoryCompartment> Compartments;

    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="ANOMALIA|Inventory", meta=(ClampMin="0.1", ClampMax="500"))
    float WeightCapacityKg = 14.f;

    UPROPERTY(BlueprintAssignable, Category="ANOMALIA|Inventory")
    FAnomaliaInventoryUpdated OnInventoryUpdated;

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Inventory")
    float GetCurrentWeightKg() const;

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Inventory")
    bool ConfigureCompartment(FName Id, int32 Width, int32 Height);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Inventory")
    bool ConfigureCompartmentFromPreset(FName Id, FName PresetId);

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Inventory")
    int32 GetUsedCells(FName ContainerId) const;

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Inventory")
    FIntPoint GetItemSize(FName ItemId, bool bRotated = false) const;
    bool IsRecoveryContainer(FName ContainerId) const;

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Inventory")
    bool TryAddItem(FName ItemId, int32 Count);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Inventory")
    bool TryRemoveItem(FName ItemId, int32 Count);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Inventory")
    bool TryMoveStack(int32 StackId, FName ContainerId, int32 X, int32 Y, bool bRotate);

    /** Return the selected held stack to the first free compartment slot, without discarding it. */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Inventory")
    bool TryStowStack(int32 StackId);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Inventory")
    bool TrySplitStack(int32 StackId, int32 Count, int32& OutNewStackId);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Inventory")
    bool TryMergeStacks(int32 TargetStackId, int32 SourceStackId);

    /** Save/load only the inventory field while preserving all other player-profile data. */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Inventory|Persistence")
    bool SaveInventoryToPlayerProfile(const FString& ServerId, const FString& PlayerId, FString& OutError);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Inventory|Persistence")
    bool LoadInventoryFromPlayerProfile(const FString& ServerId, const FString& PlayerId, FString& OutError);

    /** Serialize the current inventory into an existing profile without writing it. Server only. */
    bool BuildInventoryProfile(const FString& ServerId, const FString& PlayerId, FString& OutJson, FString& OutError);
    /** Same representation for player, vehicle and world-container inventories. Trusted server API. */
    TSharedPtr<FJsonObject> ExportInventoryObject() const;
    bool LoadInventoryObject(const TSharedPtr<FJsonObject>& Inventory, FString& OutError);
    bool IsPersistenceLocked() const { return bPersistenceLocked || bProfileRecoveryPending; }
    void SetProfileRecoveryPending(bool Pending);

    UPROPERTY(ReplicatedUsing=OnRep_Stacks, BlueprintReadOnly, Category="ANOMALIA|Bank")
    FString BankAccountId;
    UPROPERTY(ReplicatedUsing=OnRep_Stacks, BlueprintReadOnly, Category="ANOMALIA|Bank")
    int64 BankBalanceCents = 0;
    UPROPERTY(ReplicatedUsing=OnRep_Stacks, BlueprintReadOnly, Category="ANOMALIA|Bank")
    int64 NextBankSequence = 1;
    UPROPERTY(ReplicatedUsing=OnRep_Stacks, BlueprintReadOnly, Category="ANOMALIA|Bank")
    bool bBankingAvailable = false;
    UPROPERTY(ReplicatedUsing=OnRep_Stacks, BlueprintReadOnly, Category="ANOMALIA|Bank")
    FString BankMessage;

    void RequestBankOperation(EAnomaliaBankAction Action, FName NoteId = NAME_None, const FString& RecipientId = FString(), int64 AmountCents = 0);
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* TickFunction) override;

    /** Client UI requests; the owning actor's RPC ownership routes them to the server. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Inventory")
    bool RequestMoveStack(int32 StackId, FName ContainerId, int32 X, int32 Y, bool bRotate);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Inventory")
    bool RequestStowStack(int32 StackId);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Inventory")
    bool RequestSplitStack(int32 StackId, int32 Count);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Inventory")
    bool RequestMergeStacks(int32 TargetStackId, int32 SourceStackId);

    FString GetItemDisplayName(FName ItemId) const;
    FString GetUseActionLabel(FName ItemId) const;
    /** Client supplies only the selected stack and its displayed count, never effects or profile identity. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Inventory")
    bool RequestUseStack(int32 StackId, int32 ExpectedCount);
    /** Trusted server entry point. Persists the consumed unit and resulting vitals in one profile write. */
    bool TryUseStack(int32 StackId, int32 ExpectedCount, const FString& ServerId, const FString& PlayerId, FString& OutError);

    UPROPERTY(ReplicatedUsing=OnRep_Stacks, BlueprintReadOnly, Category="ANOMALIA|Inventory")
    FString UseMessage;

    UFUNCTION(BlueprintImplementableEvent, Category="ANOMALIA|Inventory")
    void OnInventoryChanged();

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    UFUNCTION()
    void OnRep_Stacks();

    UFUNCTION()
    void OnRep_Compartments();

    UFUNCTION(Server, Reliable)
    void ServerBankOperation(EAnomaliaBankAction Action, FName NoteId, const FString& RecipientId, int64 AmountCents, int64 Sequence);

    UFUNCTION(Server, Reliable)
    void ServerRequestMoveStack(int32 StackId, FName ContainerId, int32 X, int32 Y, bool bRotate);

    UFUNCTION(Server, Reliable)
    void ServerRequestStowStack(int32 StackId);

    UFUNCTION(Server, Reliable)
    void ServerRequestSplitStack(int32 StackId, int32 Count);

    UFUNCTION(Server, Reliable)
    void ServerRequestMergeStacks(int32 TargetStackId, int32 SourceStackId);

    UFUNCTION(Server, Reliable)
    void ServerRequestUseStack(int32 StackId, int32 ExpectedCount);

private:
    friend class UAnomaliaLootSubsystem;
    friend class UAnomaliaEconomySubsystem;
    friend class UAnomaliaSharedStorageSubsystem;
    bool bPersistenceLocked = false;
    bool bProfileRecoveryPending = false;
    double NextBankRequestTime = 0;
    double NextUseRequestTime = 0;
    FAnomaliaItemUseRule GetUseRule(FName ItemId) const;
    bool UseFromOwningPlayer(int32 StackId, int32 ExpectedCount);
    bool bSuppressNotifications = false;
    int32 NextStackId = 1;
    bool GetItemRules(FName ItemId, float& OutWeightKg, int32& OutMaxStack, FIntPoint& OutSize) const;
    bool CanPlace(const TArray<FAnomaliaInventoryStack>& Candidate, const FAnomaliaInventoryStack& Stack,
        FName ContainerId, int32 X, int32 Y, bool bRotate) const;
    bool FindPlacement(const TArray<FAnomaliaInventoryStack>& Candidate, FAnomaliaInventoryStack& Stack, bool bIncludeRecovery = false) const;
    void Commit(TArray<FAnomaliaInventoryStack>&& Candidate);
};
