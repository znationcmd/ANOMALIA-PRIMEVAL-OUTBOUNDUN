#include "AnomaliaZPrigimaliaWorldStateSubsystem.h"
#include "AnomaliaZPrigimaliaWorldMechanism.h"
#include "../AnomaliaZPrigimaliaSurvivor.h"
#include "../AnomaliaZPrigimaliaInventoryComponent.h"
#include "../AnomaliaZPrigimaliaGameMode.h"
#include "../AnomaliaZPrigimaliaConfigLibrary.h"
#include "../AnomaliaZPrigimaliaLootSubsystem.h"
#include "../AnomaliaZPrigimaliaEconomySubsystem.h"
#include "Dom/JsonObject.h"
#include "JsonObjectConverter.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Misc/DateTime.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"
#include "HAL/FileManager.h"
#include "Engine/World.h"
#include "Components/CapsuleComponent.h"
#include "Engine/StaticMesh.h"

namespace
{
    double NowUtc() { return FDateTime::UtcNow().ToUnixTimestamp(); }
    FString Json(const TSharedPtr<FJsonObject>& Value)
    { FString Raw;FJsonSerializer::Serialize(Value.ToSharedRef(),TJsonWriterFactory<>::Create(&Raw));return Raw; }
    bool Parse(const FString& Raw,TSharedPtr<FJsonObject>& Value)
    { return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw),Value) && Value.IsValid(); }
    bool SafeId(const FString& Id)
    {
        if(Id.IsEmpty() || Id.Len()>64) return false;
        for(TCHAR C:Id) if(C>127 || !(FChar::IsAlnum(C) || C=='_' || C=='-')) return false;
        return true;
    }
    bool ValidState(const FAnomaliaZPrigimaliaMechanismState& S)
    {
        if(uint8(S.Repair)>uint8(EAnomaliaZPrigimaliaRepairState::Disabled) || S.Deposited.Num()>64 ||
           !FMath::IsFinite(S.FuelSeconds) || S.FuelSeconds<0 || S.FuelSeconds>31536000 ||
           !FMath::IsFinite(S.RepairEndsUtc) || S.RepairEndsUtc<0 ||
           !FMath::IsFinite(S.PortalEndsUtc) || S.PortalEndsUtc<0) return false;
        TSet<FName> Seen;
        for(const auto& Pair:S.Deposited)
        {
            if(!SafeId(Pair.Key.ToString()) || Pair.Key.IsNone() || Seen.Contains(Pair.Key) || Pair.Value<0 || Pair.Value>1000000) return false;
            Seen.Add(Pair.Key);
        }
        return true;
    }
    bool ValidRecipe(const TMap<FName,int32>& Recipe)
    {
        if(Recipe.Num()>64) return false;
        for(const auto& Pair:Recipe) if(!SafeId(Pair.Key.ToString()) || Pair.Value<1 || Pair.Value>1000000) return false;
        return true;
    }
}
bool UAnomaliaZPrigimaliaWorldStateSubsystem::DoesSupportWorldType(EWorldType::Type Type) const
{ return Type==EWorldType::Game || Type==EWorldType::PIE; }
TStatId UAnomaliaZPrigimaliaWorldStateSubsystem::GetStatId() const
{ RETURN_QUICK_DECLARE_CYCLE_STAT(UAnomaliaZPrigimaliaWorldStateSubsystem,STATGROUP_Tickables); }

