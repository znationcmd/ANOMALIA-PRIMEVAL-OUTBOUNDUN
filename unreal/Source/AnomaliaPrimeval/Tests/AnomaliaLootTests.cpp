#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaLootSubsystem.h"
#include "../AnomaliaLootPickup.h"
#include "../AnomaliaSurvivor.h"
#include "../AnomaliaInventoryComponent.h"
#include "../AnomaliaConfigLibrary.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/Guid.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace
{
    FString Scope() { return TEXT("loot-test-")+FGuid::NewGuid().ToString(EGuidFormats::Digits); }
    AAnomaliaLootPickup* Food(UWorld* World)
    {
        for (TActorIterator<AAnomaliaLootPickup> It(World); It; ++It)
            if (It->SpawnId == TEXT("review-house-food") && !It->IsActorBeingDestroyed()) return *It;
        return nullptr;
    }
    int32 Units(const UAnomaliaInventoryComponent* Inventory)
    {
        int32 Total = 0;
        for (const auto& Stack : Inventory->Stacks) Total += Stack.Count;
        return Total;
    }
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaLootCatalogTest, "Anomalia.Native.LootCatalog",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaLootCatalogTest::RunTest(const FString& Parameters)
{
    auto* World = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("Isolated world"), World)) return false;
    auto* Loot = World->GetSubsystem<UAnomaliaLootSubsystem>();
    if (!TestNotNull(TEXT("Native loot subsystem"), Loot)) { World->DestroyWorld(false); return false; }
    TestEqual(TEXT("All source catalogue entries and three empty containers available to native inventory"), Loot->GetCatalogSize(), 262);
    const auto* Battery = Loot->FindItem(TEXT("car_battery"));
    TestTrue(TEXT("Existing battery retains both source categories without duplication"), Battery &&
        Battery->Categories.Contains(TEXT("power_lighting")) && Battery->Categories.Contains(TEXT("vehicle_engine_parts")));
    auto* Survivor = World->SpawnActor<AAnomaliaSurvivor>();
    for (const FName Id : Loot->GetItemIds())
    {
        TestNotNull(*FString::Printf(TEXT("Catalogue ID resolves: %s"), *Id.ToString()), Loot->FindItem(Id));
        TestTrue(*FString::Printf(TEXT("Catalogue item enters inventory: %s"), *Id.ToString()), Survivor->InventoryComponent->TryAddItem(Id, 1));
        TestTrue(*FString::Printf(TEXT("Catalogue item removes cleanly: %s"), *Id.ToString()), Survivor->InventoryComponent->TryRemoveItem(Id, 1));
    }
    auto* Inventory=Survivor->InventoryComponent.Get();
    TestTrue(TEXT("Added metal resource is accepted by the real inventory"),Inventory->TryAddItem(TEXT("metal_ingot"),2));
    TestTrue(TEXT("Added wool resource is accepted by the real inventory"),Inventory->TryAddItem(TEXT("wool"),4));
    TestTrue(TEXT("Added resources use their catalogue storage mass"),FMath::IsNearlyEqual(Inventory->GetCurrentWeightKg(),3.2f));
    Inventory->WeightCapacityKg=3.2f;
    TestFalse(TEXT("Resource weight prevents an overweight addition"),Inventory->TryAddItem(TEXT("wool"),1));
    TestEqual(TEXT("Rejected resource addition preserves the six existing units"),Units(Inventory),6);
    Inventory->WeightCapacityKg=14.f;
    TestFalse(TEXT("Unlisted item cannot enter inventory"), Survivor->InventoryComponent->TryAddItem(TEXT("not-authorized-item"), 1));
    World->DestroyWorld(false);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaLootTransactionTest, "Anomalia.Native.LootTransactions",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaLootTransactionTest::RunTest(const FString& Parameters)
{
    const FString Server = Scope(); FString Error;
    auto* World = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("Isolated world"), World)) return false;
    auto* Loot = World->GetSubsystem<UAnomaliaLootSubsystem>();
    if (!Loot || !TestTrue(TEXT("Load shipped catalogue tiers and layout"), Loot->Configure(Server, TEXT("ANOMALIA_LootReview_v1"), Error)))
    { AddError(Error); World->DestroyWorld(false); return false; }
    Loot->RefreshLoot();
    auto* Pickup = Food(World);
    if (!TestNotNull(TEXT("Real native pickup spawned from tier-one catalogue"), Pickup)) { World->DestroyWorld(false); return false; }
    auto* Survivor = World->SpawnActor<AAnomaliaSurvivor>();
    Survivor->SetActorLocation(FVector(-1000,0,30));
    TestFalse(TEXT("Distant pickup denied"), Loot->TryCollect(Pickup, Survivor, TEXT("player-a"), Error));
    TestEqual(TEXT("Denied request adds no resources"), Units(Survivor->InventoryComponent), 0);
    Survivor->SetActorLocation(FVector(100,0,30));
    Survivor->InventoryComponent->WeightCapacityKg = .001f;
    TestFalse(TEXT("Full inventory leaves pickup available"), Loot->TryCollect(Pickup, Survivor, TEXT("player-a"), Error));
    TestFalse(TEXT("Failed capacity check does not consume pickup"), Pickup->IsActorBeingDestroyed());
    Survivor->InventoryComponent->WeightCapacityKg = 14.f;
    FString Raw;
    TestTrue(TEXT("Seed unrelated profile fields"), UAnomaliaConfigLibrary::SavePlayerProfile(Server, TEXT("player-a"), TEXT("{\"extension\":{\"keep\":true}}"), Error));
    TestFalse(TEXT("Invalid player scope denied"), Loot->TryCollect(Pickup, Survivor, TEXT("../player"), Error));
    TestTrue(TEXT("Valid pickup reaches inventory and durable profile"), Loot->TryCollect(Pickup, Survivor, TEXT("player-a"), Error));
    TestEqual(TEXT("Exactly one unit added"), Units(Survivor->InventoryComponent), 1);
    TestFalse(TEXT("Same pickup cannot be replayed"), Loot->TryCollect(Pickup, Survivor, TEXT("player-a"), Error));
    TestEqual(TEXT("Replay does not duplicate resources"), Units(Survivor->InventoryComponent), 1);
    TestTrue(TEXT("Transaction finishes unlocked"), !Survivor->InventoryComponent->IsPersistenceLocked());
    TestTrue(TEXT("Profile exists after pickup"), UAnomaliaConfigLibrary::LoadPlayerProfile(Server, TEXT("player-a"), Raw, Error));
    TSharedPtr<FJsonObject> Profile;
    TestTrue(TEXT("Saved profile parses"), FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw), Profile));
    if (Profile.IsValid()) TestTrue(TEXT("Unrelated profile extension preserved"), Profile->HasField(TEXT("extension")));
    const FString Key = Loot->GetStateId();
    World->DestroyWorld(false);
    World = UWorld::CreateWorld(EWorldType::Game, false);
    Loot = World->GetSubsystem<UAnomaliaLootSubsystem>();
    TestTrue(TEXT("Reload same server and map"), Loot->Configure(Server, TEXT("ANOMALIA_LootReview_v1"), Error));
    Loot->RefreshLoot();
    TestNull(TEXT("Consumed point remains absent across restart before restock"), Food(World));
    Survivor = World->SpawnActor<AAnomaliaSurvivor>();
    TestTrue(TEXT("Existing inventory loader reads pickup result"), Survivor->InventoryComponent->LoadInventoryFromPlayerProfile(Server, TEXT("player-a"), Error));
    TestEqual(TEXT("Saved resources restored once"), Units(Survivor->InventoryComponent), 1);
    TestTrue(TEXT("Different server remains isolated"), !UAnomaliaConfigLibrary::LoadWorldState(Server+TEXT("-other"), Key, Raw, Error));
    World->DestroyWorld(false);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaLootRecoveryTest, "Anomalia.Native.LootJournalRecovery",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaLootRecoveryTest::RunTest(const FString& Parameters)
{
    const FString Server = Scope(); FString Error, Raw;
    auto* World = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("Isolated world"), World)) return false;
    auto* Loot = World->GetSubsystem<UAnomaliaLootSubsystem>();
    if (!Loot || !TestTrue(TEXT("Initialize isolated journal"), Loot->Configure(Server, TEXT("ANOMALIA_LootReview_v1"), Error)))
    { World->DestroyWorld(false); return false; }
    const FString Key = Loot->GetStateId();
    UAnomaliaConfigLibrary::LoadWorldState(Server, Key, Raw, Error);
    TSharedPtr<FJsonObject> State;
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw), State)) { World->DestroyWorld(false); return false; }
    auto* Survivor = World->SpawnActor<AAnomaliaSurvivor>();
    Survivor->InventoryComponent->TryAddItem(TEXT("m4a1"), 1);
    FString After;
    Survivor->InventoryComponent->BuildInventoryProfile(Server, TEXT("player-a"), After, Error);
    auto Pending = MakeShared<FJsonObject>();
    Pending->SetStringField(TEXT("playerId"), TEXT("player-a")); Pending->SetStringField(TEXT("profileAfter"), After);
    State->SetObjectField(TEXT("pending"), Pending);
    Raw.Empty(); FJsonSerializer::Serialize(State.ToSharedRef(), TJsonWriterFactory<>::Create(&Raw));
    TestTrue(TEXT("Persist simulated crash after intent but before profile commit"), UAnomaliaConfigLibrary::SaveWorldState(Server, Key, Raw, Error));
    World->DestroyWorld(false);
    for (int32 Attempt = 0; Attempt < 2; ++Attempt)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        Loot = World->GetSubsystem<UAnomaliaLootSubsystem>();
        TestTrue(TEXT("Restart recovers durable intent"), Loot->Configure(Server, TEXT("ANOMALIA_LootReview_v1"), Error));
        TestFalse(TEXT("Pending player lock cleared only after both writes"), Loot->HasPendingPlayer(TEXT("player-a")));
        Survivor = World->SpawnActor<AAnomaliaSurvivor>();
        TestTrue(TEXT("Recovered profile load"), Survivor->InventoryComponent->LoadInventoryFromPlayerProfile(Server, TEXT("player-a"), Error));
        TestEqual(TEXT("Recovery and repeated restart do not add another unit"), Units(Survivor->InventoryComponent), 1);
        World->DestroyWorld(false);
    }
    TestFalse(TEXT("World traversal rejected"), UAnomaliaConfigLibrary::SaveWorldState(TEXT("../escape"), Key, TEXT("{}"), Error));
    return true;
}
#endif
