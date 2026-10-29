#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaZPrigimaliaEconomySubsystem.h"
#include "../AnomaliaZPrigimaliaInventoryComponent.h"
#include "../AnomaliaZPrigimaliaSurvivor.h"
#include "../AnomaliaZPrigimaliaConfigLibrary.h"
#include "Engine/World.h"
#include "Misc/Guid.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaZPrigimaliaBankTest, "AnomaliaZPrigimalia.Native.RPBankTransactions",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaZPrigimaliaBankTest::RunTest(const FString& Parameters)
{
    const FString Server = TEXT("bank-test-")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    FString Error, Raw;
    auto* World = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("Isolated bank world"), World)) return false;
    auto* Bank = World->GetSubsystem<UAnomaliaZPrigimaliaEconomySubsystem>();
    if (!Bank || !TestTrue(TEXT("Configure native bank"), Bank->Configure(Server, TEXT("ANOMALIA_LootReview_v1"), Error)))
    { AddError(Error); World->DestroyWorld(false); return false; }
    Bank->SpawnTerminals();
    auto* A = World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>(); auto* B = World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();
    A->SetActorLocation(FVector(350,0,50)); B->SetActorLocation(FVector(350,150,50));
    auto* IA = A->InventoryComponent.Get(); auto* IB = B->InventoryComponent.Get();
    Bank->RefreshAccount(IA, TEXT("player-a")); Bank->RefreshAccount(IB, TEXT("player-b"));
    TestTrue(TEXT("Registered terminal reachable"), IA->bBankingAvailable);
    TestEqual(TEXT("No starting money is fabricated"), IA->BankBalanceCents, int64(0));
    IA->SetProfileRecoveryPending(true);
    TestFalse(TEXT("Inventory awaiting recovery cannot be mutated"),IA->TryAddItem(TEXT("eur_note_50"),2));
    TestFalse(TEXT("Inventory awaiting recovery cannot overwrite its profile"),IA->SaveInventoryToPlayerProfile(Server,TEXT("player-a"),Error));
    IA->SetProfileRecoveryPending(false);
    TestTrue(TEXT("Physical RP note enters native inventory"), IA->TryAddItem(TEXT("eur_note_50"),2));
    TestTrue(TEXT("Seed unrelated profile extension"), UAnomaliaZPrigimaliaConfigLibrary::SavePlayerProfile(Server,TEXT("player-a"),TEXT("{\"extension\":{\"keep\":true}}"),Error));
    TestTrue(TEXT("Deposit consumes one note and credits its fixed value"), Bank->Execute(IA,TEXT("player-a"),EAnomaliaZPrigimaliaBankAction::Deposit,TEXT("eur_note_50"),TEXT(""),0,1,Error));
    TestEqual(TEXT("Deposit value in integer cents"),IA->BankBalanceCents,int64(5000));
    TestFalse(TEXT("Replayed sequence cannot credit again"), Bank->Execute(IA,TEXT("player-a"),EAnomaliaZPrigimaliaBankAction::Deposit,TEXT("eur_note_50"),TEXT(""),0,1,Error));
    TestFalse(TEXT("Withdrawal cannot overdraw"), Bank->Execute(IA,TEXT("player-a"),EAnomaliaZPrigimaliaBankAction::Withdraw,TEXT("eur_note_500"),TEXT(""),0,2,Error));
    TestFalse(TEXT("Negative transfers rejected"), Bank->Execute(IA,TEXT("player-a"),EAnomaliaZPrigimaliaBankAction::Transfer,NAME_None,TEXT("player-b"),-1,2,Error));
    TestFalse(TEXT("Unknown recipient rejected"), Bank->Execute(IA,TEXT("player-a"),EAnomaliaZPrigimaliaBankAction::Transfer,NAME_None,TEXT("missing-account"),1000,2,Error));
    TestTrue(TEXT("Transfer atomically moves balances"), Bank->Execute(IA,TEXT("player-a"),EAnomaliaZPrigimaliaBankAction::Transfer,NAME_None,TEXT("player-b"),2500,2,Error));
    Bank->RefreshAccount(IB,TEXT("player-b"));
    TestEqual(TEXT("Sender debited"), IA->BankBalanceCents,int64(2500));
    TestEqual(TEXT("Recipient credited"), IB->BankBalanceCents,int64(2500));
    TestFalse(TEXT("Transfer replay cannot debit twice"), Bank->Execute(IA,TEXT("player-a"),EAnomaliaZPrigimaliaBankAction::Transfer,NAME_None,TEXT("player-b"),2500,2,Error));
    TestTrue(TEXT("Recipient can withdraw a physical note"), Bank->Execute(IB,TEXT("player-b"),EAnomaliaZPrigimaliaBankAction::Withdraw,TEXT("eur_note_20"),TEXT(""),0,1,Error));
    TestEqual(TEXT("Withdrawal debits value"), IB->BankBalanceCents,int64(500));
    IB->WeightCapacityKg = .001f;
    TestFalse(TEXT("Full inventory does not debit a withdrawal"), Bank->Execute(IB,TEXT("player-b"),EAnomaliaZPrigimaliaBankAction::Withdraw,TEXT("eur_note_5"),TEXT(""),0,2,Error));
    TestEqual(TEXT("Failed withdrawal preserves balance"), IB->BankBalanceCents,int64(500));
    A->SetActorLocation(FVector(-10000,0,50));
    TestFalse(TEXT("Remote banking rejected on server"), Bank->Execute(IA,TEXT("player-a"),EAnomaliaZPrigimaliaBankAction::Deposit,TEXT("eur_note_50"),TEXT(""),0,3,Error));
    A->SetActorLocation(FVector(350,0,50));
    TestFalse(TEXT("A valuable cannot masquerade as banknotes"), Bank->Execute(IA,TEXT("player-a"),EAnomaliaZPrigimaliaBankAction::Deposit,TEXT("gold_bar_1g"),TEXT(""),0,3,Error));
    TestTrue(TEXT("Profile still readable"), UAnomaliaZPrigimaliaConfigLibrary::LoadPlayerProfile(Server,TEXT("player-a"),Raw,Error));
    TestTrue(TEXT("Profile extension preserved"), Raw.Contains(TEXT("extension")));
    World->DestroyWorld(false);
    World = UWorld::CreateWorld(EWorldType::Game,false); Bank = World->GetSubsystem<UAnomaliaZPrigimaliaEconomySubsystem>();
    TestTrue(TEXT("Reload durable ledger"),Bank->Configure(Server,TEXT("ANOMALIA_LootReview_v1"),Error)); Bank->SpawnTerminals();
    A = World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>(); A->SetActorLocation(FVector(350,0,50)); IA = A->InventoryComponent.Get();
    TestTrue(TEXT("Reload physical note inventory"), IA->LoadInventoryFromPlayerProfile(Server,TEXT("player-a"),Error));
    Bank->RefreshAccount(IA,TEXT("player-a"));
    TestEqual(TEXT("Transfer persists after restart"),IA->BankBalanceCents,int64(2500));
    TestEqual(TEXT("Sequence persists after restart"),IA->NextBankSequence,int64(3));
    // Simulate interruption after the durable intent, before the player's note removal reaches its profile.
    TestTrue(TEXT("Prepare post-deposit inventory"), IA->TryRemoveItem(TEXT("eur_note_50"),1));
    FString After;
    TestTrue(TEXT("Snapshot prepared inventory"),IA->BuildInventoryProfile(Server,TEXT("player-a"),After,Error));
    UAnomaliaZPrigimaliaConfigLibrary::LoadWorldState(Server,TEXT("rp-economy"),Raw,Error);
    TSharedPtr<FJsonObject> State;
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw),State)) { World->DestroyWorld(false); return false; }
    auto Account = State->GetObjectField(TEXT("accounts"))->GetObjectField(TEXT("player-a"));
    Account->SetNumberField(TEXT("balanceCents"),7500); Account->SetNumberField(TEXT("sequence"),3);
    auto Pending = MakeShared<FJsonObject>(); Pending->SetStringField(TEXT("playerId"),TEXT("player-a")); Pending->SetStringField(TEXT("profileAfter"),After);
    State->SetObjectField(TEXT("pending"),Pending); Raw.Empty(); FJsonSerializer::Serialize(State.ToSharedRef(),TJsonWriterFactory<>::Create(&Raw));
    TestTrue(TEXT("Persist interrupted deposit intent"),UAnomaliaZPrigimaliaConfigLibrary::SaveWorldState(Server,TEXT("rp-economy"),Raw,Error));
    World->DestroyWorld(false);
    for (int32 Attempt=0;Attempt<2;++Attempt)
    {
        World=UWorld::CreateWorld(EWorldType::Game,false); Bank=World->GetSubsystem<UAnomaliaZPrigimaliaEconomySubsystem>();
        TestTrue(TEXT("Recover interrupted deposit idempotently"),Bank->Configure(Server,TEXT("ANOMALIA_LootReview_v1"),Error));
        A=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>(); IA=A->InventoryComponent.Get();
        TestTrue(TEXT("Recover inventory snapshot"),IA->LoadInventoryFromPlayerProfile(Server,TEXT("player-a"),Error));
        Bank->RefreshAccount(IA,TEXT("player-a"));
        TestEqual(TEXT("Deposit credited only once across repeated restarts"),IA->BankBalanceCents,int64(7500));
        TestFalse(TEXT("Consumed physical note does not reappear"),IA->TryRemoveItem(TEXT("eur_note_50"),1));
        World->DestroyWorld(false);
    }
    TestFalse(TEXT("Server scope traversal rejected"),UAnomaliaZPrigimaliaConfigLibrary::SaveWorldState(TEXT("../escape"),TEXT("rp-economy"),TEXT("{}"),Error));
    return true;
}
#endif
