#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "AnomaliaZPrigimaliaEconomySubsystem.generated.h"
class UAnomaliaZPrigimaliaInventoryComponent;
class AAnomaliaZPrigimaliaBankTerminal;
class FJsonObject;

UENUM(BlueprintType)
enum class EAnomaliaZPrigimaliaBankAction : uint8 { Deposit, Withdraw, Transfer };

/** Integer-cent server ledger. Inventory exchanges use a recoverable write-ahead journal. */
UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaEconomySubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual bool DoesSupportWorldType(EWorldType::Type Type) const override;
    virtual TStatId GetStatId() const override;
    virtual void Tick(float DeltaTime) override;
    bool Configure(const FString& InServerId, const FString& InMapName, FString& Error);
    bool HasPendingPlayer(const FString& PlayerId) const;
    bool IsReady() const { return bReady; }
    int64 GetDenomination(FName ItemId) const { const auto* Value = Denominations.Find(ItemId); return Value ? *Value : 0; }
    void SpawnTerminals();
    void RefreshAccount(UAnomaliaZPrigimaliaInventoryComponent* Inventory, const FString& PlayerId);
    // Trusted server call. PlayerId must be resolved from the owning controller, never a client RPC argument.
    bool Execute(UAnomaliaZPrigimaliaInventoryComponent* Inventory, const FString& PlayerId, EAnomaliaZPrigimaliaBankAction Action,
        FName NoteId, const FString& RecipientId, int64 AmountCents, int64 Sequence, FString& Error);
private:
    FString ServerId, MapName;
    bool bReady = false, bConfigured = false, bEnabled = false, bTerminalsSpawned = false;
    float Accumulator = 0;
    int64 MaxBalanceCents = 1000000000000LL;
    TMap<FName, int64> Denominations;
    TArray<FVector> TerminalLocations;
    TArray<TWeakObjectPtr<AAnomaliaZPrigimaliaBankTerminal>> Terminals;
    TSharedPtr<FJsonObject> State;
    TWeakObjectPtr<UAnomaliaZPrigimaliaInventoryComponent> PendingInventory;
    bool Persist(FString& Error);
    bool RecoverPending(FString& Error);
    bool NearTerminal(const UAnomaliaZPrigimaliaInventoryComponent* Inventory) const;
    TSharedPtr<FJsonObject> Account(const FString& Id) const;
};
