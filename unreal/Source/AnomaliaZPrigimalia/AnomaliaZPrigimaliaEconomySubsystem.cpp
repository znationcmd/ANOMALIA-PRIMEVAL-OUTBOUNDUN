#include "AnomaliaZPrigimaliaEconomySubsystem.h"
#include "AnomaliaZPrigimaliaBankTerminal.h"
#include "AnomaliaZPrigimaliaInventoryComponent.h"
#include "AnomaliaZPrigimaliaSurvivor.h"
#include "AnomaliaZPrigimaliaLootSubsystem.h"
#include "AnomaliaZPrigimaliaConfigLibrary.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
namespace
{
    const FString LedgerId = TEXT("rp-economy");
    bool BankSafeId(const FString& Id)
    {
        if (Id.IsEmpty() || Id.Len() > 64) return false;
        for (TCHAR C : Id) if (C > 127 || !(FChar::IsAlnum(C) || C == '-' || C == '_')) return false;
        return true;
    }
    bool BankParse(const FString& Text, TSharedPtr<FJsonObject>& Out)
    { return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Out) && Out.IsValid(); }
    FString BankJson(const TSharedPtr<FJsonObject>& Root)
    { FString Text; FJsonSerializer::Serialize(Root.ToSharedRef(), TJsonWriterFactory<>::Create(&Text)); return Text; }
    bool BankInteger(const TSharedPtr<FJsonObject>& Row, const TCHAR* Key, int64& Out, int64 Min, int64 Max)
    {
        double Value = 0;
        if (!Row->TryGetNumberField(Key, Value) || !FMath::IsFinite(Value) || Value < Min || Value > Max || Value != FMath::FloorToDouble(Value)) return false;
        Out = static_cast<int64>(Value); return true;
    }
}
bool UAnomaliaZPrigimaliaEconomySubsystem::DoesSupportWorldType(EWorldType::Type Type) const
{ return Type == EWorldType::Game || Type == EWorldType::PIE; }
TStatId UAnomaliaZPrigimaliaEconomySubsystem::GetStatId() const
{ RETURN_QUICK_DECLARE_CYCLE_STAT(UAnomaliaZPrigimaliaEconomySubsystem, STATGROUP_Tickables); }
void UAnomaliaZPrigimaliaEconomySubsystem::Tick(float DeltaTime)
{
    if (!bConfigured || !GetWorld() || GetWorld()->GetNetMode() == NM_Client) return;
    Accumulator += DeltaTime; if (Accumulator < 1.f) return; Accumulator = 0;
    FString Error;
    if (!RecoverPending(Error)) return;
    if (bReady && bEnabled && GetWorld()->HasBegunPlay()) SpawnTerminals();
}
bool UAnomaliaZPrigimaliaEconomySubsystem::Configure(const FString& InServerId, const FString& InMapName, FString& Error)
{
    Error.Empty();
    if (bConfigured || !GetWorld() || GetWorld()->GetNetMode() == NM_Client || !BankSafeId(InServerId))
    { Error = TEXT("Invalid authority economy scope"); return false; }
    ServerId = InServerId; MapName = FPaths::GetBaseFilename(InMapName);
    if (MapName.StartsWith(TEXT("UEDPIE_")))
    {
        const int32 Split = MapName.Find(TEXT("_"), ESearchCase::CaseSensitive, ESearchDir::FromStart, 7);
        if (Split >= 0) MapName.RightChopInline(Split+1);
    }
    const FString Override = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Servers"), ServerId, TEXT("rp_economy.json"));
    const FString File = IFileManager::Get().FileExists(*Override) ? Override :
        FPaths::Combine(FPaths::ProjectContentDir(), TEXT("AnomaliaZPrigimalia/Data/rp_economy.json"));
    FString Raw; TSharedPtr<FJsonObject> Config;
    if (IFileManager::Get().FileSize(*File) > 262144 || !FFileHelper::LoadFileToString(Raw, *File) || !BankParse(Raw, Config))
    { Error = TEXT("Missing or invalid RP economy configuration"); return false; }
    int64 Schema = 0;
    const TArray<TSharedPtr<FJsonValue>> *Notes = nullptr, *Locations = nullptr;
    if (!BankInteger(Config, TEXT("schemaVersion"), Schema, 1, 1) || !Config->TryGetBoolField(TEXT("enabled"), bEnabled) ||
        !BankInteger(Config, TEXT("maxBalanceCents"), MaxBalanceCents, 1, 1000000000000LL) ||
        !Config->TryGetArrayField(TEXT("denominations"), Notes) || !Notes || Notes->Num() != 7 ||
        !Config->TryGetArrayField(TEXT("terminals"), Locations) || !Locations || Locations->Num() > 256)
    { Error = TEXT("Invalid RP economy settings"); return false; }
    // Denominations are fixed game tokens. Price/value is never taken from a client.
    const TMap<FName, int64> Required = {{TEXT("eur_note_5"),500},{TEXT("eur_note_10"),1000},{TEXT("eur_note_20"),2000},
        {TEXT("eur_note_50"),5000},{TEXT("eur_note_100"),10000},{TEXT("eur_note_200"),20000},{TEXT("eur_note_500"),50000}};
    for (const auto& Value : *Notes)
    {
        const auto Row = Value.IsValid() && Value->Type == EJson::Object ? Value->AsObject() : nullptr;
        FString Id; int64 Cents = 0;
        if (!Row.IsValid() || !Row->TryGetStringField(TEXT("itemId"), Id) || !Required.Contains(FName(*Id)) ||
            Denominations.Contains(FName(*Id)) || !BankInteger(Row, TEXT("valueCents"), Cents, 1, 50000) || Required[FName(*Id)] != Cents)
        { Error = TEXT("Invalid banknote denomination"); return false; }
        Denominations.Add(FName(*Id), Cents);
    }
    TSet<FString> Seen;
    for (const auto& Value : *Locations)
    {
        const auto Row = Value.IsValid() && Value->Type == EJson::Object ? Value->AsObject() : nullptr;
        FString Id, Map; double X = 0, Y = 0, Z = 0;
        if (!Row.IsValid() || !Row->TryGetStringField(TEXT("id"), Id) || !BankSafeId(Id) ||
            !Row->TryGetStringField(TEXT("map"), Map) || !BankSafeId(Map) || Seen.Contains(Map+TEXT(":")+Id) ||
            !Row->TryGetNumberField(TEXT("x"), X) || !Row->TryGetNumberField(TEXT("y"), Y) || !Row->TryGetNumberField(TEXT("z"), Z) ||
            !FMath::IsFinite(X) || !FMath::IsFinite(Y) || !FMath::IsFinite(Z) || FMath::Abs(X)>2400000 || FMath::Abs(Y)>2400000 || FMath::Abs(Z)>2400000)
        { Error = TEXT("Invalid bank terminal placement"); return false; }
        Seen.Add(Map+TEXT(":")+Id); if (Map == MapName) TerminalLocations.Add(FVector(X,Y,Z));
    }
    if (UAnomaliaZPrigimaliaConfigLibrary::LoadWorldState(ServerId, LedgerId, Raw, Error))
    {
        if (!BankParse(Raw, State)) return false;
        const TSharedPtr<FJsonObject>* Accounts = nullptr;
        if (!BankInteger(State, TEXT("schemaVersion"), Schema, 1, 1) ||
            !State->TryGetObjectField(TEXT("accounts"), Accounts) || !Accounts || !Accounts->IsValid() || (*Accounts)->Values.Num()>2000)
        { Error = TEXT("Malformed bank ledger; existing state preserved"); return false; }
        for (const auto& Pair : (*Accounts)->Values)
        {
            const auto Row = Pair.Value.IsValid() && Pair.Value->Type == EJson::Object ? Pair.Value->AsObject() : nullptr;
            int64 Balance = 0, Sequence = 0;
            if (!BankSafeId(FString(*Pair.Key)) || !Row.IsValid() || !BankInteger(Row, TEXT("balanceCents"), Balance, 0, MaxBalanceCents) ||
                !BankInteger(Row, TEXT("sequence"), Sequence, 0, 1000000000000LL))
            { Error = TEXT("Malformed bank account; existing state preserved"); return false; }
        }
    }
    else if (Error == TEXT("World state not found"))
    {
        State = MakeShared<FJsonObject>(); State->SetNumberField(TEXT("schemaVersion"),1);
        State->SetObjectField(TEXT("accounts"), MakeShared<FJsonObject>()); Error.Empty();
    }
    else return false;
    bConfigured = true;
    if (!RecoverPending(Error)) return false;
    bReady = Persist(Error); return bReady;
}
bool UAnomaliaZPrigimaliaEconomySubsystem::Persist(FString& Error)
{ return UAnomaliaZPrigimaliaConfigLibrary::SaveWorldState(ServerId, LedgerId, BankJson(State), Error); }
bool UAnomaliaZPrigimaliaEconomySubsystem::HasPendingPlayer(const FString& PlayerId) const
{
    const TSharedPtr<FJsonObject>* Pending = nullptr; FString Id;
    return State.IsValid() && State->TryGetObjectField(TEXT("pending"), Pending) && Pending && Pending->IsValid() &&
        (*Pending)->TryGetStringField(TEXT("playerId"), Id) && Id == PlayerId;
}
bool UAnomaliaZPrigimaliaEconomySubsystem::RecoverPending(FString& Error)
{
    if (!State.IsValid() || !State->HasField(TEXT("pending"))) return true;
    const TSharedPtr<FJsonObject>* Ptr = nullptr;
    if (!State->TryGetObjectField(TEXT("pending"), Ptr) || !Ptr || !Ptr->IsValid()) return false;
    const auto Pending = *Ptr; FString Player, Profile;
    if (!Pending->TryGetStringField(TEXT("playerId"), Player) || !BankSafeId(Player) ||
        !Pending->TryGetStringField(TEXT("profileAfter"), Profile)) return false;
    if (!UAnomaliaZPrigimaliaConfigLibrary::SavePlayerProfile(ServerId, Player, Profile, Error)) return false;
    State->RemoveField(TEXT("pending"));
    if (!Persist(Error)) { State->SetObjectField(TEXT("pending"), Pending); return false; }
    if (PendingInventory.IsValid())
    {
        PendingInventory->bPersistenceLocked = false;
        PendingInventory->Commit(TArray<FAnomaliaZPrigimaliaInventoryStack>(PendingInventory->Stacks));
        PendingInventory.Reset();
    }
    bReady = true; return true;
}
TSharedPtr<FJsonObject> UAnomaliaZPrigimaliaEconomySubsystem::Account(const FString& Id) const
{
    const TSharedPtr<FJsonObject>* Ptr = nullptr;
    const auto Accounts = State.IsValid() ? State->GetObjectField(TEXT("accounts")) : nullptr;
    return Accounts.IsValid() && Accounts->TryGetObjectField(Id, Ptr) && Ptr ? *Ptr : nullptr;
}
void UAnomaliaZPrigimaliaEconomySubsystem::SpawnTerminals()
{
    if (!bReady || !bEnabled || bTerminalsSpawned || !GetWorld() || GetWorld()->GetNetMode() == NM_Client) return;
    for (const FVector Location : TerminalLocations)
    {
        FActorSpawnParameters Params; Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        if (auto* Terminal = GetWorld()->SpawnActor<AAnomaliaZPrigimaliaBankTerminal>(Location, FRotator::ZeroRotator, Params)) Terminals.Add(Terminal);
    }
    bTerminalsSpawned = true;
}
bool UAnomaliaZPrigimaliaEconomySubsystem::NearTerminal(const UAnomaliaZPrigimaliaInventoryComponent* Inventory) const
{
    const auto* Survivor = Inventory ? Cast<AAnomaliaZPrigimaliaSurvivor>(Inventory->GetOwner()) : nullptr;
    if (!Survivor || !Survivor->HasAuthority() || Survivor->Health <= 0 || Survivor->bSleeping ||
        Survivor->GetWorld() != GetWorld()) return false;
    for (const auto& Weak : Terminals)
    {
        if (!Weak.IsValid() || Weak->IsActorBeingDestroyed() ||
            FVector::DistSquared(Weak->GetActorLocation(), Survivor->GetActorLocation()) > FMath::Square(300.f)) continue;
        FHitResult Hit; FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaZPrigimaliaBankVisibility), false, Survivor);
        Query.AddIgnoredActor(Weak.Get());
        if (!GetWorld()->LineTraceSingleByChannel(Hit, Survivor->GetActorLocation()+FVector(0,0,50), Weak->GetActorLocation(), ECC_Visibility, Query)) return true;
    }
    return false;
}
void UAnomaliaZPrigimaliaEconomySubsystem::RefreshAccount(UAnomaliaZPrigimaliaInventoryComponent* Inventory, const FString& PlayerId)
{
    if (!bReady || !bEnabled || !Inventory || !Inventory->GetOwner() || !Inventory->GetOwner()->HasAuthority() ||
        Inventory->IsPersistenceLocked() || !BankSafeId(PlayerId) || State->HasField(TEXT("pending"))) return;
    auto Row = Account(PlayerId);
    if (!Row.IsValid())
    {
        if (State->GetObjectField(TEXT("accounts"))->Values.Num() >= 2000) return;
        Row = MakeShared<FJsonObject>(); Row->SetNumberField(TEXT("balanceCents"),0); Row->SetNumberField(TEXT("sequence"),0);
        State->GetObjectField(TEXT("accounts"))->SetObjectField(PlayerId, Row);
        FString Error;
        if (!Persist(Error)) { State->GetObjectField(TEXT("accounts"))->RemoveField(PlayerId); bReady = false; return; }
    }
    const int64 Balance = static_cast<int64>(Row->GetNumberField(TEXT("balanceCents")));
    const int64 Sequence = static_cast<int64>(Row->GetNumberField(TEXT("sequence")))+1;
    const bool Available = NearTerminal(Inventory);
    if (Inventory->BankAccountId != PlayerId || Inventory->BankBalanceCents != Balance ||
        Inventory->NextBankSequence != Sequence || Inventory->bBankingAvailable != Available)
    {
        Inventory->BankAccountId = PlayerId; Inventory->BankBalanceCents = Balance;
        Inventory->NextBankSequence = Sequence; Inventory->bBankingAvailable = Available;
        Inventory->OnInventoryUpdated.Broadcast(); Inventory->GetOwner()->ForceNetUpdate();
    }
}
bool UAnomaliaZPrigimaliaEconomySubsystem::Execute(UAnomaliaZPrigimaliaInventoryComponent* Inventory, const FString& PlayerId,
    EAnomaliaZPrigimaliaBankAction Action, FName NoteId, const FString& RecipientId, int64 AmountCents, int64 Sequence, FString& Error)
{
    Error.Empty();
    const auto* Loot = GetWorld() ? GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaLootSubsystem>() : nullptr;
    if (!bReady || !bEnabled || !Inventory || Inventory->IsPersistenceLocked() || !BankSafeId(PlayerId) ||
        (Loot && Loot->HasPendingPlayer(PlayerId)) ||
        State->HasField(TEXT("pending")) || !NearTerminal(Inventory))
    { Error = TEXT("Banque indisponible : approchez-vous d’un terminal."); return false; }
    const auto Sender = Account(PlayerId);
    if (!Sender.IsValid() || Sequence < 1 || Sequence > 1000000000000LL ||
        Sequence != static_cast<int64>(Sender->GetNumberField(TEXT("sequence")))+1)
    { Error = TEXT("Requête bancaire répétée ou périmée."); return false; }
    const int64 Balance = static_cast<int64>(Sender->GetNumberField(TEXT("balanceCents")));
    const FString BeforeState = BankJson(State);
    const auto BeforeStacks = Inventory->Stacks; const int32 BeforeId = Inventory->NextStackId;
    if (Action == EAnomaliaZPrigimaliaBankAction::Transfer)
    {
        const auto Recipient = BankSafeId(RecipientId) && RecipientId != PlayerId ? Account(RecipientId) : nullptr;
        if (!Recipient.IsValid() || !NoteId.IsNone() || AmountCents <= 0 || AmountCents > Balance ||
            AmountCents > MaxBalanceCents-static_cast<int64>(Recipient->GetNumberField(TEXT("balanceCents"))))
        { Error = TEXT("Compte ou montant de transfert invalide."); return false; }
        Sender->SetNumberField(TEXT("balanceCents"), static_cast<double>(Balance-AmountCents));
        Sender->SetNumberField(TEXT("sequence"), static_cast<double>(Sequence));
        Recipient->SetNumberField(TEXT("balanceCents"), Recipient->GetNumberField(TEXT("balanceCents"))+static_cast<double>(AmountCents));
        if (!Persist(Error)) { BankParse(BeforeState, State); return false; }
        RefreshAccount(Inventory, PlayerId); return true;
    }
    const int64 Value = GetDenomination(NoteId);
    if (!Value || !RecipientId.IsEmpty() || AmountCents != 0 ||
        (Action != EAnomaliaZPrigimaliaBankAction::Deposit && Action != EAnomaliaZPrigimaliaBankAction::Withdraw) ||
        (Action == EAnomaliaZPrigimaliaBankAction::Deposit && Value > MaxBalanceCents-Balance) ||
        (Action == EAnomaliaZPrigimaliaBankAction::Withdraw && Value > Balance))
    { Error = TEXT("Billet ou solde invalide."); return false; }
    Inventory->bSuppressNotifications = true;
    const bool Changed = Action == EAnomaliaZPrigimaliaBankAction::Deposit ? Inventory->TryRemoveItem(NoteId,1) : Inventory->TryAddItem(NoteId,1);
    if (!Changed) { Inventory->bSuppressNotifications = false; Error = TEXT("Billet absent ou inventaire plein."); return false; }
    FString After;
    if (!Inventory->BuildInventoryProfile(ServerId, PlayerId, After, Error))
    { Inventory->Stacks = BeforeStacks; Inventory->NextStackId = BeforeId; Inventory->bSuppressNotifications = false; return false; }
    Sender->SetNumberField(TEXT("balanceCents"), static_cast<double>(Balance+(Action == EAnomaliaZPrigimaliaBankAction::Deposit ? Value : -Value)));
    Sender->SetNumberField(TEXT("sequence"), static_cast<double>(Sequence));
    auto Pending = MakeShared<FJsonObject>(); Pending->SetStringField(TEXT("playerId"), PlayerId); Pending->SetStringField(TEXT("profileAfter"), After);
    State->SetObjectField(TEXT("pending"), Pending);
    if (!Persist(Error))
    { BankParse(BeforeState, State); Inventory->Stacks = BeforeStacks; Inventory->NextStackId = BeforeId; Inventory->bSuppressNotifications = false; return false; }
    Inventory->bPersistenceLocked = true; Inventory->bSuppressNotifications = false; PendingInventory = Inventory; bReady = false;
    if (!RecoverPending(Error)) UE_LOG(LogTemp, Error, TEXT("ANOMALIA bank transaction retained for recovery: %s"), *Error);
    if (bReady) RefreshAccount(Inventory, PlayerId);
    return true;
}
