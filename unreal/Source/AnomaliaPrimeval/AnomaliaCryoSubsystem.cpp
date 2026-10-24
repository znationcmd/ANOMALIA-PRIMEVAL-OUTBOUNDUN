#include "AnomaliaCryoSubsystem.h"
#include "AnomaliaConfigLibrary.h"
#include "AnomaliaGameMode.h"
#include "Engine/World.h"
#include "JsonObjectConverter.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
 constexpr int32 MaxTerminals=256;
 constexpr int32 MaxStoredCreatures=4096;
 bool ValidStorageId(const FString& Id)
 {
  if(Id.IsEmpty()||Id.Len()>128)return false;
  for(const TCHAR C:Id)if(C<32||C==127)return false;
  return true;
 }
 bool ValidTerminal(const FAnomaliaCryoTerminal& T,TSet<FString>& AllIds)
 {
  if(!ValidStorageId(T.Id)||!ValidStorageId(T.OwnerId)||T.Location.ContainsNaN()||
     !FMath::IsFinite(T.Range)||T.Range<1.f||T.Range>200.f||T.Capacity< -1||
     T.AllowedIds.Num()>256||T.Creatures.Num()>MaxStoredCreatures||
     (T.Capacity>=0&&T.Creatures.Num()>T.Capacity))return false;
  for(const FString& Id:T.AllowedIds)if(!ValidStorageId(Id))return false;
  for(const auto& C:T.Creatures)
  {
   if(!ValidStorageId(C.Id)||!ValidStorageId(C.OwnerId)||C.Species.Len()>128||
      !C.bStored||C.bDead||AllIds.Contains(C.Id)||AllIds.Num()>=MaxStoredCreatures)return false;
   AllIds.Add(C.Id);
  }
  return true;
 }
}

void UAnomaliaCryoSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
 Super::OnWorldBeginPlay(InWorld);
 if(InWorld.GetNetMode()!=NM_Client)EnsureStorage();
}

bool UAnomaliaCryoSubsystem::EnsureStorage()
{
 if(!IsInGameThread()||!GetWorld()||GetWorld()->GetNetMode()==NM_Client)return false;
 if(bStorageReady)return true;
 if(!StorageServerId.IsEmpty())return StartPersistentStorage(StorageServerId);
 const auto* Mode=GetWorld()->GetAuthGameMode<AAnomaliaGameMode>();
 return StartPersistentStorage(Mode?Mode->ServerId:TEXT("main"));
}

bool UAnomaliaCryoSubsystem::StartPersistentStorage(const FString& ServerId)
{
 if(!IsInGameThread()||!GetWorld()||GetWorld()->GetNetMode()==NM_Client)return false;
 if(bStorageReady)return StorageServerId==ServerId;
 StorageServerId=ServerId;
 FString Raw;
 if(!UAnomaliaConfigLibrary::LoadWorldState(ServerId,TEXT("creature-vault-metadata"),Raw,StorageError))
 {
  // Missing is the only recoverable load error. Corrupt/inaccessible saves stay untouched.
  if(StorageError!=TEXT("World state not found"))return false;
  if(!SaveStorage())return false;
  bStorageReady=true;return true;
 }
 TSharedPtr<FJsonObject> Root;
 const auto Reader=TJsonReaderFactory<>::Create(Raw);
 const TArray<TSharedPtr<FJsonValue>>* Values=nullptr;
 double Version=0;
 FString Kind;
 if(!FJsonSerializer::Deserialize(Reader,Root)||!Root.IsValid()||
    !Root->TryGetNumberField(TEXT("schemaVersion"),Version)||Version!=1||
    !Root->TryGetStringField(TEXT("recordKind"),Kind)||Kind!=TEXT("terminal-metadata-only")||
    !Root->TryGetArrayField(TEXT("terminals"),Values)||Values->Num()>MaxTerminals)
 {StorageError=TEXT("Unsupported or malformed vault metadata; preserved");return false;}
 TMap<FString,FAnomaliaCryoTerminal> Loaded;
 TSet<FString> LoadedIds;
 for(const auto& Value:*Values)
 {
  const TSharedPtr<FJsonObject>* Object=nullptr;
  FAnomaliaCryoTerminal T;
  if(!Value.IsValid()||!Value->TryGetObject(Object)||!Object||!Object->IsValid()||
     !(*Object)->HasTypedField<EJson::String>(TEXT("id"))||
     !(*Object)->HasTypedField<EJson::String>(TEXT("ownerId"))||
     !(*Object)->HasTypedField<EJson::Array>(TEXT("creatures"))||
     !FJsonObjectConverter::JsonObjectToUStruct(Object->ToSharedRef(),&T,0,0)||
     !ValidTerminal(T,LoadedIds)||Loaded.Contains(T.Id))
  {StorageError=TEXT("Invalid or duplicate vault metadata; preserved");return false;}
  Loaded.Add(T.Id,MoveTemp(T));
 }
 Terminals=MoveTemp(Loaded);StoredCreatureIds=MoveTemp(LoadedIds);
 bStorageReady=true;StorageError.Empty();return true;
}

