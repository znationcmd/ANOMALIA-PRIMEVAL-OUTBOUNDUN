#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaZPrigimaliaModResolver.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FAnomaliaZPrigimaliaModResolverTest,
    "AnomaliaZPrigimalia.Native.ModResolver",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAnomaliaZPrigimaliaModResolverTest::RunTest(const FString& Parameters)
{
    auto MakeMod = [](const TCHAR* Id, const TArray<FString>& Dependencies)
    {
        FAnomaliaZPrigimaliaModManifest Mod;
        Mod.Id = Id;
        Mod.Version = TEXT("1.2.3-rc.1");
        Mod.Sha256 = FString::ChrN(64, TEXT('a'));
        Mod.Dependencies = Dependencies;
        Mod.Compatibility = {TEXT("solo"), TEXT("dedicated")};
        Mod.bSigned = true;
        return Mod;
    };

    FString Error;
    FAnomaliaZPrigimaliaModManifest Core = MakeMod(TEXT("core.mod"), {});
    FAnomaliaZPrigimaliaModManifest World = MakeMod(TEXT("world.mod"), {TEXT("core.mod")});
    FAnomaliaZPrigimaliaModManifest Extra = MakeMod(TEXT("extra.mod"), {TEXT("world.mod")});
    TestTrue(TEXT("Valid signed manifest with checksum"), UAnomaliaZPrigimaliaModResolver::ValidateModManifest(Core, Error));
    FAnomaliaZPrigimaliaModResolution Result;
    TestTrue(TEXT("Topological resolution"), UAnomaliaZPrigimaliaModResolver::ResolveMods(
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

    FAnomaliaZPrigimaliaModManifest Cycle = MakeMod(TEXT("loop.mod"), {TEXT("loop.mod")});
    TestFalse(TEXT("Cycles rejected"), UAnomaliaZPrigimaliaModResolver::ResolveMods(
        {TEXT("loop.mod")}, {Cycle}, {}, Result, Error));
    TestTrue(TEXT("Cycles reported"), Error.Contains(TEXT("Circular")));
    TestEqual(TEXT("Failed resolution does not leak partial result"), Result.Required.Num(), 0);

    TestFalse(TEXT("Duplicate IDs rejected"), UAnomaliaZPrigimaliaModResolver::ResolveMods(
        {TEXT("core.mod")}, {Core, Core}, {}, Result, Error));
    TestFalse(TEXT("Missing dependencies rejected"), UAnomaliaZPrigimaliaModResolver::ResolveMods(
        {TEXT("world.mod")}, {World}, {}, Result, Error));

    Core.bSigned = false;
    TestFalse(TEXT("Unsigned mods refused"), UAnomaliaZPrigimaliaModResolver::ValidateModManifest(Core, Error));
    Core.bSigned = true;
    Core.Sha256 = TEXT("not-a-valid-hash");
    TestFalse(TEXT("Bad SHA256 refused"), UAnomaliaZPrigimaliaModResolver::ValidateModManifest(Core, Error));

    TestTrue(TEXT("Safe relative mapping paths"), UAnomaliaZPrigimaliaModResolver::ValidatePlacementManifest(
        {TEXT("mapping/manifest.json"), TEXT("zones/house.json")}, Error));
    TestFalse(TEXT("Parent traversal refused"), UAnomaliaZPrigimaliaModResolver::ValidatePlacementManifest(
        {TEXT("../world.json")}, Error));
    TestFalse(TEXT("Windows path refused"), UAnomaliaZPrigimaliaModResolver::ValidatePlacementManifest(
        {TEXT("mapping\\bad.json")}, Error));
    TestFalse(TEXT("Absolute path refused"), UAnomaliaZPrigimaliaModResolver::ValidatePlacementManifest(
        {TEXT("/tmp/world.json")}, Error));
    TestFalse(TEXT("Wrong extension refused"), UAnomaliaZPrigimaliaModResolver::ValidatePlacementManifest(
        {TEXT("mods/plugin.exe")}, Error));

    return true;
}
#endif
