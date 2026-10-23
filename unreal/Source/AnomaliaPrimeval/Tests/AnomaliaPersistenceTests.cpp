#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaConfigLibrary.h"
#include "../AnomaliaVehicleCatalog.h"
#include "Misc/Guid.h"
#include <limits>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaCatalogTest, "Anomalia.Native.VehicleCatalog",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAnomaliaCatalogTest::RunTest(const FString& Parameters)
{
    const auto Catalog = UAnomaliaVehicleCatalog::GetDefaultVehicleCatalog();
    TestEqual(TEXT("Expected catalogue size (not finished vehicles)"), Catalog.Num(), 45);
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
    FAnomaliaVehicleDefinition Tractor;
    TestTrue(TEXT("Agricultural tractor remains in the catalogue"),
        UAnomaliaVehicleCatalog::FindVehicleDefinition(FName(TEXT("farm_tractor")), Tractor));
    TestTrue(TEXT("Tractor uses the ground domain"), Tractor.Domain == EAnomaliaVehicleDomain::Ground);
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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaSettingsFiniteTest,"Anomalia.Native.SettingsRejectNonFinite",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaSettingsFiniteTest::RunTest(const FString& Parameters)
{
    const FString Scope=TEXT("settings-")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    FAnomaliaServerSettings Settings;Settings.TimeMultiplier=2.f;FString Error;
    if(!TestTrue(TEXT("Save isolated settings"),UAnomaliaConfigLibrary::SaveServerSettings(Scope,Settings,Error))) return false;
    Settings.TimeMultiplier=std::numeric_limits<float>::quiet_NaN();
    TestFalse(TEXT("Reject NaN without replacing existing settings"),UAnomaliaConfigLibrary::SaveServerSettings(Scope,Settings,Error));
    Settings.TimeMultiplier=std::numeric_limits<float>::infinity();
    TestFalse(TEXT("Reject infinity"),UAnomaliaConfigLibrary::SaveServerSettings(Scope,Settings,Error));
    FAnomaliaServerSettings Loaded;
    TestTrue(TEXT("Original settings remain readable"),UAnomaliaConfigLibrary::LoadServerSettings(Scope,Loaded,Error));
    TestEqual(TEXT("Original multiplier preserved"),Loaded.TimeMultiplier,2.f);
    return true;
}
#endif
