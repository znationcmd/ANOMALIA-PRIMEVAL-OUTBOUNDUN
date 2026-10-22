#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaConfigFusionLibrary.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FAnomaliaConfigFusionTest,
    "Anomalia.Native.ConfigFusion",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAnomaliaConfigFusionTest::RunTest(const FString& Parameters)
{
    FString Json, Flat, Report, Error;
    const FString Ini = TEXT("; comment\n[Game]\nDifficulty=3\nName=A=B\n# skip\n");
    TestTrue(TEXT("INI parser"), UAnomaliaConfigFusionLibrary::ParseIniToJson(Ini, Json, Error));
    TestTrue(TEXT("INI flattener"), UAnomaliaConfigFusionLibrary::FlattenIniJson(Json, Flat, Error));
    TSharedPtr<FJsonObject> Parsed;
    TestTrue(TEXT("Flattened JSON parses"), FJsonSerializer::Deserialize(
        TJsonReaderFactory<>::Create(Flat), Parsed));
    if (Parsed.IsValid())
    {
        TestEqual(TEXT("Section.key"), Parsed->GetStringField(TEXT("Game.Difficulty")), FString(TEXT("3")));
        TestEqual(TEXT("INI value preserves equals"), Parsed->GetStringField(TEXT("Game.Name")), FString(TEXT("A=B")));
    }

    TestFalse(TEXT("Dangerous INI key rejected"),
        UAnomaliaConfigFusionLibrary::ParseIniToJson(TEXT("constructor=bad"), Json, Error));
    TestFalse(TEXT("Dangerous INI section rejected"),
        UAnomaliaConfigFusionLibrary::ParseIniToJson(TEXT("[__proto__]\nx=1"), Json, Error));

    const bool Merged = UAnomaliaConfigFusionLibrary::MergeConfigJson(
        TEXT("{\"difficulty\":1,\"stock\":true}"),
        TEXT("{\"difficulty\":2}"),
        TEXT("{\"difficulty\":3,\"labels\":[\"A\"]}"),
        TEXT("{\"difficulty\":4,\"stock\":true}"),
        Report, Error);
    TestTrue(TEXT("Four layers merge"), Merged);
    if (Merged)
    {
        TSharedPtr<FJsonObject> Root;
        TestTrue(TEXT("Report JSON parses"), FJsonSerializer::Deserialize(
            TJsonReaderFactory<>::Create(Report), Root));
        if (Root.IsValid())
        {
            const TSharedPtr<FJsonObject> Values = Root->GetObjectField(TEXT("values"));
            TestEqual(TEXT("Server wins"), Values->GetNumberField(TEXT("difficulty")), 4.0);
            TestTrue(TEXT("Boolean survives"), Values->GetBoolField(TEXT("stock")));
            TestEqual(TEXT("Array survives"), Values->GetArrayField(TEXT("labels")).Num(), 1);
            TestEqual(TEXT("Three distinct conflicts"), Root->GetArrayField(TEXT("conflicts")).Num(), 3);
            TestEqual(TEXT("All four layers recorded"), Root->GetArrayField(TEXT("precedence")).Num(), 4);
        }
    }
    TestFalse(TEXT("Unsafe JSON key rejected"), UAnomaliaConfigFusionLibrary::MergeConfigJson(
        TEXT("{\"__proto__\":1}"), TEXT("{}"), TEXT("{}"), TEXT("{}"), Report, Error));
    TestFalse(TEXT("Malformed JSON rejected"), UAnomaliaConfigFusionLibrary::MergeConfigJson(
        TEXT("{broken"), TEXT("{}"), TEXT("{}"), TEXT("{}"), Report, Error));

    TestTrue(TEXT("12-domain report"), UAnomaliaConfigFusionLibrary::BuildFusionReport(
        {TEXT("config.json"), TEXT("loot_tiers.json")}, Report, Error));
    TSharedPtr<FJsonObject> ReportRoot;
    TestTrue(TEXT("Domain report parses"), FJsonSerializer::Deserialize(
        TJsonReaderFactory<>::Create(Report), ReportRoot));
    if (ReportRoot.IsValid())
    {
        const auto& Domains = ReportRoot->GetArrayField(TEXT("domains"));
        TestEqual(TEXT("All domains present"), Domains.Num(), 12);
        if (Domains.Num() > 0)
            TestTrue(TEXT("Primary server config found"), Domains[0]->AsObject()->GetBoolField(TEXT("primaryPresent")));
    }
    return true;
}
#endif