bool UAnomaliaZPrigimaliaWorldStateSubsystem::Configure(const FString& Server,const FString& Map,FString& Error)
{
    Error.Empty();
    if(!GetWorld() || GetWorld()->GetNetMode()==NM_Client || !SafeId(Server) || Map.IsEmpty()) return false;
    FString MapLeaf=FPaths::GetBaseFilename(Map);
    if(MapLeaf.StartsWith(TEXT("UEDPIE_")))
    {
        const int32 End=MapLeaf.Find(TEXT("_"),ESearchCase::CaseSensitive,ESearchDir::FromStart,7);
        const FString Instance=End>7?MapLeaf.Mid(7,End-7):FString();
        if(!Instance.IsEmpty() && Instance.IsNumeric()) MapLeaf=MapLeaf.Mid(End+1);
    }
    const FString MapKey=FPaths::GetPath(Map).IsEmpty()?MapLeaf:FPaths::Combine(FPaths::GetPath(Map),MapLeaf);
    FTCHARToUTF8 Encoded(*MapKey);
    const FString Id=TEXT("reactive-")+FSHA1::HashBuffer(Encoded.Get(),Encoded.Length()).ToString().ToLower().Left(24);
    if(bConfigured) return ServerId==Server && StateId==Id && bReady;
    bConfigured=true;ServerId=Server;StateId=Id;
    const FString File=FPaths::Combine(FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("Servers"),Server),TEXT("World"),StateId+TEXT(".json"));
    if(IFileManager::Get().FileExists(*File))
    {
        FString Raw;
        if(!UAnomaliaZPrigimaliaConfigLibrary::LoadWorldState(Server,StateId,Raw,Error) || !Read(Raw,Error)) return false;
    }
    else if(!Save(Error)) return false;
    bReady=Recover(Error);return bReady;
}
bool UAnomaliaZPrigimaliaWorldStateSubsystem::Read(const FString& Raw,FString& Error)
{
    TSharedPtr<FJsonObject> Root;
    const TSharedPtr<FJsonObject>* Rows=nullptr;double Version=0,Ends=0;FString EventName;
    if(!Parse(Raw,Root) || !Root->TryGetNumberField(TEXT("schemaVersion"),Version) || Version!=1 ||
       !Root->TryGetObjectField(TEXT("mechanisms"),Rows) || !Rows || (*Rows)->Values.Num()>2048 ||
       !Root->TryGetStringField(TEXT("event"),EventName) || (!EventName.IsEmpty() && !SafeId(EventName)) ||
       !Root->TryGetNumberField(TEXT("eventEndsUtc"),Ends) || !FMath::IsFinite(Ends) || Ends<0)
    {Error=TEXT("Invalid or unsupported reactive world state; original file preserved");return false;}
    TMap<FName,FAnomaliaZPrigimaliaMechanismState> Loaded;
    for(const auto& Row:(*Rows)->Values)
    {
        const auto Object=Row.Value.IsValid() && Row.Value->Type==EJson::Object?Row.Value->AsObject():nullptr;FAnomaliaZPrigimaliaMechanismState S;
        if(!SafeId(FString(*Row.Key)) || Loaded.Contains(FName(*Row.Key)) || !Object.IsValid() || !FJsonObjectConverter::JsonObjectToUStruct(Object.ToSharedRef(),&S,0,0) || !ValidState(S))
        {Error=TEXT("Invalid mechanism state; original file preserved");return false;}
        Loaded.Add(FName(*Row.Key),S);
    }
    TSharedPtr<FJsonObject> LoadedPending;
    if(Root->HasField(TEXT("pending")))
    {
        const TSharedPtr<FJsonObject>* P=nullptr;FString Player,Profile;TSharedPtr<FJsonObject> CheckedProfile;
        if(!Root->TryGetObjectField(TEXT("pending"),P) || !P || !(*P)->TryGetStringField(TEXT("playerId"),Player) ||
           !SafeId(Player) || !(*P)->TryGetStringField(TEXT("profileAfter"),Profile) || !Parse(Profile,CheckedProfile))
        {Error=TEXT("Invalid reactive world transaction; original file preserved");return false;}
        LoadedPending=*P;
    }
    States=MoveTemp(Loaded);Event=EventName.IsEmpty()?NAME_None:FName(*EventName);EventEndsUtc=Ends;Pending=LoadedPending;
    return true;
}
bool UAnomaliaZPrigimaliaWorldStateSubsystem::Save(FString& Error)
{
    auto Root=MakeShared<FJsonObject>();auto Rows=MakeShared<FJsonObject>();
    Root->SetNumberField(TEXT("schemaVersion"),1);
    for(const auto& Pair:States)
    {
        auto Row=MakeShared<FJsonObject>();
        if(!ValidState(Pair.Value) || !FJsonObjectConverter::UStructToJsonObject(FAnomaliaZPrigimaliaMechanismState::StaticStruct(),&Pair.Value,Row,0,0)) return false;
        Rows->SetObjectField(Pair.Key.ToString(),Row);
    }
    Root->SetObjectField(TEXT("mechanisms"),Rows);Root->SetStringField(TEXT("event"),Event.IsNone()?TEXT(""):Event.ToString());
    Root->SetNumberField(TEXT("eventEndsUtc"),EventEndsUtc);
    if(Pending.IsValid()) Root->SetObjectField(TEXT("pending"),Pending);
    return UAnomaliaZPrigimaliaConfigLibrary::SaveWorldState(ServerId,StateId,Json(Root),Error);
}
bool UAnomaliaZPrigimaliaWorldStateSubsystem::HasPendingPlayer(const FString& Player) const
{
    FString Id;return Pending.IsValid() && Pending->TryGetStringField(TEXT("playerId"),Id) && Id==Player;
}
bool UAnomaliaZPrigimaliaWorldStateSubsystem::Recover(FString& Error)
{
    if(!Pending.IsValid()) return true;
    FString Player,Profile;
    if(!Pending->TryGetStringField(TEXT("playerId"),Player) || !SafeId(Player) ||
       !Pending->TryGetStringField(TEXT("profileAfter"),Profile) ||
       !UAnomaliaZPrigimaliaConfigLibrary::SavePlayerProfile(ServerId,Player,Profile,Error)) return false;
    const auto Intent=Pending;Pending.Reset();
    if(!Save(Error)) {Pending=Intent;return false;}
    if(PendingInventory.IsValid())
    {
        PendingInventory->bPersistenceLocked=false;
        PendingInventory->Commit(TArray<FAnomaliaZPrigimaliaInventoryStack>(PendingInventory->Stacks));
        PendingInventory.Reset();
    }
    return true;
}
bool UAnomaliaZPrigimaliaWorldStateSubsystem::Register(AAnomaliaZPrigimaliaWorldMechanism* Actor)
{
    if(!bReady || !IsValid(Actor) || !Actor->HasAuthority() || !Actor->Definition ||
       !SafeId(Actor->StableId.ToString()) || Actor->StableId.IsNone() ||
       Actor->GetWorld()!=GetWorld()) return false;
    if(auto* Existing=Actors.Find(Actor->StableId))
        if(Existing->IsValid() && Existing->Get()!=Actor)
        {UE_LOG(LogTemp,Error,TEXT("Duplicate reactive world ID rejected: %s"),*Actor->StableId.ToString());return false;}
    if(!States.Contains(Actor->StableId))
    {
        if(States.Num()>=2048) return false;
        States.Add(Actor->StableId,FAnomaliaZPrigimaliaMechanismState());FString Error;
        if(!Save(Error)) {States.Remove(Actor->StableId);return false;}
    }
    Actors.Add(Actor->StableId,Actor);RefreshActors();return true;
}
void UAnomaliaZPrigimaliaWorldStateSubsystem::Unregister(AAnomaliaZPrigimaliaWorldMechanism* Actor)
{
    if(!Actor) return;
    const auto* Found=Actors.Find(Actor->StableId);
    if(Found && Found->Get()==Actor) Actors.Remove(Actor->StableId);
    // State deliberately survives streaming out. Missing cable endpoints fail closed.
    if(bReady) RefreshActors();
}
bool UAnomaliaZPrigimaliaWorldStateSubsystem::CommitWithInventory(AAnomaliaZPrigimaliaSurvivor* User,const TMap<FName,int32>& Cost,FString& Error)
{
    auto* Inventory=User->InventoryComponent.Get();
    const auto* Mode=GetWorld()->GetAuthGameMode<AAnomaliaZPrigimaliaGameMode>();
    const FString Player=Mode?Mode->GetPersistentPlayerId(User->GetController()):FString();
    const auto* Loot=GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaLootSubsystem>();
    const auto* Economy=GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaEconomySubsystem>();
    if(!Inventory || Inventory->IsPersistenceLocked() || !SafeId(Player) || !ValidRecipe(Cost) ||
       (Loot && Loot->HasPendingPlayer(Player)) || (Economy && Economy->HasPendingPlayer(Player))) return false;
    if(Cost.IsEmpty()) return Save(Error);
    const auto Before=Inventory->Stacks;const int32 Next=Inventory->NextStackId;
    Inventory->bSuppressNotifications=true;
    auto Rollback=[&](){Inventory->Stacks=Before;Inventory->NextStackId=Next;Inventory->bSuppressNotifications=false;};
    for(const auto& Pair:Cost)
        if(!Inventory->TryRemoveItem(Pair.Key,Pair.Value)) {Rollback();return false;}
    FString Profile;
    if(!Inventory->BuildInventoryProfile(ServerId,Player,Profile,Error)) {Rollback();return false;}
    Pending=MakeShared<FJsonObject>();Pending->SetStringField(TEXT("playerId"),Player);Pending->SetStringField(TEXT("profileAfter"),Profile);
    if(!Save(Error)) {Pending.Reset();Rollback();return false;}
    Inventory->bPersistenceLocked=true;Inventory->bSuppressNotifications=false;PendingInventory=Inventory;
    bReady=Recover(Error);
    // Durable intent is the commit point. Pending actors remain unavailable until recovered.
    return true;
}
bool UAnomaliaZPrigimaliaWorldStateSubsystem::Interact(AAnomaliaZPrigimaliaWorldMechanism* Actor,AAnomaliaZPrigimaliaSurvivor* User,FString& Error)
{
    if(!bReady || Pending.IsValid() || !IsValid(Actor) || !Actor->CanInteract(User) || !Actor->Definition ||
       Actors.FindRef(Actor->StableId).Get()!=Actor) return false;
    const auto* D=Actor->Definition.Get();auto* Current=States.Find(Actor->StableId);
    if(!Current || Current->Repair==EAnomaliaZPrigimaliaRepairState::Disabled) return false;
    const auto Before=*Current;TMap<FName,int32> Cost;
    auto* Inventory=User->InventoryComponent.Get();
    if(!Inventory || Inventory->IsPersistenceLocked()) return false;
    auto Count=[&](FName Item){int64 N=0;for(const auto& S:Inventory->Stacks) if(S.ItemId==Item) N+=S.Count;return N;};
    if(D->Kind==EAnomaliaZPrigimaliaWorldMechanism::Repair)
    {
        if(Current->Repair==EAnomaliaZPrigimaliaRepairState::Repaired || Current->RepairEndsUtc>0 ||
           D->Materials.IsEmpty() || !ValidRecipe(D->Materials) || !FMath::IsFinite(D->RepairSeconds) ||
           D->RepairSeconds<0 || D->RepairSeconds>86400 || !D->RepairedMesh.LoadSynchronous()) return false;
        bool Complete=true;
        for(const auto& Need:D->Materials)
        {
            const int32 Remaining=FMath::Max(0,Need.Value-Current->GetDeposited(Need.Key));
            const int32 Units=int32(FMath::Min<int64>(Remaining,Count(Need.Key)));
            if(Units>0) {Cost.Add(Need.Key,Units);Current->AddDeposited(Need.Key,Units);}
            Complete &= Current->GetDeposited(Need.Key)>=Need.Value;
        }
        // An administrator may reduce a recipe after earlier collective deposits.
        // Already-satisfied work can finish without charging a fictitious extra unit.
        if(Cost.IsEmpty() && !Complete) return false;
        Current->Repair=EAnomaliaZPrigimaliaRepairState::Repairing;
        if(Complete) Current->RepairEndsUtc=NowUtc()+FMath::Max(1.f,D->RepairSeconds);
    }
    else if(D->Kind==EAnomaliaZPrigimaliaWorldMechanism::Generator)
    {
        if(!FMath::IsFinite(D->FuelSecondsPerItem) || D->FuelSecondsPerItem<=0 || D->FuelSecondsPerItem>86400) return false;
        if(Current->FuelSeconds<=0)
        {Cost.Add(D->FuelItem,1);Current->FuelSeconds=D->FuelSecondsPerItem;Current->bSwitchedOn=true;}
        else Current->bSwitchedOn=!Current->bSwitchedOn;
    }
    else if(D->Kind==EAnomaliaZPrigimaliaWorldMechanism::Access)
    {
        if(Current->bUnlocked || (D->bRequiresPower && !Actor->bPowered) ||
           D->RequiredCard.IsNone() || Count(D->RequiredCard)<1) return false;
        Current->bUnlocked=true;if(D->bConsumeCard) Cost.Add(D->RequiredCard,1);
    }
    else if(D->Kind==EAnomaliaZPrigimaliaWorldMechanism::Portal)
    {
        if(Current->PortalEndsUtc>NowUtc())
        {
            if(D->bRequiresPower && !Actor->bPowered) return false;
            if(!IsValid(Actor->Destination) || Actor->Destination->GetWorld()!=GetWorld()) return false;
            FVector Target=Actor->Destination->GetActorLocation();FRotator Rotation=Actor->Destination->GetActorRotation();
            // TeleportTo performs a real encroachment test. A blocked destination consumes nothing.
            return User->TeleportTo(Target,Rotation,false,false);
        }
        if(!IsEventActive(D->RequiredEvent) || (D->bRequiresPower && !Actor->bPowered) ||
           !IsValid(Actor->Destination) || D->PortalComponents.IsEmpty() || !ValidRecipe(D->PortalComponents) ||
           !FMath::IsFinite(D->PortalSeconds) || D->PortalSeconds<1 || D->PortalSeconds>86400) return false;
        Cost=D->PortalComponents;Current->PortalEndsUtc=NowUtc()+D->PortalSeconds;
    }
    else return false;
    if(!CommitWithInventory(User,Cost,Error)) {*Current=Before;return false;}
    if(bReady) RefreshActors();return true;
}
bool UAnomaliaZPrigimaliaWorldStateSubsystem::IsEventActive(FName Id) const
{ return bReady && !Id.IsNone() && Event==Id && EventEndsUtc>NowUtc(); }
bool UAnomaliaZPrigimaliaWorldStateSubsystem::StartWorldEvent(FName Id,float Seconds)
{
    if(!bReady || Pending.IsValid() || !SafeId(Id.ToString()) || Id.IsNone() || !FMath::IsFinite(Seconds) || Seconds<1 || Seconds>86400) return false;
    const FName Old=Event;const double Ends=EventEndsUtc;
    Event=Id;EventEndsUtc=NowUtc()+Seconds;FString Error;
    if(!Save(Error)) {Event=Old;EventEndsUtc=Ends;return false;}
    RefreshActors();return true;
}
void UAnomaliaZPrigimaliaWorldStateSubsystem::SolvePower()
{
    TSet<FName> Seen;
    for(const auto& Pair:Actors)
    {
        if(Seen.Contains(Pair.Key) || !Pair.Value.IsValid()) continue;
        TArray<FName> Queue{Pair.Key};TArray<AAnomaliaZPrigimaliaWorldMechanism*> Group;double Supply=0,Demand=0;
        for(int32 Index=0;Index<Queue.Num();++Index)
        {
            const FName Id=Queue[Index];if(Seen.Contains(Id)) continue;
            auto* Node=Actors.FindRef(Id).Get();if(!Node || !Node->Definition) continue;
            Seen.Add(Id);Group.Add(Node);const auto* D=Node->Definition.Get();const auto& S=States.FindChecked(Id);
            if(S.Repair==EAnomaliaZPrigimaliaRepairState::Disabled) continue;
            if(D->Kind==EAnomaliaZPrigimaliaWorldMechanism::Generator && S.bSwitchedOn && S.FuelSeconds>0 && FMath::IsFinite(D->OutputWatts)) Supply+=FMath::Max(0.f,D->OutputWatts);
            if(D->Kind==EAnomaliaZPrigimaliaWorldMechanism::Consumer || D->bRequiresPower)
                if(FMath::IsFinite(D->DemandWatts)) Demand+=FMath::Max(0.f,D->DemandWatts);
            for(const auto& Other:Actors)
            {
                auto* B=Other.Value.Get();
                if(!B || !B->Definition || Seen.Contains(Other.Key) || States.FindChecked(Other.Key).Repair==EAnomaliaZPrigimaliaRepairState::Disabled ||
                   !(Node->ConnectedNodeIds.Contains(Other.Key) || B->ConnectedNodeIds.Contains(Id))) continue;
                const float Range=FMath::Min(D->CableRangeCm,B->Definition->CableRangeCm);
                if(FMath::IsFinite(Range) && Range>0 && FVector::DistSquared(Node->GetActorLocation(),B->GetActorLocation())<=FMath::Square(Range)) Queue.AddUnique(Other.Key);
            }
        }
        const bool Overload=Supply>0 && Demand>Supply;
        for(auto* Node:Group)
        {
            const auto& S=States.FindChecked(Node->StableId);
            Node->ActiveWorldEvent=Event;Node->WorldEventEndsUtc=EventEndsUtc;
            Node->ApplyServerState(S,Supply>0 && !Overload && S.Repair!=EAnomaliaZPrigimaliaRepairState::Disabled,Overload);
        }
    }
}
void UAnomaliaZPrigimaliaWorldStateSubsystem::RefreshActors() {SolvePower();}
void UAnomaliaZPrigimaliaWorldStateSubsystem::Tick(float Dt)
{
    if(!bConfigured || !GetWorld() || GetWorld()->GetNetMode()==NM_Client || !FMath::IsFinite(Dt) || Dt<=0) return;
    Accumulator+=Dt;if(Accumulator<1) return;
    const float Elapsed=FMath::Min(Accumulator,5.f);Accumulator=0;FString Error;
    if(Pending.IsValid()) {bReady=Recover(Error);if(bReady) RefreshActors();return;}
    if(!bReady) return;
    const auto Before=States;const FName OldEvent=Event;const double OldEnds=EventEndsUtc;bool Changed=false;
    if(EventEndsUtc>0 && EventEndsUtc<=NowUtc()) {Event=NAME_None;EventEndsUtc=0;Changed=true;}
    for(auto& Pair:States)
    {
        auto& S=Pair.Value;
        if(S.Repair==EAnomaliaZPrigimaliaRepairState::Repairing && S.RepairEndsUtc>0 && S.RepairEndsUtc<=NowUtc())
        {S.Repair=EAnomaliaZPrigimaliaRepairState::Repaired;S.RepairEndsUtc=0;Changed=true;}
        // Unloaded generators retain their state and pause consumption; their absent nodes cannot power devices.
        if(Actors.FindRef(Pair.Key).IsValid() && S.bSwitchedOn && S.FuelSeconds>0)
        {S.FuelSeconds=FMath::Max(0.,S.FuelSeconds-Elapsed);if(S.FuelSeconds<=0) S.bSwitchedOn=false;Changed=true;}
        if(S.PortalEndsUtc>0 && S.PortalEndsUtc<=NowUtc()) {S.PortalEndsUtc=0;Changed=true;}
    }
    if(Changed && !Save(Error))
    {
        States=Before;Event=OldEvent;EventEndsUtc=OldEnds;
        // A storage fault disables all powered projections; retries keep authoritative state intact.
        for(const auto& Pair:Actors) if(auto* A=Pair.Value.Get()) A->ApplyServerState(States.FindChecked(Pair.Key),false,false);
        return;
    }
    RefreshActors();
}
