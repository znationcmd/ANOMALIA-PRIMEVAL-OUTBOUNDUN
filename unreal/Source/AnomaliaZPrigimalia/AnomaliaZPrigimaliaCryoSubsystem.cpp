#include "AnomaliaZPrigimaliaCryoSubsystem.h"

bool UAnomaliaZPrigimaliaCryoSubsystem::CanAccess(const FAnomaliaZPrigimaliaCryoTerminal& Terminal,const FString& ActorId,bool Admin) const
{
 return !ActorId.IsEmpty()&&(Admin||ActorId==Terminal.OwnerId||Terminal.AllowedIds.Contains(ActorId));
}
bool UAnomaliaZPrigimaliaCryoSubsystem::RegisterTerminal(const FString& Id,const FString& Owner,FVector Location)
{
 if(Id.IsEmpty()||Owner.IsEmpty()||Location.ContainsNaN()||Terminals.Contains(Id))return false;
 FAnomaliaZPrigimaliaCryoTerminal Terminal;Terminal.Id=Id;Terminal.OwnerId=Owner;Terminal.Location=Location;
 Terminals.Add(Id,MoveTemp(Terminal));return true;
}
bool UAnomaliaZPrigimaliaCryoSubsystem::CaptureCreature(const FString& Id,const FString& Actor,bool Admin,FAnomaliaZPrigimaliaCryoCreature Creature,bool ViaGun,float Distance,bool AdminMode)
{
 FAnomaliaZPrigimaliaCryoTerminal* Terminal=Terminals.Find(Id);
 if(!Terminal||!CanAccess(*Terminal,Actor,Admin))return false;
 const bool Override=Admin&&AdminMode;
 if(Creature.Id.IsEmpty()||Creature.bDead||Creature.bStored||(!Override&&(!Creature.bTamed||Creature.bInCombat||Creature.OwnerId!=Actor&&!Terminal->AllowedIds.Contains(Creature.OwnerId))))return false;
 if(Creature.bHybrid&&!Terminal->bAllowHybrids)return false;
 if(!FMath::IsFinite(Distance)||Distance<0.f||(ViaGun&&Distance>Terminal->Range&&!Override))return false;
 if(StoredCreatureIds.Contains(Creature.Id)||(Terminal->Capacity>=0&&Terminal->Creatures.Num()>=Terminal->Capacity))return false;
 Creature.bStored=true;
 Terminal->Creatures.Add(MoveTemp(Creature));
 StoredCreatureIds.Add(Terminal->Creatures.Last().Id);
 return true;
}
bool UAnomaliaZPrigimaliaCryoSubsystem::ReleaseCreature(const FString& Id,const FString& CreatureId,const FString& Actor,bool Admin,bool SpawnAllowed,FAnomaliaZPrigimaliaCryoCreature& OutCreature)
{
 FAnomaliaZPrigimaliaCryoTerminal* Terminal=Terminals.Find(Id);
 if(!Terminal||!CanAccess(*Terminal,Actor,Admin)||!SpawnAllowed)return false;
 const int32 Index=Terminal->Creatures.IndexOfByPredicate([&](const FAnomaliaZPrigimaliaCryoCreature& C){return C.Id==CreatureId;});
 if(Index==INDEX_NONE)return false;
 OutCreature=Terminal->Creatures[Index];OutCreature.bStored=false;
 Terminal->Creatures.RemoveAt(Index);
 StoredCreatureIds.Remove(CreatureId);
 return true;
}
bool UAnomaliaZPrigimaliaCryoSubsystem::ConfigureTerminal(const FString& Id,const FString& Actor,bool Admin,float Range,int32 Capacity,bool AllowHybrids)
{
 FAnomaliaZPrigimaliaCryoTerminal* Terminal=Terminals.Find(Id);
 if(!Terminal||Actor.IsEmpty()||(!Admin&&Actor!=Terminal->OwnerId)||!FMath::IsFinite(Range)||Capacity< -1)return false;
 if(Capacity>=0&&Capacity<Terminal->Creatures.Num())return false;
 Terminal->Range=FMath::Clamp(Range,1.f,200.f);Terminal->Capacity=Capacity;Terminal->bAllowHybrids=AllowHybrids;return true;
}
bool UAnomaliaZPrigimaliaCryoSubsystem::GetTerminal(const FString& Id,FAnomaliaZPrigimaliaCryoTerminal& OutTerminal) const
{
 const FAnomaliaZPrigimaliaCryoTerminal* Terminal=Terminals.Find(Id);
 if(!Terminal)return false;
 OutTerminal=*Terminal;return true;
}