#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaSurvivor.h"
#include "../AnomaliaInventoryComponent.h"
#include "../AnomaliaConfigLibrary.h"
#include "../AnomaliaLootSubsystem.h"
#include "../AnomaliaItemEffectsComponent.h"
#include "Engine/World.h"
#include "Misc/Guid.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaItemUseTest,"Anomalia.Native.ItemConsumption",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaItemUseTest::RunTest(const FString& Parameters)
{
    const FString Server=TEXT("item-use-test-")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    auto* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("Isolated world"),World)) return false;
    auto* Survivor=World->SpawnActor<AAnomaliaSurvivor>();
    auto* Inventory=Survivor->InventoryComponent.Get();
    FString Error,Raw;
    TestTrue(TEXT("Seed profile extension"),UAnomaliaConfigLibrary::SavePlayerProfile(Server,TEXT("food"),TEXT("{\"extension\":{\"keep\":true}}"),Error));
    Survivor->RestoreSurvival(10,20,30);
    if(!TestTrue(TEXT("Add two real catalogue cans"),Inventory->TryAddItem(TEXT("canned_beans"),2)))
    { World->DestroyWorld(false);return false; }
    const int32 Id=Inventory->Stacks[0].StackId;
    TestFalse(TEXT("Stale displayed count rejected"),Inventory->TryUseStack(Id,3,Server,TEXT("food"),Error));
    TestTrue(TEXT("Consume one can"),Inventory->TryUseStack(Id,2,Server,TEXT("food"),Error));
    TestEqual(TEXT("Exactly one can remains"),Inventory->Stacks[0].Count,1);
    TestEqual(TEXT("Server rule restores hunger"),Survivor->Hunger,40.f);
    TestEqual(TEXT("Food does not heal unrelated injury"),Survivor->Health,30.f);
    TestFalse(TEXT("Replayed original request rejected"),Inventory->TryUseStack(Id,2,Server,TEXT("food"),Error));
    TestTrue(TEXT("Read combined durable result"),UAnomaliaConfigLibrary::LoadPlayerProfile(Server,TEXT("food"),Raw,Error));
    TSharedPtr<FJsonObject> Saved;
    TestTrue(TEXT("Profile parses"),FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw),Saved));
    if(Saved.IsValid())
    {
        TestTrue(TEXT("Unknown extension preserved"),Saved->HasField(TEXT("extension")));
        TestEqual(TEXT("Vitals and inventory share the same saved result"),Saved->GetObjectField(TEXT("survival"))->GetNumberField(TEXT("hunger")),40.);
        TestEqual(TEXT("Saved stack decremented once"),Saved->GetObjectField(TEXT("inventory"))->GetArrayField(TEXT("stacks"))[0]->AsObject()->GetNumberField(TEXT("count")),1.);
    }
    Survivor->RestoreSurvival(100,20,30);
    TestFalse(TEXT("Full hunger does not waste food"),Inventory->TryUseStack(Id,1,Server,TEXT("food"),Error));
    Survivor->RestoreSurvival(10,20,30);
    TestFalse(TEXT("Invalid profile scope rolls back before benefit"),Inventory->TryUseStack(Id,1,TEXT("../invalid"),TEXT("food"),Error));
    TestEqual(TEXT("Failed write preserves count"),Inventory->Stacks[0].Count,1);
    TestEqual(TEXT("Failed write grants no benefit"),Survivor->Hunger,10.f);
    Inventory->SetProfileRecoveryPending(true);
    TestFalse(TEXT("Recovery lock blocks consumption"),Inventory->TryUseStack(Id,1,Server,TEXT("food"),Error));
    Inventory->SetProfileRecoveryPending(false);
    TestTrue(TEXT("Seed malformed survival without overwriting inventory manually"),UAnomaliaConfigLibrary::SavePlayerProfile(Server,TEXT("malformed"),TEXT("{\"survival\":\"preserve\",\"extension\":true}"),Error));
    TestFalse(TEXT("Malformed existing survival preserved"),Inventory->TryUseStack(Id,1,Server,TEXT("malformed"),Error));
    TestEqual(TEXT("Malformed profile does not consume can"),Inventory->Stacks[0].Count,1);

    auto* Drinker=World->SpawnActor<AAnomaliaSurvivor>();auto* Bottles=Drinker->InventoryComponent.Get();
    Drinker->RestoreSurvival(100,40,70);
    // ConfigureCompartment intentionally refuses shrinking an existing compartment.
    // This isolated empty fixture starts without the survivor's default pockets.
    Bottles->Compartments.Reset();
    TestTrue(TEXT("Single-bottle-sized container"),Bottles->ConfigureCompartment(TEXT("pockets"),1,3));
    if(!TestTrue(TEXT("Two bottles share one occupied footprint"),Bottles->TryAddItem(TEXT("water_bottle"),2)))
    { World->DestroyWorld(false);return false; }
    const int32 BottleId=Bottles->Stacks[0].StackId;
    TestFalse(TEXT("No room for returned bottle keeps source intact"),Bottles->TryUseStack(BottleId,2,Server,TEXT("water"),Error));
    TestEqual(TEXT("No room means no free hydration"),Drinker->Thirst,40.f);
    TestEqual(TEXT("Both bottles remain"),Bottles->Stacks[0].Count,2);
    TestTrue(TEXT("Free the source slot after single use"),Bottles->TryRemoveItem(TEXT("water_bottle"),1));
    TestTrue(TEXT("Drink and return empty container"),Bottles->TryUseStack(BottleId,1,Server,TEXT("water"),Error));
    TestEqual(TEXT("Hydration applied"),Drinker->Thirst,85.f);
    TestEqual(TEXT("Empty bottle retained"),Bottles->Stacks[0].ItemId,FName(TEXT("empty_water_bottle")));
    TestTrue(TEXT("Empty bottle has its own lower mass"),FMath::IsNearlyEqual(Bottles->GetCurrentWeightKg(),.05f));
    auto* Reloaded=World->SpawnActor<AAnomaliaSurvivor>();
    TestTrue(TEXT("Reload consumed bottle result"),Reloaded->InventoryComponent->LoadInventoryFromPlayerProfile(Server,TEXT("water"),Error));
    TestTrue(TEXT("Restart restores empty container, not full water"),Reloaded->InventoryComponent->Stacks.ContainsByPredicate([](const auto& S){return S.ItemId==TEXT("empty_water_bottle");}));

    // A filled pocket must not lose or duplicate the item held while making space.
    auto* Carrier=World->SpawnActor<AAnomaliaSurvivor>();
    auto* Storage=Carrier->InventoryComponent.Get();
    Storage->Compartments.Reset();
    TestTrue(TEXT("Limit storage to one bottle-sized slot"),Storage->ConfigureCompartment(TEXT("pockets"),1,3));
    if(!TestTrue(TEXT("Bottle available to hold"),Storage->TryAddItem(TEXT("water_bottle"),1)))
    { World->DestroyWorld(false);return false; }
    const int32 HeldId=Storage->Stacks[0].StackId;
    TestTrue(TEXT("Move bottle into hands"),Storage->RequestMoveStack(HeldId,TEXT("hands"),0,0,false));
    TestTrue(TEXT("Fill vacated footprint"),Storage->TryAddItem(TEXT("empty_water_bottle"),1));
    TestFalse(TEXT("Full storage refuses stow"),Storage->RequestStowStack(HeldId));
    TestTrue(TEXT("Rejected stow retains held bottle"),Storage->Stacks.ContainsByPredicate([&](const auto& S){return S.StackId==HeldId && S.ContainerId==TEXT("hands") && S.Count==1;}));
    TestTrue(TEXT("Make space without changing held item"),Storage->TryRemoveItem(TEXT("empty_water_bottle"),1));
    Storage->SetProfileRecoveryPending(true);
    TestFalse(TEXT("Recovery lock also protects storage transfers"),Storage->RequestStowStack(HeldId));
    Storage->SetProfileRecoveryPending(false);
    TestTrue(TEXT("Stow once space and recovery permit"),Storage->RequestStowStack(HeldId));
    TestFalse(TEXT("Repeated stow cannot duplicate item"),Storage->RequestStowStack(HeldId));
    TestEqual(TEXT("Exactly one item remains after storage transfers"),Storage->Stacks.Num(),1);

    auto* Patient=World->SpawnActor<AAnomaliaSurvivor>();auto* Medical=Patient->InventoryComponent.Get();
    Patient->RestoreSurvival(100,100,70);
    if(!TestTrue(TEXT("Medical supply available"),Medical->TryAddItem(TEXT("sterile_bandage"),1)))
    { World->DestroyWorld(false);return false; }
    TestTrue(TEXT("Simple game care consumes bandage"),Medical->TryUseStack(Medical->Stacks[0].StackId,1,Server,TEXT("medical"),Error));
    TestEqual(TEXT("Bounded game health effect"),Patient->Health,85.f);
    TestTrue(TEXT("Spent bandage removed"),Medical->Stacks.IsEmpty());
    TestTrue(TEXT("Weapon can be carried"),Medical->TryAddItem(TEXT("m4a1"),1));
    TestFalse(TEXT("Weapon is never treated as food or medicine"),Medical->TryUseStack(Medical->Stacks[0].StackId,1,Server,TEXT("medical"),Error));
    const auto* Loot=World->GetSubsystem<UAnomaliaLootSubsystem>();
    int32 TestedUses=0;
    if(Loot) for(const FName ItemId:Loot->GetItemIds())
    {
        const auto* Definition=Loot->FindItem(ItemId);
        if(!Definition || !Definition->Use.IsUsable()) continue;
        auto* Sample=World->SpawnActor<AAnomaliaSurvivor>();
        Sample->RestoreSurvival(10,10,10);
        FAnomaliaItemEffectsState Conditions;
        Conditions.Blood=50;Conditions.Bleeding=40;Conditions.Pain=50;Conditions.Infection=50;Conditions.Poison=50;
        Sample->ItemEffectsComponent->ApplyState(Conditions);
        auto* Items=Sample->InventoryComponent.Get();
        const bool Added=Items->TryAddItem(ItemId,1);
        TestTrue(*FString::Printf(TEXT("Consumable enters inventory: %s"),*ItemId.ToString()),Added);
        if(Added)
        {
            if(!Definition->Use.RequiredItem.IsNone())
                TestTrue(TEXT("Required tool available"),Items->TryAddItem(Definition->Use.RequiredItem,1));
            const bool Used=Items->TryUseStack(Items->Stacks[0].StackId,1,Server,ItemId.ToString(),Error);
            TestTrue(*FString::Printf(TEXT("Actual use and profile write: %s"),*ItemId.ToString()),Used);
            if(Used)
            {
                TestEqual(TEXT("Catalogue hunger gain applied"),Sample->Hunger,10.f+Definition->Use.Hunger);
                TestEqual(TEXT("Catalogue thirst gain applied"),Sample->Thirst,10.f+Definition->Use.Thirst);
                TestEqual(TEXT("Catalogue care gain applied"),Sample->Health,10.f+Definition->Use.Health);
                TestFalse(TEXT("Full source item consumed exactly once"),Items->Stacks.ContainsByPredicate([&](const auto& S){return S.ItemId==ItemId;}));
                if(!Definition->Use.ReturnItem.IsNone())
                    TestTrue(TEXT("Specified empty container returned"),Items->Stacks.ContainsByPredicate([&](const auto& S){return S.ItemId==Definition->Use.ReturnItem && S.Count==1;}));
            }
        }
        ++TestedUses;
    }
    TestEqual(TEXT("Every configured catalogue consumable tested"),TestedUses,98);
    World->DestroyWorld(false);
    return true;
}
#endif
