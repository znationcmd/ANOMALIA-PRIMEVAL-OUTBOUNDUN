#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "AnomaliaConfigLibrary.h"
#include "AnomaliaVehicleCatalog.h"
#include "Misc/Guid.h"
#include "Furniture/AnomaliaFurnitureRules.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaFurnitureTransactionTest, "Anomalia.Native.FurnitureTransactions",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAnomaliaFurnitureTransactionTest::RunTest(const FString& Parameters)
{
    using namespace AnomaliaFurniture;
    Layout State;
    const Record Bed{"bed-1", "owner-a", "bed", {0, 0, 50, 0}};
    TestTrue(TEXT("Place own furniture"), State.Place("owner-a", Bed));
    TestFalse(TEXT("Other owner cannot move"), State.Move("owner-b", "bed-1", {50, 0, 50, 90}));
    TestFalse(TEXT("Removal must be confirmed"), State.Remove("owner-a", "bed-1", false));
    TestTrue(TEXT("Own move"), State.Move("owner-a", "bed-1", {100, 0, 50, 90}));
    TestTrue(TEXT("Undo own move"), State.Undo("owner-a"));
    TestTrue(TEXT("Original pose restored"), State.Find("bed-1") && State.Find("bed-1")->Transform == Bed.Transform);
    TestTrue(TEXT("Redo own move"), State.Redo("owner-a"));
    Layout OtherServer;
    TestFalse(TEXT("Other world has no shared records"), OtherServer.Find("bed-1") != nullptr);
    TestFalse(TEXT("Other world has no shared history"), OtherServer.Undo("owner-a"));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaCatalogTest, "Anomalia.Native.VehicleCatalog",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAnomaliaCatalogTest::RunTest(const FString& Parameters)
{
    const auto Catalog = UAnomaliaVehicleCatalog::GetDefaultVehicleCatalog();
    TestEqual(TEXT("Expected catalogue size including farm tractor (not finished vehicles)"), Catalog.Num(), 28);
    TSet<FName> Ids;
    for (const auto& Definition : Catalog)
    {
        TestFalse(TEXT("Vehicle ID must be unique"), Ids.Contains(Definition.Id));
        Ids.Add(Definition.Id);
        TestTrue(TEXT("Vehicle has a valid speed"), FMath::IsFinite(Definition.MaxSpeedKmh) && Definition.MaxSpeedKmh > 0.f);
        FAnomaliaVehicleDefinition Found;
        TestTrue(TEXT("Catalogue lookup resolves its own entry"),
            UAnomaliaVehicleCatalog::FindVehicleDefinition(Definition.Id, Found));
        TestEqual(TEXT("Lookup identity"), Found.Id, Definition.Id);
    }
    FAnomaliaVehicleDefinition Unknown;
    TestFalse(TEXT("Unknown vehicle rejected"), UAnomaliaVehicleCatalog::FindVehicleDefinition(
        FName(TEXT("__invalid_vehicle__")), Unknown));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaPersistenceTest, "Anomalia.Native.ProfileIsolation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAnomaliaPersistenceTest::RunTest(const FString& Parameters)
{
    // Unique scopes: never overwrite or clean up an existing player's/server's data.
    const FString Scope = TEXT("automation-") + FGuid::NewGuid().ToString(EGuidFormats::Digits);
    const FString ServerA = Scope + TEXT("-a");
    const FString ServerB = Scope + TEXT("-b");
    const FString Player = TEXT("test-player");
    const FString Original = TEXT("{\"inventory\":[\"canteen\"],\"extension\":{\"version\":17}}");
    FString Error, Loaded;
    if (!TestTrue(TEXT("Save profile"), UAnomaliaConfigLibrary::SavePlayerProfile(ServerA, Player, Original, Error))) return false;
    TestTrue(TEXT("Reload profile"), UAnomaliaConfigLibrary::LoadPlayerProfile(ServerA, Player, Loaded, Error));
    TestEqual(TEXT("Unknown fields and inventory survive round trip"), Loaded, Original);
    TestFalse(TEXT("Other server cannot read profile"), UAnomaliaConfigLibrary::LoadPlayerProfile(ServerB, Player, Loaded, Error));
    TestTrue(TEXT("Failed read clears output"), Loaded.IsEmpty());
    TestFalse(TEXT("Traversal rejected"), UAnomaliaConfigLibrary::SavePlayerProfile(TEXT("../escape"), Player, Original, Error));
    TestFalse(TEXT("Invalid replacement rejected"), UAnomaliaConfigLibrary::SavePlayerProfile(ServerA, Player, TEXT("broken JSON"), Error));
    TestTrue(TEXT("Original still readable"), UAnomaliaConfigLibrary::LoadPlayerProfile(ServerA, Player, Loaded, Error));
    TestEqual(TEXT("Rejected write preserves original bytes"), Loaded, Original);
    // Test data deliberately retained under this unique automation scope for inspection.
    return true;
}
#endif
