#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AnomaliaInventoryComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FAnomaliaInventoryUpdated);

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
};

/** Server-authoritative inventory data model. A UMG screen and item-world actors remain separate tasks. */
UCLASS(ClassGroup=(ANOMALIA), BlueprintType, Blueprintable, meta=(BlueprintSpawnableComponent))
class ANOMALIAPRIMEVAL_API UAnomaliaInventoryComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UAnomaliaInventoryComponent();

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
    bool TryAddItem(FName ItemId, int32 Count);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Inventory")
    bool TryRemoveItem(FName ItemId, int32 Count);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Inventory")
    bool TryMoveStack(int32 StackId, FName ContainerId, int32 X, int32 Y, bool bRotate);

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
    bool IsPersistenceLocked() const { return bPersistenceLocked; }

    /** Client UI requests; the owning actor's RPC ownership routes them to the server. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Inventory")
    bool RequestMoveStack(int32 StackId, FName ContainerId, int32 X, int32 Y, bool bRotate);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Inventory")
    bool RequestSplitStack(int32 StackId, int32 Count);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Inventory")
    bool RequestMergeStacks(int32 TargetStackId, int32 SourceStackId);

    UFUNCTION(BlueprintImplementableEvent, Category="ANOMALIA|Inventory")
    void OnInventoryChanged();

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    UFUNCTION()
    void OnRep_Stacks();

    UFUNCTION()
    void OnRep_Compartments();

    UFUNCTION(Server, Reliable)
    void ServerRequestMoveStack(int32 StackId, FName ContainerId, int32 X, int32 Y, bool bRotate);

    UFUNCTION(Server, Reliable)
    void ServerRequestSplitStack(int32 StackId, int32 Count);

    UFUNCTION(Server, Reliable)
    void ServerRequestMergeStacks(int32 TargetStackId, int32 SourceStackId);

private:
    friend class UAnomaliaLootSubsystem;
    bool bPersistenceLocked = false;
    bool bSuppressNotifications = false;
    int32 NextStackId = 1;
    bool GetItemRules(FName ItemId, float& OutWeightKg, int32& OutMaxStack, FIntPoint& OutSize) const;
    bool CanPlace(const TArray<FAnomaliaInventoryStack>& Candidate, const FAnomaliaInventoryStack& Stack,
        FName ContainerId, int32 X, int32 Y, bool bRotate) const;
    bool FindPlacement(const TArray<FAnomaliaInventoryStack>& Candidate, FAnomaliaInventoryStack& Stack) const;
    void Commit(TArray<FAnomaliaInventoryStack>&& Candidate);
};
