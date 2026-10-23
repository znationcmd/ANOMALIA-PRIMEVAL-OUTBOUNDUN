#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaModResolver.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FAnomaliaModResolverTest,
    "Anomalia.Native.ModResolver",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAnomaliaModResolverTest::RunTest(const FString& Parameters)
{
    auto MakeMod = [](const TCHAR* Id, const TArray<FString>& Dependencies)
    {
        FAnomaliaModManifest Mod;
        Mod.Id = Id;
        Mod.Version = TEXT("1.2.3-rc.1");
        Mod.Sha256 = FString::ChrN(64, TEXT('a'));
        Mod.Dependencies = Dependencies;
        Mod.Compatibility = {TEXT("solo"), TEXT("dedicated")};
        Mod.bSigned = true;
        return Mod;
    };

    FString Error;
    FAnomaliaModManifest Core = MakeMod(TEXT("core.mod"), {});
    FAnomaliaModManifest World = MakeMod(TEXT("world.mod"), {TEXT("core.mod")});
    FAnomaliaModManifest Extra = MakeMod(TEXT("extra.mod"), {TEXT("world.mod")});
    TestTrue(TEXT("Valid signed manifest with checksum"), UAnomaliaModResolver::ValidateModManifest(Core, Error));
    FAnomaliaModResolution Result;
    TestTrue(TEXT("Topological resolution"), UAnomaliaModResolver::ResolveMods(
        {TEXT("extra.mod"), TEXT("world.mod")}, {Extra, Core, World}, {Core}, Result, Error));
    TestEqual(TEXT("Each dependency only once"), Result.Required.Num(), 3);
    if (Result.Required.Num() == 3)
    {
        TestEqual(TEXT("Core dependency first"), Result.Required[0].Id, FString(TEXT("core.mod")));
        TestEqual(TEXT("World dependency second"), Result.Required[1].Id, FString(TEXT("world.mod")));
        TestEqual(TEXT("Requested mod last"), Result.Required[2].Id, FString(TEXT("extra.mod")));
    }
    TestEqual(TEXT("One installed checksum matches"), Result.AlreadyInstalled.Num(), 1);
    TestEqual(TEXT("Two mod downloads planned"), Result.Downloads.Num(), 2);
    TestTrue(TEXT("User must consent"), Result.bRequiresConsent);

    FAnomaliaModManifest Cycle = MakeMod(TEXT("loop.mod"), {TEXT("loop.mod")});
    TestFalse(TEXT("Cycles rejected"), UAnomaliaModResolver::ResolveMods(
        {TEXT("loop.mod")}, {Cycle}, {}, Result, Error));
    TestTrue(TEXT("Cycles reported"), Error.Contains(TEXT("Circular")));
    TestEqual(TEXT("Failed resolution does not leak partial result"), Result.Required.Num(), 0);

    TestFalse(TEXT("Duplicate IDs rejected"), UAnomaliaModResolver::ResolveMods(
        {TEXT("core.mod")}, {Core, Core}, {}, Result, Error));
    TestFalse(TEXT("Missing dependencies rejected"), UAnomaliaModResolver::ResolveMods(
        {TEXT("world.mod")}, {World}, {}, Result, Error));

    Core.bSigned = false;
    TestFalse(TEXT("Unsigned mods refused"), UAnomaliaModResolver::ValidateModManifest(Core, Error));
    Core.bSigned = true;
    Core.Sha256 = TEXT("not-a-valid-hash");
    TestFalse(TEXT("Bad SHA256 refused"), UAnomaliaModResolver::ValidateModManifest(Core, Error));

    TestTrue(TEXT("Safe relative mapping paths"), UAnomaliaModResolver::ValidatePlacementManifest(
        {TEXT("mapping/manifest.json"), TEXT("zones/house.json")}, Error));
    TestFalse(TEXT("Parent traversal refused"), UAnomaliaModResolver::ValidatePlacementManifest(
        {TEXT("../world.json")}, Error));
    TestFalse(TEXT("Windows path refused"), UAnomaliaModResolver::ValidatePlacementManifest(
        {TEXT("mapping\\bad.json")}, Error));
    TestFalse(TEXT("Absolute path refused"), UAnomaliaModResolver::ValidatePlacementManifest(
        {TEXT("/tmp/world.json")}, Error));
    TestFalse(TEXT("Wrong extension refused"), UAnomaliaModResolver::ValidatePlacementManifest(
        {TEXT("mods/plugin.exe")}, Error));

    return true;
}
#endif