bool UAnomaliaCryoSubsystem::SaveStorage()
{
 if(Terminals.Num()>MaxTerminals){StorageError=TEXT("Vault terminal limit reached");return false;}
 auto Root=MakeShared<FJsonObject>();
 Root->SetNumberField(TEXT("schemaVersion"),1);
 // Explicitly label this legacy metadata, never a complete actor snapshot.
 Root->SetStringField(TEXT("recordKind"),TEXT("terminal-metadata-only"));
 TArray<TSharedPtr<FJsonValue>> Values;
 TArray<FString> Keys;Terminals.GetKeys(Keys);Keys.Sort();
 TSet<FString> ValidatedIds;
 for(const auto& Key:Keys)
 {
  const auto& T=Terminals[Key];
  auto Object=MakeShared<FJsonObject>();
  if(!ValidTerminal(T,ValidatedIds)||!FJsonObjectConverter::UStructToJsonObject(
      FAnomaliaCryoTerminal::StaticStruct(),&T,Object.ToSharedRef(),0,0))
  {StorageError=TEXT("Invalid vault metadata; write refused");return false;}
  Values.Add(MakeShared<FJsonValueObject>(Object));
 }
 Root->SetArrayField(TEXT("terminals"),Values);
 FString Raw;
 const auto Writer=TJsonWriterFactory<>::Create(&Raw);
 if(!FJsonSerializer::Serialize(Root,Writer))return false;
 return UAnomaliaConfigLibrary::SaveWorldState(StorageServerId,TEXT("creature-vault-metadata"),Raw,StorageError);
}

bool UAnomaliaCryoSubsystem::CanAccess(const FAnomaliaCryoTerminal& Terminal,const FString& ActorId,bool Admin) const
{
 return !ActorId.IsEmpty()&&(Admin||ActorId==Terminal.OwnerId||Terminal.AllowedIds.Contains(ActorId));
}
bool UAnomaliaCryoSubsystem::RegisterTerminal(const FString& Id,const FString& Owner,FVector Location)
{
 if(!EnsureStorage()||!ValidStorageId(Id)||!ValidStorageId(Owner)||Location.ContainsNaN()||Terminals.Contains(Id))return false;
 FAnomaliaCryoTerminal Terminal;Terminal.Id=Id;Terminal.OwnerId=Owner;Terminal.Location=Location;
 Terminals.Add(Id,MoveTemp(Terminal));
 if(SaveStorage())return true;
 Terminals.Remove(Id);return false;
}
bool UAnomaliaCryoSubsystem::CaptureCreature(const FString& Id,const FString& Actor,bool Admin,FAnomaliaCryoCreature Creature,bool ViaGun,float Distance,bool AdminMode)
{
 if(!EnsureStorage())return false;
 FAnomaliaCryoTerminal* Terminal=Terminals.Find(Id);
 if(!Terminal||!CanAccess(*Terminal,Actor,Admin))return false;
 const bool Override=Admin&&AdminMode;
 if(Creature.Id.IsEmpty()||Creature.bDead||Creature.bStored||(!Override&&(!Creature.bTamed||Creature.bInCombat||Creature.OwnerId!=Actor&&!Terminal->AllowedIds.Contains(Creature.OwnerId))))return false;
 if(Creature.bHybrid&&!Terminal->bAllowHybrids)return false;
 if(!FMath::IsFinite(Distance)||Distance<0.f||(ViaGun&&Distance>Terminal->Range&&!Override))return false;
 if(StoredCreatureIds.Contains(Creature.Id)||(Terminal->Capacity>=0&&Terminal->Creatures.Num()>=Terminal->Capacity))return false;
 Creature.bStored=true;
 Terminal->Creatures.Add(MoveTemp(Creature));
 StoredCreatureIds.Add(Terminal->Creatures.Last().Id);
 if(SaveStorage())return true;
 StoredCreatureIds.Remove(Terminal->Creatures.Last().Id);
 Terminal->Creatures.Pop();return false;
}
bool UAnomaliaCryoSubsystem::ReleaseCreature(const FString& Id,const FString& CreatureId,const FString& Actor,bool Admin,bool SpawnAllowed,FAnomaliaCryoCreature& OutCreature)
{
 if(!EnsureStorage())return false;
 FAnomaliaCryoTerminal* Terminal=Terminals.Find(Id);
 if(!Terminal||!CanAccess(*Terminal,Actor,Admin)||!SpawnAllowed)return false;
 const int32 Index=Terminal->Creatures.IndexOfByPredicate([&](const FAnomaliaCryoCreature& C){return C.Id==CreatureId;});
 if(Index==INDEX_NONE)return false;
 const auto Saved=Terminal->Creatures[Index];
 Terminal->Creatures.RemoveAt(Index);
 StoredCreatureIds.Remove(CreatureId);
 if(!SaveStorage())
 {Terminal->Creatures.Insert(Saved,Index);StoredCreatureIds.Add(CreatureId);return false;}
 OutCreature=Saved;OutCreature.bStored=false;
 return true;
}
bool UAnomaliaCryoSubsystem::ConfigureTerminal(const FString& Id,const FString& Actor,bool Admin,float Range,int32 Capacity,bool AllowHybrids)
{
 if(!EnsureStorage())return false;
 FAnomaliaCryoTerminal* Terminal=Terminals.Find(Id);
 if(!Terminal||Actor.IsEmpty()||(!Admin&&Actor!=Terminal->OwnerId)||!FMath::IsFinite(Range)||Capacity< -1)return false;
 if(Capacity>=0&&Capacity<Terminal->Creatures.Num())return false;
 const auto Previous=*Terminal;
 Terminal->Range=FMath::Clamp(Range,1.f,200.f);Terminal->Capacity=Capacity;Terminal->bAllowHybrids=AllowHybrids;
 if(SaveStorage())return true;
 *Terminal=Previous;return false;
}
bool UAnomaliaCryoSubsystem::GetTerminal(const FString& Id,FAnomaliaCryoTerminal& OutTerminal) const
{
 const FAnomaliaCryoTerminal* Terminal=Terminals.Find(Id);
 if(!Terminal)return false;
 OutTerminal=*Terminal;return true;
}
