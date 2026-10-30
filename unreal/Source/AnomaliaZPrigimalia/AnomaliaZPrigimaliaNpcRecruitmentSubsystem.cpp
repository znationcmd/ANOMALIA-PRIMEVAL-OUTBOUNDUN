#include "AnomaliaZPrigimaliaNpcRecruitmentSubsystem.h"
#include "AnomaliaZPrigimaliaGameMode.h"
#include "GameFramework/Controller.h"
#include "Engine/World.h"

namespace
{
    constexpr float MaxTorpor = 100.f;
    constexpr float BindRangeMeters = 3.f;
    constexpr float RopeRangeMeters = 14.f;
    constexpr float TrainingBaseSeconds = 90.f;

    bool IsWorkRole(EAnomaliaZPrigimaliaRecruitRole Role)
    {
        return Role == EAnomaliaZPrigimaliaRecruitRole::Blacksmith ||
            Role == EAnomaliaZPrigimaliaRecruitRole::Tanner ||
            Role == EAnomaliaZPrigimaliaRecruitRole::Carpenter ||
            Role == EAnomaliaZPrigimaliaRecruitRole::Cook ||
            Role == EAnomaliaZPrigimaliaRecruitRole::Farmer;
    }
}

bool UAnomaliaZPrigimaliaNpcRecruitmentSubsystem::IsAuthoritative() const
{
    return GetWorld() && GetWorld()->GetNetMode() != NM_Client;
}

FString UAnomaliaZPrigimaliaNpcRecruitmentSubsystem::ServerPlayerId(const AController* Controller) const
{
    if (!IsAuthoritative() || !IsValid(Controller) || Controller->GetWorld() != GetWorld())
        return FString();
    const AAnomaliaZPrigimaliaGameMode* GameMode = GetWorld()->GetAuthGameMode<AAnomaliaZPrigimaliaGameMode>();
    return GameMode ? GameMode->GetPersistentPlayerId(Controller) : FString();
}

bool UAnomaliaZPrigimaliaNpcRecruitmentSubsystem::CanManage(
    const FAnomaliaZPrigimaliaRecruitmentStation& Station, const AController* Controller) const
{
    const FString PlayerId = ServerPlayerId(Controller);
    return !PlayerId.IsEmpty() && Station.OwnerId == PlayerId;
}

bool UAnomaliaZPrigimaliaNpcRecruitmentSubsystem::RegisterWorldNpc(const FAnomaliaZPrigimaliaRecruitNpcState& Npc)
{
    if (!IsAuthoritative() || Npc.Id.IsEmpty() || Npcs.Contains(Npc.Id) ||
        !FMath::IsFinite(Npc.Health) || !FMath::IsFinite(Npc.Torpor) ||
        Npc.Status != EAnomaliaZPrigimaliaRecruitStatus::World || Npc.bDead)
        return false;
    FAnomaliaZPrigimaliaRecruitNpcState Copy = Npc;
    Copy.Level = FMath::Clamp(Copy.Level, 1, 100);
    Copy.Health = FMath::Clamp(Copy.Health, 0.f, 100.f);
    Copy.Torpor = FMath::Clamp(Copy.Torpor, 0.f, MaxTorpor);
    Copy.TrainingProgress = 0.f;
    Copy.bUnconscious = Copy.Torpor >= MaxTorpor;
    Copy.BoundByPlayerId.Empty();
    Copy.StationId.Empty();
    Npcs.Add(Copy.Id, MoveTemp(Copy));
    return true;
}

bool UAnomaliaZPrigimaliaNpcRecruitmentSubsystem::RegisterStation(
    const FString& StationId, AController* OwnerController)
{
    const FString OwnerId = ServerPlayerId(OwnerController);
    if (StationId.IsEmpty() || OwnerId.IsEmpty() || Stations.Contains(StationId))
        return false;
    FAnomaliaZPrigimaliaRecruitmentStation Station;
    Station.Id = StationId;
    Station.OwnerId = OwnerId;
    Stations.Add(StationId, MoveTemp(Station));
    return true;
}

