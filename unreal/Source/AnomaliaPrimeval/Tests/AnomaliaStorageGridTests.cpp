#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaStorageCatalog.h"
#include "../AnomaliaSurvivor.h"
#include "../AnomaliaInventoryComponent.h"
#include "Engine/World.h"
#include "Misc/Guid.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaStorageGridTest,"Anomalia.Native.StorageGrids",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaStorageGridTest::RunTest(const FString& Parameters)
{
    const FString Server=TEXT("storage-grid-")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    const TMap<FName,int32> Required={
        {TEXT("jacket_light"),100},{TEXT("jacket_military"),180},{TEXT("pants"),80},{TEXT("vest_tactical"),100},
        {TEXT("backpack_small"),100},{TEXT("backpack_medium"),150},{TEXT("backpack_large"),180},{TEXT("backpack_military"),240},
        {TEXT("tent_small"),200},{TEXT("tent_large"),800},{TEXT("tent_vehicle"),1000},{TEXT("barrel"),300},{TEXT("crate"),150},
        {TEXT("car"),1000},{TEXT("suv"),1300},{TEXT("van"),1600},{TEXT("truck"),3000},{TEXT("motorcycle"),1000},
        {TEXT("airplane"),500},{TEXT("helicopter"),500},{TEXT("boat"),500},{TEXT("tank"),5500},
        {TEXT("military_vehicle"),5500},{TEXT("civil_vehicle"),1000},{TEXT("f1"),500},
        {TEXT("kart"),1500},{TEXT("quad"),1500},{TEXT("snowmobile"),1500},{TEXT("jet_ski"),1500},
        {TEXT("yacht"),10000},{TEXT("dinosaur"),100000}
    };
    auto* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("Isolated storage world"),World)) return false;
    FString Error;
    for(const auto& Reference:Required)
    {
        FIntPoint Grid;
        if(!TestTrue(TEXT("Requested storage preset exists"),UAnomaliaStorageCatalog::GetGrid(Reference.Key,Grid))) continue;
        TestEqual(*FString::Printf(TEXT("Requested cell capacity: %s"),*Reference.Key.ToString()),Grid.X*Grid.Y,Reference.Value);
        auto* Owner=World->SpawnActor<AAnomaliaSurvivor>();auto* Inventory=Owner->InventoryComponent.Get();
        if(!TestTrue(TEXT("Preset applies to real inventory"),Inventory->ConfigureCompartmentFromPreset(TEXT("cargo"),Reference.Key))) continue;
        if(!TestTrue(TEXT("Rectangular source item can be carried"),Inventory->TryAddItem(TEXT("wood"),1))) continue;
        const int32 Id=Inventory->Stacks[0].StackId;
        TestTrue(TEXT("Far edge of every large grid is usable"),Inventory->TryMoveStack(Id,TEXT("cargo"),Grid.X-1,Grid.Y-3,false));
        TestEqual(TEXT("One three-cell stack occupies three actual cells"),Inventory->GetUsedCells(TEXT("cargo")),3);
        TestFalse(TEXT("Boundary overflow cannot move the stack"),Inventory->TryMoveStack(Id,TEXT("cargo"),Grid.X-1,Grid.Y-2,false));
        TestTrue(TEXT("Large coordinates save through existing persistence"),Inventory->SaveInventoryToPlayerProfile(Server,Reference.Key.ToString(),Error));
        auto* Restart=World->SpawnActor<AAnomaliaSurvivor>();
        TestTrue(TEXT("Every storage size reloads without truncating coordinates"),Restart->InventoryComponent->LoadInventoryFromPlayerProfile(Server,Reference.Key.ToString(),Error));
        if(!Restart->InventoryComponent->Stacks.IsEmpty())
        {
            TestEqual(TEXT("Far-edge X survives reload"),Restart->InventoryComponent->Stacks[0].X,Grid.X-1);
            TestEqual(TEXT("Far-edge Y survives reload"),Restart->InventoryComponent->Stacks[0].Y,Grid.Y-3);
        }
    }
    auto* Owner=World->SpawnActor<AAnomaliaSurvivor>();auto* Inventory=Owner->InventoryComponent.Get();
    TestFalse(TEXT("Huge grid product is bounded"),Inventory->ConfigureCompartment(TEXT("bad"),1000,101));
    TestFalse(TEXT("Dimension overflow is rejected"),Inventory->ConfigureCompartment(TEXT("bad"),1001,1));
    TestFalse(TEXT("Unknown preset cannot invent storage"),Inventory->ConfigureCompartmentFromPreset(TEXT("bad"),TEXT("unlisted")));
    TestTrue(TEXT("Add first rectangular stack"),Inventory->TryAddItem(TEXT("wood"),1));
    TestTrue(TEXT("Separate second stack can be carried"),Inventory->TryAddItem(TEXT("rifle"),1));
    if(Inventory->Stacks.Num()==2)
    {
        const int32 Wood=Inventory->Stacks[0].StackId,Rifle=Inventory->Stacks[1].StackId;
        TestTrue(TEXT("Move rectangular weapon into hands"),Inventory->TryMoveStack(Rifle,TEXT("hands"),0,0,false));
        TestTrue(TEXT("Place first stack"),Inventory->TryMoveStack(Wood,TEXT("pockets"),0,0,false));
        TestFalse(TEXT("A multi-cell weapon cannot overlap existing wood"),Inventory->TryMoveStack(Rifle,TEXT("pockets"),0,0,false));
        TestTrue(TEXT("Auto-stow finds a genuinely free rectangle"),Inventory->TryStowStack(Rifle));
        TestEqual(TEXT("Combined occupied area counts both footprints"),Inventory->GetUsedCells(TEXT("pockets")),13);
    }
    World->DestroyWorld(false);return true;
}
#endif
