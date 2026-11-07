#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../Survival/AnomaliaZPrigimaliaThermalModel.h"
#include "../Survival/AnomaliaZPrigimaliaWeather.h"
#include "../AnomaliaZPrigimaliaSurvivor.h"
#include "../AnomaliaZPrigimaliaInventoryComponent.h"
#include "../AnomaliaZPrigimaliaVitalsComponent.h"
#include "Engine/World.h"
#include "Misc/Guid.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaThermalTest,"AnomaliaZPrigimalia.Native.WeatherThermalModel",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FAnomaliaThermalTest::RunTest(const FString& Parameters)
{
    AnomaliaThermal::Item Food;
    for(int N=0;N<60;++N)Food=AnomaliaThermal::Advance(Food,-25,60);
    TestTrue(TEXT("Sustained cold freezes provisions"),Food.Ice>.99);
    TestFalse(TEXT("Frozen provisions cannot be consumed"),AnomaliaThermal::Consumable(Food));
    const auto FirstWarm=AnomaliaThermal::Advance(Food,45,1);
    TestTrue(TEXT("One second near fire does not skip phase change"),FirstWarm.Ice>.9);
    for(int N=0;N<60;++N)Food=AnomaliaThermal::Advance(Food,45,60);
    TestTrue(TEXT("Sustained heat thaws provisions"),AnomaliaThermal::Consumable(Food));
    TestFalse(TEXT("Scalding provisions need cooling"),AnomaliaThermal::Consumable({90,0}));
    TestTrue(TEXT("Wetting the head reduces heat load"),AnomaliaThermal::BodyTarget(45,5,0,1,0,0,.2)<AnomaliaThermal::BodyTarget(45,5,0,0,0,0,.2));
    TestTrue(TEXT("Wet clothes increase cold exposure"),AnomaliaThermal::BodyTarget(-15,20,1,0,0,0,.7)<AnomaliaThermal::BodyTarget(-15,20,0,0,0,0,.7));
    TestTrue(TEXT("Fire increases cold target temperature"),AnomaliaThermal::BodyTarget(-15,10,0,0,1,1,.7)>AnomaliaThermal::BodyTarget(-15,10,0,0,1,0,.7));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaFrozenInventoryTest,"AnomaliaZPrigimalia.Native.FrozenInventoryPersistence",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FAnomaliaFrozenInventoryTest::RunTest(const FString& Parameters)
{
    auto* World=UWorld::CreateWorld(EWorldType::Game,false);if(!TestNotNull(TEXT("World"),World))return false;
    auto* Survivor=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();auto* Inventory=Survivor->InventoryComponent.Get();
    Survivor->RestoreSurvival(10,10,100);FString Error;
    const FString Scope=TEXT("thermal-")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    if(!TestTrue(TEXT("Existing food catalogue item"),Inventory->TryAddItem(TEXT("canned_beans"),1))){World->DestroyWorld(false);return false;}
    const int Id=Inventory->Stacks[0].StackId;
    for(int N=0;N<60;++N)Inventory->AdvanceConsumableTemperature(-25,60);
    TestFalse(TEXT("Frozen stack blocked without consumption"),Inventory->TryUseStack(Id,1,Scope,TEXT("player"),Error));
    TestEqual(TEXT("Frozen food retained"),Inventory->Stacks[0].Count,1);
    const auto Saved=Inventory->ExportInventoryObject();
    auto* Reloaded=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();
    TestTrue(TEXT("Thermal inventory reload"),Reloaded->InventoryComponent->LoadInventoryObject(Saved,Error));
    TestTrue(TEXT("Reload retains frozen fraction"),Reloaded->InventoryComponent->Stacks[0].FrozenFraction>.99f);
    for(int N=0;N<60;++N)Inventory->AdvanceConsumableTemperature(40,60);
    TestTrue(TEXT("Thawed food consumed through real durable transaction"),Inventory->TryUseStack(Id,1,Scope,TEXT("player"),Error));
    TestTrue(TEXT("Consumed exactly once"),Inventory->Stacks.IsEmpty());
    TestTrue(TEXT("Water available"),Inventory->TryAddItem(TEXT("water_bottle"),1));
    TestTrue(TEXT("Water transaction can wet head"),Inventory->TryUseStack(Inventory->Stacks[0].StackId,1,Scope,TEXT("player"),Error,true));
    TestEqual(TEXT("Head becomes wet after persistence"),Survivor->VitalsComponent->HeadWetness,1.f);
    TestEqual(TEXT("Wetting does not give free hydration"),Survivor->Thirst,10.f);
    TestEqual(TEXT("Empty bottle retained"),Inventory->Stacks[0].ItemId,FName(TEXT("empty_water_bottle")));
    World->DestroyWorld(false);return true;
}
#endif
