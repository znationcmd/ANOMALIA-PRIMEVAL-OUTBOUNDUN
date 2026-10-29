#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "AnomaliaZPrigimaliaLootSubsystem.generated.h"

class FJsonObject;
class AAnomaliaZPrigimaliaLootPickup;
class AAnomaliaZPrigimaliaSurvivor;
class UAnomaliaZPrigimaliaInventoryComponent;

struct FAnomaliaZPrigimaliaItemUseRule
{
    FString Action;
    float Hunger = 0.f, Thirst = 0.f, Health = 0.f;
    FName ReturnItem;
    FString Effect, RestrictedGroup;
    FName RequiredItem;
    bool IsUsable() const { return !Action.IsEmpty() && (Hunger>0.f || Thirst>0.f || Health>0.f || !Effect.IsEmpty() || Action==TEXT("purify")); }
};

struct FAnomaliaZPrigimaliaLootItem
{
    FName Id;
    FString DisplayName, Category;
    TSet<FString> Categories;
    TSet<FString> AllowedPOIs;
    bool IsAllowedAtPOI(const FString& POI) const { return AllowedPOIs.IsEmpty() || AllowedPOIs.Contains(POI); }
    bool MatchesAnyCategory(const TSet<FString>& Allowed) const
    { for (const auto& Name : Categories) if (Allowed.Contains(Name)) return true; return false; }
    int32 MinTier = 1, MaxTier = 5, Quantity = 1, Nominal = 1, Minimum = 0;
    double RestockSeconds = 600, LifetimeSeconds = 3600;
    // Provisional storage rules when a catalogue entry has no physical inventory metadata.
    float WeightKg = 1.f;
    int32 MaxStack = 20;
    FIntPoint Size = FIntPoint(1, 1);
    bool bEnabled = true;
    FAnomaliaZPrigimaliaItemUseRule Use;
};

struct FAnomaliaZPrigimaliaLootSpawn
{
    FString Id;
    FString BuildingType;
    FString POIId;
    FVector Location = FVector::ZeroVector;
    TSet<FString> Categories;
    int32 Tier = 1;
    bool bPlayerStartRelative = false;
};

/** Authority owns selection, replicated pickups and an idempotent inventory/world journal. */
UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaLootSubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual bool DoesSupportWorldType(EWorldType::Type WorldType) const override;
    virtual void Tick(float DeltaTime) override;
    virtual TStatId GetStatId() const override;
    const FAnomaliaZPrigimaliaLootItem* FindItem(FName Id) const { return Items.Find(Id); }
    int32 GetCatalogSize() const { return Items.Num(); }
    TArray<FName> GetItemIds() const { TArray<FName> Ids; Items.GetKeys(Ids); return Ids; }
    bool Configure(const FString& InServerId, const FString& InMapName, FString& Error);
    bool IsReady() const { return bReady; }
    bool HasPendingPlayer(const FString& PlayerId) const;
    bool TryCollect(AAnomaliaZPrigimaliaLootPickup* Pickup, AAnomaliaZPrigimaliaSurvivor* Survivor, const FString& PlayerId, FString& Error);
    // Called by the world tick and by native automation in an isolated world.
    void RefreshLoot();
    FString GetStateId() const { return StateId; }
private:
    friend class FAnomaliaZPrigimaliaPOIResourceTest;
    TMap<FName, FAnomaliaZPrigimaliaLootItem> Items;
    TArray<FAnomaliaZPrigimaliaLootSpawn> Spawns;
    TMap<FString, int32> BuildingTiers;
    TMap<int32, double> Rarity;
    TMap<int32, TSet<FString>> TierCategories;
    TMap<FString, TWeakObjectPtr<AAnomaliaZPrigimaliaLootPickup>> Pickups;
    TSharedPtr<FJsonObject> State;
    TWeakObjectPtr<UAnomaliaZPrigimaliaInventoryComponent> PendingInventory;
    FString ServerId, MapName, StateId;
    bool bConfigured = false, bReady = false;
    double DefaultRestock = 1800;
    float Accumulator = 0;
    bool LoadCatalog(const FString& File, FString& Error, bool Append = false);
    bool RecoverPending(FString& Error);
    bool Persist(FString& Error);
    void SyncActors();
};
