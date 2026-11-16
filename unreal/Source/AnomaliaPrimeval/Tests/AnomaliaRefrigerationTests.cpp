#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "AnomaliaFoodPreservation.h"
#include "AnomaliaPowerGenerator.h"
#include "AnomaliaBatteryCharger.h"
#include "AnomaliaWorkLight.h"
#include "AnomaliaRefrigerator.h"

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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaElectricalDefaultsTest, "Anomalia.Native.ElectricalDefaults",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAnomaliaElectricalDefaultsTest::RunTest(const FString& Parameters)
{
    const AAnomaliaPowerGenerator* Generator = GetDefault<AAnomaliaPowerGenerator>();
    const AAnomaliaBatteryCharger* Charger = GetDefault<AAnomaliaBatteryCharger>();
    const AAnomaliaWorkLight* Light = GetDefault<AAnomaliaWorkLight>();
    const AAnomaliaRefrigerator* Fridge = GetDefault<AAnomaliaRefrigerator>();
    TestNotNull(TEXT("Generator CDO exists"), Generator);
    TestNotNull(TEXT("Battery charger CDO exists"), Charger);
    TestNotNull(TEXT("Construction light CDO exists"), Light);
    TestNotNull(TEXT("Refrigerator CDO exists"), Fridge);
    if (!Generator || !Charger || !Light || !Fridge) return false;
    TestNotNull(TEXT("Generator has mesh slot"), Generator->VisualMesh.Get());
    TestNotNull(TEXT("Charger has status indicator light"), Charger->StatusLED.Get());
    TestNotNull(TEXT("Construction light contains a real spotlight component"), Light->FloodBeam.Get());
    TestFalse(TEXT("Construction light is dark without power"), Light->bIsLit);
    TestFalse(TEXT("Battery charger does not charge without a battery"), Charger->bCharging);
    TestFalse(TEXT("Generator is off by default"), Generator->bRunning);
    TestEqual(TEXT("Cold storage target defaults to 4 degrees"), Fridge->SetPointC, 4.f);
    return true;
}
#endif
