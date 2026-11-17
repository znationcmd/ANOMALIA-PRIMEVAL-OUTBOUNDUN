#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaZPrigimaliaInventoryComponent.h"
#include "../Survival/AnomaliaZPrigimaliaWaterSource.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaZPrigimaliaKitchenRulesTest,
    "AnomaliaZPrigimalia.Native.KitchenRules",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaZPrigimaliaKitchenRulesTest::RunTest(const FString& Parameters)
{
    using Kitchen=UAnomaliaZPrigimaliaInventoryComponent;
    TestTrue(TEXT("Bouteille vide remplissable"),Kitchen::IsFillableContainer(TEXT("empty_water_bottle")));
    TestTrue(TEXT("Gourde vide remplissable"),Kitchen::IsFillableContainer(TEXT("empty_military_canteen")));
    TestTrue(TEXT("Gourde filtrante remplissable"),Kitchen::IsFillableContainer(TEXT("empty_filter_canteen")));
    TestTrue(TEXT("Marmite vide remplissable"),Kitchen::IsFillableContainer(TEXT("cooking_pot")));
    TestFalse(TEXT("Bouteille pleine non remplissable"),Kitchen::IsFillableContainer(TEXT("water_bottle")));
    TestFalse(TEXT("Poêle non remplissable"),Kitchen::IsFillableContainer(TEXT("frying_pan")));
    TestTrue(TEXT("Poêle cuisine"),Kitchen::IsKitchenUtensil(TEXT("frying_pan")));
    TestTrue(TEXT("Marmite potable cuisine"),Kitchen::IsKitchenUtensil(TEXT("cooking_pot_water")));
    TestFalse(TEXT("Marmite contaminée doit être bouillie"),
        Kitchen::IsKitchenUtensil(TEXT("dirty_cooking_pot_water")));
    TestEqual(TEXT("Viande cru vers cuite"),Kitchen::CookedFoodFor(TEXT("raw_meat")),FName(TEXT("cooked_meat")));
    TestEqual(TEXT("Poisson cru vers cuit"),Kitchen::CookedFoodFor(TEXT("raw_fish")),FName(TEXT("cooked_fish")));
    TestEqual(TEXT("Œuf cru vers cuit"),Kitchen::CookedFoodFor(TEXT("egg")),FName(TEXT("cooked_egg")));
    TestEqual(TEXT("Pomme de terre"),Kitchen::CookedFoodFor(TEXT("potato")),FName(TEXT("cooked_potato")));
    TestTrue(TEXT("Pas de cuisine pour équipement"),Kitchen::CookedFoodFor(TEXT("rifle")).IsNone());

    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("World isolé"),World))return false;
    auto* Source=World->SpawnActor<AAnomaliaZPrigimaliaWaterSource>(
        FVector::ZeroVector,FRotator::ZeroRotator);
    if(!TestNotNull(TEXT("Source créée"),Source)){World->DestroyWorld(false);return false;}
    TestFalse(TEXT("Eau naturelle non potable par défaut"),Source->bPotable);
    TestTrue(TEXT("Accès à 100 cm"),Source->CanFillFrom(FVector(100,0,0)));
    TestFalse(TEXT("Refus à 300 cm"),Source->CanFillFrom(FVector(300,0,0)));
    Source->bAvailable=false;
    TestFalse(TEXT("Point fermé"),Source->CanFillFrom(FVector::ZeroVector));
    World->DestroyWorld(false);
    return true;
}
#endif