bool UAnomaliaZPrigimaliaNpcRecruitmentSubsystem::ApplyNonlethalStrike(
    const FString& NpcId, float TorporAmount)
{
    if (!IsAuthoritative() || !FMath::IsFinite(TorporAmount) || TorporAmount <= 0.f)
        return false;
    FAnomaliaZPrigimaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
    if (!Npc || Npc->bDead || Npc->Status != EAnomaliaZPrigimaliaRecruitStatus::World)
        return false;
    Npc->Torpor = FMath::Clamp(Npc->Torpor + TorporAmount, 0.f, MaxTorpor);
    Npc->bUnconscious = Npc->Torpor >= MaxTorpor;
    return true;
}

bool UAnomaliaZPrigimaliaNpcRecruitmentSubsystem::BindNpc(
    const FString& NpcId, AController* Controller, bool bServerVerifiedRope,
    float DistanceMeters)
{
    const FString PlayerId = ServerPlayerId(Controller);
    FAnomaliaZPrigimaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
    if (PlayerId.IsEmpty() || !Npc || Npc->bDead || !Npc->bUnconscious ||
        Npc->Status != EAnomaliaZPrigimaliaRecruitStatus::World || !bServerVerifiedRope ||
        !FMath::IsFinite(DistanceMeters) || DistanceMeters < 0.f ||
        DistanceMeters > BindRangeMeters ||
        (!Npc->BoundByPlayerId.IsEmpty() && Npc->BoundByPlayerId != PlayerId))
        return false;
    Npc->BoundByPlayerId = PlayerId;
    return true;
}

bool UAnomaliaZPrigimaliaNpcRecruitmentSubsystem::DragNpc(
    const FString& NpcId, AController* Controller, float DistanceMeters,
    bool bClimbing, float& OutSpeedMultiplier)
{
    OutSpeedMultiplier = 1.f;
    const FString PlayerId = ServerPlayerId(Controller);
    FAnomaliaZPrigimaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
    if (PlayerId.IsEmpty() || !Npc || Npc->BoundByPlayerId != PlayerId ||
        Npc->Status != EAnomaliaZPrigimaliaRecruitStatus::World ||
        !FMath::IsFinite(DistanceMeters) || DistanceMeters < 0.f)
        return false;
    if (DistanceMeters > RopeRangeMeters || bClimbing)
    {
        Npc->BoundByPlayerId.Empty();
        return false;
    }
    OutSpeedMultiplier = 0.5f;
    return true;
}

bool UAnomaliaZPrigimaliaNpcRecruitmentSubsystem::AdmitNpc(
    const FString& StationId, const FString& NpcId, AController* Controller)
{
    FAnomaliaZPrigimaliaRecruitmentStation* Station = Stations.Find(StationId);
    FAnomaliaZPrigimaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
    if (!Station || !Station->bActive || !CanManage(*Station, Controller) ||
        !Npc || Npc->bDead || !Npc->bUnconscious ||
        Npc->Status != EAnomaliaZPrigimaliaRecruitStatus::World ||
        Npc->BoundByPlayerId != Station->OwnerId || Station->RecruitIds.Contains(NpcId))
        return false;
    Npc->BoundByPlayerId.Empty();
    Npc->StationId = StationId;
    Npc->Level = FMath::Clamp(Npc->Level, 1, 100);
    Npc->TrainingProgress = 0.f;
    Npc->Status = EAnomaliaZPrigimaliaRecruitStatus::Training;
    Station->RecruitIds.Add(NpcId);
    return true;
}

TArray<FString> UAnomaliaZPrigimaliaNpcRecruitmentSubsystem::AdvanceTraining(
    const FString& StationId, float DeltaSeconds, int32 ConsumedSupplies)
{
    TArray<FString> Ready;
    FAnomaliaZPrigimaliaRecruitmentStation* Station = Stations.Find(StationId);
    if (!IsAuthoritative() || !Station || !Station->bActive ||
        !FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.f || ConsumedSupplies <= 0)
        return Ready;
    for (const FString& NpcId : Station->RecruitIds)
    {
        FAnomaliaZPrigimaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
        if (!Npc || Npc->Status != EAnomaliaZPrigimaliaRecruitStatus::Training) continue;
        Npc->TrainingProgress = FMath::Clamp(
            Npc->TrainingProgress +
                DeltaSeconds / (TrainingBaseSeconds * FMath::Max(1, Npc->Level)) * 100.f,
            0.f, 100.f);
        if (Npc->TrainingProgress >= 100.f)
        {
            Npc->Status = EAnomaliaZPrigimaliaRecruitStatus::Ready;
            Ready.Add(NpcId);
        }
    }
    return Ready;
}

