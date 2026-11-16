#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "AnomaliaFoodPreservation.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaFoodPreservationTest, "Anomalia.Native.FoodPreservation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAnomaliaFoodPreservationTest::RunTest(const FString& Parameters)
{
    TestTrue(TEXT("Raw meat is perishable"), AnomaliaFoodPreservation::IsPerishable(TEXT("raw_meat")));
    TestTrue(TEXT("Fish is perishable"), AnomaliaFoodPreservation::IsPerishable(TEXT("raw_fish")));
    TestFalse(TEXT("Weapons do not spoil"), AnomaliaFoodPreservation::IsPerishable(TEXT("rifle")));
    const float Warm = AnomaliaFoodPreservation::Advance(TEXT("raw_meat"), 1.f, 4.f, 22.f);
    const float Chilled = AnomaliaFoodPreservation::Advance(TEXT("raw_meat"), 1.f, 4.f, 4.f);
    TestTrue(TEXT("Refrigerated meat stays fresher than warm meat"), Chilled > Warm);
    TestTrue(TEXT("Unrefrigerated meat spoils over time"), Warm < 1.f);
    TestTrue(TEXT("Neither container can restore existing spoilage"), Chilled <= 1.f);
    TestEqual(TEXT("Freshness never becomes negative"), AnomaliaFoodPreservation::Advance(TEXT("raw_meat"), .1f, 240.f, 35.f), 0.f);
    TestEqual(TEXT("Non-perishable items stay unchanged"), AnomaliaFoodPreservation::Advance(TEXT("rifle"), .7f, 240.f, 22.f), .7f);
    TestEqual(TEXT("Non-positive duration must not age food"), AnomaliaFoodPreservation::Advance(TEXT("raw_meat"), .6f, 0.f, 22.f), .6f);
    TestTrue(TEXT("At cold temperature food still ages"), Chilled < 1.f);
    return true;
}
#endif
