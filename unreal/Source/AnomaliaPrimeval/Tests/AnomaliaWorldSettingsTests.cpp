#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/Guid.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "../AnomaliaWorldSettingsLibrary.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FAnomaliaWorldSettingsTest,
    "Anomalia.Native.WorldSettings",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAnomaliaWorldSettingsTest::RunTest(const FString& Parameters)
{
    FAnomaliaWorldSettings Input;
    Input.Mode = TEXT("unknown");
    Input.Difficulty = -9.f;
    Input.Xp = 1000.f;
    Input.Harvest = TNumericLimits<float>::QuietNaN();
    Input.WaterDrain = -1.f;
    Input.Taming = 200.f;
    Input.DayLength = 0.f;
    Input.MaxPlayers = 999;

    const FAnomaliaWorldSettings Normalized =
        UAnomaliaWorldSettingsLibrary::NormalizeWorldSettings(Input);
    TestEqual(TEXT("Invalid mode defaults to PVE"), Normalized.Mode, FString(TEXT("pve")));
    TestEqual(TEXT("Difficulty lower bound"), Normalized.Difficulty, .2f);
    TestEqual(TEXT("XP upper bound"), Normalized.Xp, 20.f);
    TestEqual(TEXT("NaN resets to default"), Normalized.Harvest, 1.f);
    TestEqual(TEXT("Water drain lower bound"), Normalized.WaterDrain, 0.f);
    TestEqual(TEXT("Taming upper bound"), Normalized.Taming, 50.f);
    TestEqual(TEXT("Day multiplier lower bound"), Normalized.DayLength, .1f);
    TestEqual(TEXT("Player count upper bound"), Normalized.MaxPlayers, 64);

    FString Error;
    FAnomaliaWorldSettings Loaded;
    TestFalse(TEXT("Server scope traversal rejected"), UAnomaliaWorldSettingsLibrary::SaveWorldSettings(
        TEXT("../escape"), Input, Error));

    const FString ServerId = TEXT("world-options-test-") +
        FGuid::NewGuid().ToString(EGuidFormats::Digits);
    const FString TestDirectory = FPaths::Combine(
        FPaths::ProjectSavedDir(), TEXT("Servers"), ServerId);
    const bool Saved = UAnomaliaWorldSettingsLibrary::SaveWorldSettings(ServerId, Input, Error);
    TestTrue(TEXT("Save in isolated temporary server scope"), Saved);
    if (Saved)
    {
        TestTrue(TEXT("Reload isolated world settings"), UAnomaliaWorldSettingsLibrary::LoadWorldSettings(
            ServerId, Loaded, Error));
        TestEqual(TEXT("Saved normalization persists"), Loaded.Xp, 20.f);
        TestEqual(TEXT("Invalid mode does not persist"), Loaded.Mode, FString(TEXT("pve")));
        TestEqual(TEXT("Unspecified rate is unchanged"), Loaded.Breeding, 1.f);
    }
    // Only remove the freshly generated, uniquely named test scope.
    IFileManager::Get().DeleteDirectory(*TestDirectory, false, true);
    return true;
}
#endif