bool UAnomaliaZPrigimaliaNpcRecruitmentSubsystem::BeginDeployment(
    const FString& StationId, const FString& NpcId, AController* Controller,
    bool bServerVerifiedPlacement, EAnomaliaZPrigimaliaRecruitRole Role,
    FAnomaliaZPrigimaliaRecruitNpcState& OutNpc)
{
    FAnomaliaZPrigimaliaRecruitmentStation* Station = Stations.Find(StationId);
    FAnomaliaZPrigimaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
    if (!bServerVerifiedPlacement || !Station || !Station->bActive ||
        !CanManage(*Station, Controller) || !Station->RecruitIds.Contains(NpcId) ||
        !Npc || Npc->Status != EAnomaliaZPrigimaliaRecruitStatus::Ready ||
        Npc->StationId != StationId)
        return false;
    Npc->Status = EAnomaliaZPrigimaliaRecruitStatus::PendingDeployment;
    Npc->Role = Role;
    OutNpc = *Npc;
    OutNpc.OwnerId = Station->OwnerId;
    OutNpc.BoundByPlayerId.Empty();
    OutNpc.bUnconscious = false;
    OutNpc.Torpor = 0.f;
    OutNpc.Status = EAnomaliaZPrigimaliaRecruitStatus::Deployed;
    OutNpc.StationId.Empty();
    return true;
}

bool UAnomaliaZPrigimaliaNpcRecruitmentSubsystem::FinishDeployment(
    const FString& StationId, const FString& NpcId, AController* Controller,
    bool bWorldSpawnSucceeded)
{
    FAnomaliaZPrigimaliaRecruitmentStation* Station = Stations.Find(StationId);
    FAnomaliaZPrigimaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
    if (!Station || !CanManage(*Station, Controller) ||
        !Station->RecruitIds.Contains(NpcId) || !Npc ||
        Npc->Status != EAnomaliaZPrigimaliaRecruitStatus::PendingDeployment)
        return false;
    if (!bWorldSpawnSucceeded)
    {
        Npc->Status = EAnomaliaZPrigimaliaRecruitStatus::Ready;
        return true; // Roll back reservation; the NPC remains in the station.
    }
    Npc->Status = EAnomaliaZPrigimaliaRecruitStatus::Deployed;
    Npc->OwnerId = Station->OwnerId;
    Npc->BoundByPlayerId.Empty();
    Npc->bUnconscious = false;
    Npc->Torpor = 0.f;
    Npc->StationId.Empty();
    Station->RecruitIds.RemoveSingle(NpcId);
    return true;
}

bool UAnomaliaZPrigimaliaNpcRecruitmentSubsystem::AssignRole(
    const FString& NpcId, AController* Controller,
    EAnomaliaZPrigimaliaRecruitRole Role, FName WorkshopType)
{
    FAnomaliaZPrigimaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
    const FString PlayerId = ServerPlayerId(Controller);
    if (!Npc || Npc->Status != EAnomaliaZPrigimaliaRecruitStatus::Deployed ||
        PlayerId.IsEmpty() || PlayerId != Npc->OwnerId ||
        (!WorkshopType.IsNone() && !IsWorkRole(Role)))
        return false;
    Npc->Role = Role;
    Npc->WorkshopType = WorkshopType;
    return true;
}

bool UAnomaliaZPrigimaliaNpcRecruitmentSubsystem::GetNpc(
    const FString& NpcId, FAnomaliaZPrigimaliaRecruitNpcState& OutNpc) const
{
    const FAnomaliaZPrigimaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
    if (!Npc) return false;
    OutNpc = *Npc;
    return true;
}

bool UAnomaliaZPrigimaliaNpcRecruitmentSubsystem::GetStation(
    const FString& StationId, FAnomaliaZPrigimaliaRecruitmentStation& OutStation) const
{
    const FAnomaliaZPrigimaliaRecruitmentStation* Station = Stations.Find(StationId);
    if (!Station) return false;
    OutStation = *Station;
    return true;
}
