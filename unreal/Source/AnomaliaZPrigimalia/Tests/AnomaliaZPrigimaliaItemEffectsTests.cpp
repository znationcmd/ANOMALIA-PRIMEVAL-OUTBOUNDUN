#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaZPrigimaliaSurvivor.h"
#include "../AnomaliaZPrigimaliaInventoryComponent.h"
#include "../AnomaliaZPrigimaliaItemEffectsComponent.h"
#include "../AnomaliaZPrigimaliaConfigLibrary.h"
#include "Engine/World.h"
#include "Misc/Guid.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaZPrigimaliaItemEffectsTest,"AnomaliaZPrigimalia.Native.ItemEffects",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaZPrigimaliaItemEffectsTest::RunTest(const FString& Parameters)
{
    const FString Server=TEXT("item-effects-")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    auto* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("Isolated effects world"),World)) return false;
    auto* Player=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();
    if(!TestNotNull(TEXT("Native survivor"),Player)) { World->DestroyWorld(false);return false; }
    auto* Items=Player->InventoryComponent.Get();auto* Effects=Player->ItemEffectsComponent.Get();
    FString Error,Raw;
    if(!TestTrue(TEXT("Cigarette stack available"),Items->TryAddItem(TEXT("cigarette"),2)))
    { World->DestroyWorld(false);return false; }
    const int32 Cigarette=Items->Stacks[0].StackId;
    TestFalse(TEXT("Missing firestarter preserves tobacco"),Items->TryUseStack(Cigarette,2,Server,TEXT("smoker"),Error));
    TestEqual(TEXT("Failed tobacco use grants no effects"),Effects->State.Dependence,0.f);
    TestTrue(TEXT("Firestarter can be carried"),Items->TryAddItem(TEXT("lighter"),1));
    TestTrue(TEXT("Tobacco use persists both item and risks"),Items->TryUseStack(Cigarette,2,Server,TEXT("smoker"),Error));
    TestEqual(TEXT("Tobacco dependence is an adverse game state"),Effects->State.Dependence,8.f);
    TestTrue(TEXT("Tobacco has a temporary effect"),Effects->State.RemainingSeconds>0);
    TestTrue(TEXT("Waste is retained"),Items->Stacks.ContainsByPredicate([](const auto& S){return S.ItemId==TEXT("cigarette_butt") && S.Count==1;}));
    TestTrue(TEXT("Read tobacco profile"),UAnomaliaZPrigimaliaConfigLibrary::LoadPlayerProfile(Server,TEXT("smoker"),Raw,Error));
    TSharedPtr<FJsonObject> Profile;FAnomaliaZPrigimaliaItemEffectsState Saved;
    if(TestTrue(TEXT("Combined tobacco profile parses"),FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw),Profile)))
    {
        TestTrue(TEXT("Effects state reads from the same inventory profile"),UAnomaliaZPrigimaliaItemEffectsComponent::ReadState(Profile->GetObjectField(TEXT("survival")),Saved,Error));
        auto* Restart=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();Restart->ItemEffectsComponent->ApplyState(Saved);
        TestEqual(TEXT("Restart retains adverse dependence"),Restart->ItemEffectsComponent->State.Dependence,8.f);
    }
    TestTrue(TEXT("Seed malformed existing effects"),UAnomaliaZPrigimaliaConfigLibrary::SavePlayerProfile(Server,TEXT("corrupt"),TEXT("{\"survival\":{\"itemEffects\":{\"Intoxication\":\"keep\"}}}"),Error));
    TestFalse(TEXT("Malformed effects block consumption without overwriting profile"),Items->TryUseStack(Cigarette,1,Server,TEXT("corrupt"),Error));
    TestEqual(TEXT("Rejected malformed save preserves live effects"),Effects->State.Dependence,8.f);
    TestTrue(TEXT("Remaining cigarette not lost on corrupt profile"),Items->Stacks.ContainsByPredicate([&](const auto& S){return S.StackId==Cigarette && S.Count==1;}));

    auto* Patient=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();auto* Medical=Patient->InventoryComponent.Get();
    auto Wounds=Patient->ItemEffectsComponent->State;Wounds.Blood=50;Wounds.Bleeding=40;Wounds.Infection=70;Wounds.Poison=70;Wounds.Pain=60;
    Patient->ItemEffectsComponent->ApplyState(Wounds);
    for(const FName Id:{FName(TEXT("sterile_bandage")),FName(TEXT("tetracycline")),FName(TEXT("charcoal_tablets"))})
    {
        if(!TestTrue(TEXT("Medical source available"),Medical->TryAddItem(Id,1))) continue;
        const auto* Stack=Medical->Stacks.FindByPredicate([&](const auto& S){return S.ItemId==Id;});
        if(Stack) TestTrue(TEXT("Appropriate medical effect can improve condition at full health"),Medical->TryUseStack(Stack->StackId,1,Server,TEXT("patient"),Error));
    }
    TestEqual(TEXT("Bandage controls bleeding"),Patient->ItemEffectsComponent->State.Bleeding,0.f);
    TestEqual(TEXT("Antibiotic affects game infection"),Patient->ItemEffectsComponent->State.Infection,40.f);
    TestEqual(TEXT("Antitoxic item affects game poisoning"),Patient->ItemEffectsComponent->State.Poison,35.f);
    TestEqual(TEXT("Unrelated blood deficit remains"),Patient->ItemEffectsComponent->State.Blood,50.f);
    if(TestTrue(TEXT("Diagnostic source available"),Medical->TryAddItem(TEXT("blood_test_kit"),1)))
    {
        const auto* Test=Medical->Stacks.FindByPredicate([](const auto& S){return S.ItemId==TEXT("blood_test_kit");});
        if(Test) TestTrue(TEXT("Diagnostic consumes kit and publishes readable result"),Medical->TryUseStack(Test->StackId,1,Server,TEXT("patient"),Error));
        TestTrue(TEXT("Diagnostic feedback includes live blood value"),Medical->UseMessage.Contains(TEXT("sang : 50")));
        TestTrue(TEXT("Diagnostic feedback includes game infection value"),Medical->UseMessage.Contains(TEXT("infection fictive : 40")));
    }

    auto* WaterUser=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();auto* Water=WaterUser->InventoryComponent.Get();
    if(TestTrue(TEXT("Treatment item available"),Water->TryAddItem(TEXT("water_purification_tablets"),1)))
    {
        const int32 Treatment=Water->Stacks[0].StackId;
        TestFalse(TEXT("Treatment requires actual dirty bottle"),Water->TryUseStack(Treatment,1,Server,TEXT("water"),Error));
        TestTrue(TEXT("Dirty water can be carried"),Water->TryAddItem(TEXT("dirty_water_bottle"),1));
        TestTrue(TEXT("Closed water recipe persists inventory replacement"),Water->TryUseStack(Treatment,1,Server,TEXT("water"),Error));
        TestEqual(TEXT("Water treatment leaves one bottle, no duplication"),Water->Stacks.Num(),1);
        if(!Water->Stacks.IsEmpty()) TestEqual(TEXT("Clean water replaces dirty water and treatment source"),Water->Stacks[0].ItemId,FName(TEXT("water_bottle")));
        auto* WaterRestart=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();
        TestTrue(TEXT("Treated water survives reload"),WaterRestart->InventoryComponent->LoadInventoryFromPlayerProfile(Server,TEXT("water"),Error));
        TestTrue(TEXT("Reload retains only clean output"),WaterRestart->InventoryComponent->Stacks.Num()==1 && WaterRestart->InventoryComponent->Stacks[0].ItemId==TEXT("water_bottle"));
        TestFalse(TEXT("Original treatment request cannot replay"),Water->TryUseStack(Treatment,1,Server,TEXT("water"),Error));
    }

    auto* RP=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();auto* Substance=RP->InventoryComponent.Get();
    if(TestTrue(TEXT("RP supply available"),Substance->TryAddItem(TEXT("rp_substance_cocaine"),4)))
    {
        const int32 Stack=Substance->Stacks[0].StackId;
        for(int32 Count=4;Count>0;--Count) TestTrue(TEXT("Server use consumes exactly one RP unit"),Substance->TryUseStack(Stack,Count,Server,TEXT("rp"),Error));
        TestTrue(TEXT("Repeated RP use accumulates dependence"),RP->ItemEffectsComponent->State.Dependence>40);
        TestEqual(TEXT("Intoxication is bounded"),RP->ItemEffectsComponent->State.Intoxication,100.f);
        TestTrue(TEXT("Intoxication limits movement"),RP->ItemEffectsComponent->GetMovementScale()<1.f);
        const float Before=RP->Health;RP->ItemEffectsComponent->AdvanceSimulation(.25f);
        TestTrue(TEXT("High intoxication harms the game character"),RP->Health<Before);
        const float Time=RP->ItemEffectsComponent->State.RemainingSeconds;
        RP->ItemEffectsComponent->AdvanceSimulation(500.f);
        TestTrue(TEXT("Hitches cannot fast-forward effects or purge dependence"),RP->ItemEffectsComponent->State.RemainingSeconds>Time-1);
    }
    auto Extensions=MakeShared<FJsonObject>();auto Extra=MakeShared<FJsonObject>();Extra->SetStringField(TEXT("custom"),TEXT("preserved"));Extensions->SetObjectField(TEXT("itemEffects"),Extra);
    TestTrue(TEXT("Writing effects accepts future extension data"),UAnomaliaZPrigimaliaItemEffectsComponent::WriteState(Extensions,Wounds,Error));
    TestEqual(TEXT("Unknown nested extension preserved"),Extensions->GetObjectField(TEXT("itemEffects"))->GetStringField(TEXT("custom")),FString(TEXT("preserved")));
    World->DestroyWorld(false);return true;
}
#endif
