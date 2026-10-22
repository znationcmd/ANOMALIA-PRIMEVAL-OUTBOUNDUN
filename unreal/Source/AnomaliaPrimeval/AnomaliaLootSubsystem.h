#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "AnomaliaLootSubsystem.generated.h"

class FJsonObject;
class AAnomaliaLootPickup;
class AAnomaliaSurvivor;
class UAnomaliaInventoryComponent;

struct FAnomaliaItemUseRule
{
    FString Action;
    float Hunger = 0.f, Thirst = 0.f, Health = 0.f;
    FName ReturnItem;
    bool IsUsable() const { return !Action.IsEmpty() && (Hunger>0.f || Thirst>0.f || Health>0.f); }
};

struct FAnomaliaLootItem
{
    FName Id;
    FString DisplayName, Category;
    TSet<FString> Categories;
    bool MatchesAnyCategory(const TSet<FString>& Allowed) const
    { for (const auto& Name : Categories) if (Allowed.Contains(Name)) return true; return false; }
    int32 MinTier = 1, MaxTier = 5, Quantity = 1, Nominal = 1, Minimum = 0;
    double RestockSeconds = 600, LifetimeSeconds = 3600;
    // Provisional storage rules when a catalogue entry has no physical inventory metadata.
    float WeightKg = 1.f;
    int32 MaxStack = 20;
    FIntPoint Size = FIntPoint(1, 1);
    bool bEnabled = true;
    FAnomaliaItemUseRule Use;
};

struct FAnomaliaLootSpawn
{
    FString Id;
    FString BuildingType;
    FVector Location = FVector::ZeroVector;
    TSet<FString> Categories;
    int32 Tier = 1;
    bool bPlayerStartRelative = false;
};

/** Authority owns selection, replicated pickups and an idempotent inventory/world journal. */
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaLootSubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual bool DoesSupportWorldType(EWorldType::Type WorldType) const override;
    virtual void Tick(float DeltaTime) override;
    virtual TStatId GetStatId() const override;
    const FAnomaliaLootItem* FindItem(FName Id) const { return Items.Find(Id); }
    int32 GetCatalogSize() const { return Items.Num(); }
    TArray<FName> GetItemIds() const { TArray<FName> Ids; Items.GetKeys(Ids); return Ids; }
    bool Configure(const FString& InServerId, const FString& InMapName, FString& Error);
    bool IsReady() const { return bReady; }
    bool HasPendingPlayer(const FString& PlayerId) const;
    bool TryCollect(AAnomaliaLootPickup* Pickup, AAnomaliaSurvivor* Survivor, const FString& PlayerId, FString& Error);
    // Called by the world tick and by native automation in an isolated world.
    void RefreshLoot();
    FString GetStateId() const { return StateId; }
private:
    TMap<FName, FAnomaliaLootItem> Items;
    TArray<FAnomaliaLootSpawn> Spawns;
    TMap<FString, int32> BuildingTiers;
    TMap<int32, double> Rarity;
    TMap<int32, TSet<FString>> TierCategories;
    TMap<FString, TWeakObjectPtr<AAnomaliaLootPickup>> Pickups;
    TSharedPtr<FJsonObject> State;
    TWeakObjectPtr<UAnomaliaInventoryComponent> PendingInventory;
    FString ServerId, MapName, StateId;
    bool bConfigured = false, bReady = false;
    double DefaultRestock = 1800;
    float Accumulator = 0;
    bool LoadCatalog(const FString& File, FString& Error, bool Append = false);
    bool RecoverPending(FString& Error);
    bool Persist(FString& Error);
    void SyncActors();
};
