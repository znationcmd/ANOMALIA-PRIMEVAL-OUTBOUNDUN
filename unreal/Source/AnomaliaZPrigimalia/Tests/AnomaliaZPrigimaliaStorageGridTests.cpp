#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaZPrigimaliaStorageCatalog.h"
#include "../AnomaliaZPrigimaliaSurvivor.h"
#include "../AnomaliaZPrigimaliaInventoryComponent.h"
#include "../AnomaliaZPrigimaliaVehicleCatalog.h"
#include "../AnomaliaZPrigimaliaEquipmentSlotsLibrary.h"
#include "Engine/World.h"
#include "Misc/Guid.h"
#include "HAL/PlatformTime.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaZPrigimaliaStorageGridTest,"AnomaliaZPrigimalia.Native.StorageGrids",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaZPrigimaliaStorageGridTest::RunTest(const FString& Parameters)
{
    const FString Server=TEXT("storage-grid-")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    const TMap<FName,int32> Required={
        {TEXT("jacket_light"),200},{TEXT("jacket_military"),400},{TEXT("pants"),200},{TEXT("vest_tactical"),300},
        {TEXT("backpack_small"),350},{TEXT("backpack_medium"),630},{TEXT("backpack_large"),900},{TEXT("backpack_military"),1200},
        {TEXT("tent_small"),1000},{TEXT("tent_medium"),2000},{TEXT("tent_large"),4000},{TEXT("tent_vehicle"),5000},
        {TEXT("barrel"),1500},{TEXT("crate"),500},{TEXT("chest"),1000},{TEXT("cabinet"),1000},
        {TEXT("motorcycle"),200},{TEXT("dirt_bike"),100},{TEXT("motorcycle_touring"),600},
        {TEXT("quad"),400},{TEXT("buggy"),800},{TEXT("snowmobile"),400},
        {TEXT("car"),500},{TEXT("suv"),1500},{TEXT("van"),3000},{TEXT("truck"),5000},
        {TEXT("jet_ski"),200},{TEXT("zodiac"),1000},{TEXT("boat"),1500},{TEXT("fishing_boat"),3000},
        {TEXT("yacht"),6000},{TEXT("superyacht"),12000},{TEXT("submarine"),8000},{TEXT("carrier"),30000},
        {TEXT("airplane"),1000},{TEXT("transport_airplane"),8000},{TEXT("fighter_jet"),400},
        {TEXT("helicopter"),1000},{TEXT("transport_helicopter"),6000},{TEXT("attack_helicopter"),1000},
        {TEXT("armored_vehicle"),2000},{TEXT("tank"),1500},{TEXT("military_truck"),6000},{TEXT("missile_vehicle"),2000},
        {TEXT("dino_ground_small"),200},{TEXT("dino_ground_medium"),500},{TEXT("dino_ground_large"),1000},{TEXT("dino_ground_giant"),2000},
        {TEXT("dino_flying_small"),200},{TEXT("dino_flying_medium"),500},{TEXT("dino_flying_large"),1000},
        {TEXT("dino_aquatic_small"),300},{TEXT("dino_aquatic_medium"),800},{TEXT("dino_aquatic_large"),1500},{TEXT("dino_aquatic_giant"),3000}
    };
    auto* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("Isolated storage world"),World)) return false;
    FString Error;
    for(const auto& Vehicle:UAnomaliaZPrigimaliaVehicleCatalog::GetDefaultVehicleCatalog())
    {
        TestTrue(TEXT("Every vehicle keeps a bounded capacity"),Vehicle.StorageSlots>=0 && Vehicle.StorageSlots<=UAnomaliaZPrigimaliaStorageCatalog::MaxCells);
        FAnomaliaZPrigimaliaVehicleDefinition Again;
        TestTrue(TEXT("Vehicle lookup still resolves existing types"),UAnomaliaZPrigimaliaVehicleCatalog::FindVehicleDefinition(Vehicle.Id,Again));
        TestEqual(TEXT("Repeated lookup never multiplies capacity again"),Again.StorageSlots,Vehicle.StorageSlots);
    }
    FAnomaliaZPrigimaliaVehicleDefinition Vehicle;
    UAnomaliaZPrigimaliaVehicleCatalog::FindVehicleDefinition(TEXT("transport_truck"),Vehicle);
    TestEqual(TEXT("Truck catalogue uses approved capacity"),Vehicle.StorageSlots,5000);
    UAnomaliaZPrigimaliaVehicleCatalog::FindVehicleDefinition(TEXT("carrier"),Vehicle);
    TestEqual(TEXT("Carrier catalogue uses 30000 actual cells"),Vehicle.StorageSlots,30000);
    TestEqual(TEXT("Unspecified models scale their original reference once"),UAnomaliaZPrigimaliaStorageCatalog::GetVehicleCapacity(TEXT("unlisted"),37),370);
    const FIntPoint Jacket=UAnomaliaZPrigimaliaEquipmentSlotsLibrary::SuggestedCargoGrid(TEXT("jacket"));
    TestEqual(TEXT("Existing equipment library uses shared capacities"),Jacket.X*Jacket.Y,200);
    for(const auto& Reference:Required)
    {
        FIntPoint Grid;
        if(!TestTrue(TEXT("Requested storage preset exists"),UAnomaliaZPrigimaliaStorageCatalog::GetGrid(Reference.Key,Grid))) continue;
        TestEqual(*FString::Printf(TEXT("Requested cell capacity: %s"),*Reference.Key.ToString()),Grid.X*Grid.Y,Reference.Value);
        auto* Owner=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();auto* Inventory=Owner->InventoryComponent.Get();
        if(!TestTrue(TEXT("Preset applies to real inventory"),Inventory->ConfigureCompartmentFromPreset(TEXT("cargo"),Reference.Key))) continue;
        if(!TestTrue(TEXT("Rectangular source item can be carried"),Inventory->TryAddItem(TEXT("wood"),1))) continue;
        const int32 Id=Inventory->Stacks[0].StackId;
        TestTrue(TEXT("Far edge of every large grid is usable"),Inventory->TryMoveStack(Id,TEXT("cargo"),Grid.X-1,Grid.Y-3,false));
        TestEqual(TEXT("One three-cell stack occupies three actual cells"),Inventory->GetUsedCells(TEXT("cargo")),3);
        TestFalse(TEXT("Boundary overflow cannot move the stack"),Inventory->TryMoveStack(Id,TEXT("cargo"),Grid.X-1,Grid.Y-2,false));
        TestTrue(TEXT("Large coordinates save through existing persistence"),Inventory->SaveInventoryToPlayerProfile(Server,Reference.Key.ToString(),Error));
        auto* Restart=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();
        TestTrue(TEXT("Every storage size reloads without truncating coordinates"),Restart->InventoryComponent->LoadInventoryFromPlayerProfile(Server,Reference.Key.ToString(),Error));
        if(!Restart->InventoryComponent->Stacks.IsEmpty())
        {
            TestEqual(TEXT("Far-edge X survives reload"),Restart->InventoryComponent->Stacks[0].X,Grid.X-1);
            TestEqual(TEXT("Far-edge Y survives reload"),Restart->InventoryComponent->Stacks[0].Y,Grid.Y-3);
        }
    }
    auto* Owner=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();auto* Inventory=Owner->InventoryComponent.Get();
    TestFalse(TEXT("Huge grid product is bounded"),Inventory->ConfigureCompartment(TEXT("bad"),1000,101));
    TestFalse(TEXT("Dimension overflow is rejected"),Inventory->ConfigureCompartment(TEXT("bad"),1001,1));
    TestFalse(TEXT("Unknown preset cannot invent storage"),Inventory->ConfigureCompartmentFromPreset(TEXT("bad"),TEXT("unlisted")));
    TestTrue(TEXT("Previously saved 100000-cell storage remains supported"),Inventory->ConfigureCompartment(TEXT("legacy_dino"),1000,100));
    TestFalse(TEXT("New smaller defaults do not shrink existing storage"),Inventory->ConfigureCompartmentFromPreset(TEXT("legacy_dino"),TEXT("dinosaur")));
    TestTrue(TEXT("Add first rectangular stack"),Inventory->TryAddItem(TEXT("wood"),1));
    TestTrue(TEXT("Separate second stack can be carried"),Inventory->TryAddItem(TEXT("rifle"),1));
    if(Inventory->Stacks.Num()==2)
    {
        const int32 Wood=Inventory->Stacks[0].StackId,Rifle=Inventory->Stacks[1].StackId;
        TestTrue(TEXT("Move rectangular weapon into hands"),Inventory->TryMoveStack(Rifle,TEXT("hands"),0,0,false));
        TestTrue(TEXT("Place first stack"),Inventory->TryMoveStack(Wood,TEXT("pockets"),0,0,false));
        TestFalse(TEXT("A multi-cell weapon cannot overlap existing wood"),Inventory->TryMoveStack(Rifle,TEXT("pockets"),0,0,false));
        TestTrue(TEXT("Auto-stow finds a genuinely free rectangle"),Inventory->TryStowStack(Rifle));
        TestEqual(TEXT("Combined occupied area counts both footprints"),Inventory->GetUsedCells(TEXT("pockets")),12);
    }
    // Exercise the real persistence bound inside the largest newly requested grid.
    auto* BulkOwner=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();auto* Bulk=BulkOwner->InventoryComponent.Get();
    Bulk->Compartments.Reset();
    TestTrue(TEXT("Create real 30000-cell carrier cargo"),Bulk->ConfigureCompartmentFromPreset(TEXT("cargo"),TEXT("carrier")));
    const double Started=FPlatformTime::Seconds();
    if(TestTrue(TEXT("Seed bulk cargo without changing weight limits"),Bulk->TryAddItem(TEXT("ammo"),513)))
    {
        while(Bulk->Stacks.Num()<UAnomaliaZPrigimaliaInventoryComponent::MaxStacks)
        {
            const auto* Source=Bulk->Stacks.FindByPredicate([](const auto& S){return S.Count>1;});
            if(!TestNotNull(TEXT("Bulk split source exists"),Source))break;
            int32 NewId=0;
            if(!TestTrue(TEXT("Split fills real distinct stack slots"),Bulk->TrySplitStack(Source->StackId,1,NewId)))break;
        }
        TestEqual(TEXT("Maximum supported stacks fit without one widget per cell"),Bulk->Stacks.Num(),UAnomaliaZPrigimaliaInventoryComponent::MaxStacks);
        const auto* Source=Bulk->Stacks.FindByPredicate([](const auto& S){return S.Count>1;});
        int32 DeniedId=0;
        if(Source)TestFalse(TEXT("Split cannot exceed the reloadable stack bound"),Bulk->TrySplitStack(Source->StackId,1,DeniedId));
        TestFalse(TEXT("An unmergeable new item cannot exceed the reloadable bound"),Bulk->TryAddItem(TEXT("berry"),1));
        TestTrue(TEXT("Merging additional units needs no extra stack"),Bulk->TryAddItem(TEXT("ammo"),1));
        TestTrue(TEXT("Filled large cargo saves"),Bulk->SaveInventoryToPlayerProfile(Server,TEXT("bulk"),Error));
        auto* Restart=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();
        TestTrue(TEXT("Filled cargo restores through actual persistence"),Restart->InventoryComponent->LoadInventoryFromPlayerProfile(Server,TEXT("bulk"),Error));
        TestEqual(TEXT("All bulk stack identities restore"),Restart->InventoryComponent->Stacks.Num(),Bulk->Stacks.Num());
        int32 Count=0;for(const auto& S:Restart->InventoryComponent->Stacks)Count+=S.Count;
        TestEqual(TEXT("Denied operations neither lose nor duplicate bulk quantities"),Count,514);
    }
    AddInfo(FString::Printf(TEXT("30000-cell/512-stack split-save-reload exercise: %.3f seconds"),FPlatformTime::Seconds()-Started));
    World->DestroyWorld(false);return true;
}
#endif
