#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../ReactiveWorld/AnomaliaZPrigimaliaWorldStateSubsystem.h"
#include "../ReactiveWorld/AnomaliaZPrigimaliaWorldMechanism.h"
#include "../ReactiveWorld/AnomaliaZPrigimaliaWorldDefinition.h"
#include "../AnomaliaZPrigimaliaConfigLibrary.h"
#include "Engine/World.h"
#include "Dom/JsonObject.h"
#include "Misc/Guid.h"
#include "Misc/DateTime.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "../AnomaliaZPrigimaliaLootSubsystem.h"
#include "../AnomaliaZPrigimaliaLootPickup.h"
#include "EngineUtils.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaZPrigimaliaReactiveWorldTest,"AnomaliaZPrigimalia.Native.ReactiveWorldPersistenceAndPower",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaZPrigimaliaReactiveWorldTest::RunTest(const FString& Parameters)
{
    const FString Server=TEXT("reactive-")+FGuid::NewGuid().ToString(EGuidFormats::Digits).Left(16);
    auto* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("Native world"),World)) return false;
    auto* Store=World->GetSubsystem<UAnomaliaZPrigimaliaWorldStateSubsystem>();FString Error;
    if(!TestNotNull(TEXT("Native state subsystem"),Store)) {World->DestroyWorld(false);return false;}
    TestTrue(TEXT("Initialize isolated server state"),Store->Configure(Server,TEXT("test-map"),Error));
    auto Make=[&](const TCHAR* Id,EAnomaliaZPrigimaliaWorldMechanism Kind,float X)
    {
        auto* A=World->SpawnActor<AAnomaliaZPrigimaliaWorldMechanism>(FVector(X,0,0),FRotator::ZeroRotator);
        A->StableId=FName(Id);A->Definition=NewObject<UAnomaliaZPrigimaliaWorldDefinition>(A);A->Definition->Kind=Kind;
        TestTrue(TEXT("Register stable native actor"),Store->Register(A));return A;
    };
    auto* Generator=Make(TEXT("generator"),EAnomaliaZPrigimaliaWorldMechanism::Generator,0);
    auto* Relay=Make(TEXT("relay"),EAnomaliaZPrigimaliaWorldMechanism::Junction,100);
    auto* Lamp=Make(TEXT("lamp"),EAnomaliaZPrigimaliaWorldMechanism::Consumer,200);
    Generator->Definition->OutputWatts=1000;Lamp->Definition->DemandWatts=100;
    auto& Fuel=Store->States.FindChecked(Generator->StableId);Fuel.FuelSeconds=10;Fuel.bSwitchedOn=true;
    Store->RefreshActors();
    TestFalse(TEXT("Proximity alone does not supply a lamp"),Lamp->bPowered);
    Generator->ConnectedNodeIds.Add(Relay->StableId);Relay->ConnectedNodeIds.Add(Lamp->StableId);
    Store->RefreshActors();TestTrue(TEXT("Explicit cable path supplies real device"),Lamp->bPowered);
    Lamp->Definition->DemandWatts=1001;Store->RefreshActors();
    TestTrue(TEXT("Overload detected"),Lamp->bOverloaded);TestFalse(TEXT("Overload cuts device power"),Lamp->bPowered);
    Lamp->Definition->DemandWatts=100;Store->Unregister(Relay);
    TestFalse(TEXT("Unloaded relay disconnects consumers"),Lamp->bPowered);
    TestTrue(TEXT("Relay restored after cell reload"),Store->Register(Relay));TestTrue(TEXT("Reload restores cable path"),Lamp->bPowered);
    Fuel.FuelSeconds=0;Store->RefreshActors();TestFalse(TEXT("Empty generator cannot supply devices"),Lamp->bPowered);
    auto* Bridge=Make(TEXT("bridge"),EAnomaliaZPrigimaliaWorldMechanism::Repair,400);
    auto& Repair=Store->States.FindChecked(Bridge->StableId);
    Repair.AddDeposited(TEXT("scrap"),100);Repair.AddDeposited(TEXT("wood"),50);
    Repair.Repair=EAnomaliaZPrigimaliaRepairState::Repairing;Repair.RepairEndsUtc=FDateTime::UtcNow().ToUnixTimestamp()-1;
    Store->Tick(1.1f);
    TestTrue(TEXT("Repair deadline completes on server"),Store->FindState(Bridge->StableId)->Repair==EAnomaliaZPrigimaliaRepairState::Repaired);
    Store->Unregister(Bridge);
    TestEqual(TEXT("Deposits survive streaming out"),Store->FindState(Bridge->StableId)->GetDeposited(TEXT("scrap")),100);
    TestTrue(TEXT("Start configured server event"),Store->StartWorldEvent(TEXT("electromagnetic_storm"),60));
    TestTrue(TEXT("Event is active server side"),Store->IsEventActive(TEXT("electromagnetic_storm")));
    TestFalse(TEXT("Different event cannot authorize a portal"),Store->IsEventActive(TEXT("chemical_storm")));
    TestTrue(TEXT("Persist before restart"),Store->Save(Error));
    auto* Restart=NewObject<UAnomaliaZPrigimaliaWorldStateSubsystem>(World);
    TestTrue(TEXT("Read same server/map after restart"),Restart->Configure(Server,TEXT("test-map"),Error));
    const auto* Loaded=Restart->FindState(TEXT("bridge"));
    if(TestNotNull(TEXT("Bridge restored"),Loaded))
    {
        TestTrue(TEXT("Repaired state restored"),Loaded->Repair==EAnomaliaZPrigimaliaRepairState::Repaired);
        TestEqual(TEXT("Consumed materials not reset"),Loaded->GetDeposited(TEXT("wood")),50);
    }
    TestTrue(TEXT("Event deadline survives restart"),Restart->IsEventActive(TEXT("electromagnetic_storm")));
    auto* PIE=NewObject<UAnomaliaZPrigimaliaWorldStateSubsystem>(World);
    TestTrue(TEXT("PIE instance number does not change map persistence identity"),PIE->Configure(Server,TEXT("UEDPIE_7_test-map"),Error));
    TestNotNull(TEXT("Same bridge restored across PIE instances"),PIE->FindState(TEXT("bridge")));
    // Simulate process loss immediately after the durable intent and before profile publication.
    Restart->Pending=MakeShared<FJsonObject>();Restart->Pending->SetStringField(TEXT("playerId"),TEXT("test-player"));
    Restart->Pending->SetStringField(TEXT("profileAfter"),TEXT("{\"marker\":\"committed-once\"}"));
    TestTrue(TEXT("Durable transaction intent"),Restart->Save(Error));
    auto* Recovered=NewObject<UAnomaliaZPrigimaliaWorldStateSubsystem>(World);
    TestTrue(TEXT("Restart replays pending profile"),Recovered->Configure(Server,TEXT("test-map"),Error));
    FString Profile;
    TestTrue(TEXT("Recovered profile exists"),UAnomaliaZPrigimaliaConfigLibrary::LoadPlayerProfile(Server,TEXT("test-player"),Profile,Error));
    TestEqual(TEXT("Exact post-transaction profile published"),Profile,FString(TEXT("{\"marker\":\"committed-once\"}")));
    TestFalse(TEXT("Recovered journal no longer locks player"),Recovered->HasPendingPlayer(TEXT("test-player")));
    auto* OtherMap=NewObject<UAnomaliaZPrigimaliaWorldStateSubsystem>(World);
    TestTrue(TEXT("Separate map scope"),OtherMap->Configure(Server,TEXT("other-map"),Error));
    TestNull(TEXT("World state isolated by map"),OtherMap->FindState(TEXT("bridge")));
    const FString OriginalFile=FPaths::Combine(FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("Servers"),Server),TEXT("World"),Store->StateId+TEXT(".json"));
    TestTrue(TEXT("Seed unsupported future schema"),UAnomaliaZPrigimaliaConfigLibrary::SaveWorldState(Server,Store->StateId,TEXT("{\"schemaVersion\":999}"),Error));
    auto* Future=NewObject<UAnomaliaZPrigimaliaWorldStateSubsystem>(World);
    TestFalse(TEXT("Unsupported save fails closed"),Future->Configure(Server,TEXT("test-map"),Error));
    FString Preserved;TestTrue(TEXT("Original future save remains readable"),UAnomaliaZPrigimaliaConfigLibrary::LoadWorldState(Server,Store->StateId,Preserved,Error));
    TestEqual(TEXT("Future save never overwritten"),Preserved,FString(TEXT("{\"schemaVersion\":999}")));
    World->DestroyWorld(false);
    IFileManager::Get().DeleteDirectory(*FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("Servers"),Server),false,true);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaZPrigimaliaPOIResourceTest,"AnomaliaZPrigimalia.Native.POIResourceExclusivity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaZPrigimaliaPOIResourceTest::RunTest(const FString& Parameters)
{
    const FString Server=TEXT("poi-")+FGuid::NewGuid().ToString(EGuidFormats::Digits).Left(20);FString Error;
    auto* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("POI test world"),World)) return false;
    auto* Loot=World->GetSubsystem<UAnomaliaZPrigimaliaLootSubsystem>();
    if(!Loot || !TestTrue(TEXT("Configure actual native loot system"),Loot->Configure(Server,TEXT("ANOMALIA_LootReview_v1"),Error)))
    {World->DestroyWorld(false);return false;}
    if(!TestTrue(TEXT("Three real existing loot points"),Loot->Spawns.Num()>=3)) {World->DestroyWorld(false);return false;}
    for(auto& Pair:Loot->Items) Pair.Value.bEnabled=false;
    auto* Resource=Loot->Items.Find(TEXT("canned_beans"));
    if(!TestNotNull(TEXT("Existing inventory resource for isolated test"),Resource)) {World->DestroyWorld(false);return false;}
    Resource->bEnabled=true;Resource->Nominal=100;Resource->Minimum=0;Resource->Quantity=1;
    Resource->AllowedPOIs.Add(TEXT("quarry-east"));Resource->AllowedPOIs.Add(TEXT("quarry-west"));
    Resource->Categories.Reset();Resource->Categories.Add(TEXT("canned_food"));Resource->MinTier=1;Resource->MaxTier=5;
    const TArray<FString> POIs{TEXT("quarry-east"),TEXT("quarry-west"),TEXT("")};
    TArray<FString> Points;
    for(int32 I=0;I<3;++I)
    {
        Loot->Spawns[I].POIId=POIs[I];Loot->Spawns[I].Tier=1;
        Loot->Spawns[I].Categories.Reset();Points.Add(Loot->Spawns[I].Id);
    }
    Loot->Spawns.SetNum(3);Loot->RefreshLoot();
    TSet<FString> Spawned;
    for(TActorIterator<AAnomaliaZPrigimaliaLootPickup> It(World);It;++It)
        if(!It->IsActorBeingDestroyed() && It->ItemId==Resource->Id) Spawned.Add(It->SpawnId);
    TestTrue(TEXT("First regional supply point spawns through real native loot"),Spawned.Contains(Points[0]));
    TestTrue(TEXT("Alternative POI prevents single-site monopoly"),Spawned.Contains(Points[1]));
    TestFalse(TEXT("Exclusive resource absent outside allowed POIs"),Spawned.Contains(Points[2]));
    TestEqual(TEXT("Exactly two approved supply points"),Spawned.Num(),2);
    Loot->Spawns[0].POIId=TEXT("civilian-town");Loot->RefreshLoot();
    bool Old=false;
    for(TActorIterator<AAnomaliaZPrigimaliaLootPickup> It(World);It;++It)
        if(!It->IsActorBeingDestroyed() && It->SpawnId==Points[0]) Old=true;
    TestFalse(TEXT("Changed region rule withdraws previously spawned unauthorized pickup"),Old);
    World->DestroyWorld(false);
    IFileManager::Get().DeleteDirectory(*FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("Servers"),Server),false,true);
    return true;
}
#endif
