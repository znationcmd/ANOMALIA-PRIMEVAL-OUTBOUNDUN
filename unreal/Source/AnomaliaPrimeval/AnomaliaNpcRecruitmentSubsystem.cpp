#include "AnomaliaNpcRecruitmentSubsystem.h"
#include "AnomaliaGameMode.h"
#include "GameFramework/Controller.h"
#include "Engine/World.h"

namespace
{
    constexpr float MaxTorpor = 100.f;
    constexpr float BindRangeMeters = 3.f;
    constexpr float RopeRangeMeters = 14.f;
    constexpr float TrainingBaseSeconds = 90.f;

    bool IsWorkRole(EAnomaliaRecruitRole Role)
    {
        return Role == EAnomaliaRecruitRole::Blacksmith ||
            Role == EAnomaliaRecruitRole::Tanner ||
            Role == EAnomaliaRecruitRole::Carpenter ||
            Role == EAnomaliaRecruitRole::Cook ||
            Role == EAnomaliaRecruitRole::Farmer;
    }
}

bool UAnomaliaNpcRecruitmentSubsystem::IsAuthoritative() const
{
    return GetWorld() && GetWorld()->GetNetMode() != NM_Client;
}

FString UAnomaliaNpcRecruitmentSubsystem::ServerPlayerId(const AController* Controller) const
{
    if (!IsAuthoritative() || !IsValid(Controller) || Controller->GetWorld() != GetWorld())
        return FString();
    const AAnomaliaGameMode* GameMode = GetWorld()->GetAuthGameMode<AAnomaliaGameMode>();
    return GameMode ? GameMode->GetPersistentPlayerId(Controller) : FString();
}

bool UAnomaliaNpcRecruitmentSubsystem::CanManage(
    const FAnomaliaRecruitmentStation& Station, const AController* Controller) const
{
    const FString PlayerId = ServerPlayerId(Controller);
    return !PlayerId.IsEmpty() && Station.OwnerId == PlayerId;
}

bool UAnomaliaNpcRecruitmentSubsystem::RegisterWorldNpc(const FAnomaliaRecruitNpcState& Npc)
{
    if (!IsAuthoritative() || Npc.Id.IsEmpty() || Npcs.Contains(Npc.Id) ||
        !FMath::IsFinite(Npc.Health) || !FMath::IsFinite(Npc.Torpor) ||
        Npc.Status != EAnomaliaRecruitStatus::World || Npc.bDead)
        return false;
    FAnomaliaRecruitNpcState Copy = Npc;
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

bool UAnomaliaNpcRecruitmentSubsystem::RegisterStation(
    const FString& StationId, AController* OwnerController)
{
    const FString OwnerId = ServerPlayerId(OwnerController);
    if (StationId.IsEmpty() || OwnerId.IsEmpty() || Stations.Contains(StationId))
        return false;
    FAnomaliaRecruitmentStation Station;
    Station.Id = StationId;
    Station.OwnerId = OwnerId;
    Stations.Add(StationId, MoveTemp(Station));
    return true;
}

bool UAnomaliaNpcRecruitmentSubsystem::ApplyNonlethalStrike(
    const FString& NpcId, float TorporAmount)
{
    if (!IsAuthoritative() || !FMath::IsFinite(TorporAmount) || TorporAmount <= 0.f)
        return false;
    FAnomaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
    if (!Npc || Npc->bDead || Npc->Status != EAnomaliaRecruitStatus::World)
        return false;
    Npc->Torpor = FMath::Clamp(Npc->Torpor + TorporAmount, 0.f, MaxTorpor);
    Npc->bUnconscious = Npc->Torpor >= MaxTorpor;
    return true;
}

bool UAnomaliaNpcRecruitmentSubsystem::BindNpc(
    const FString& NpcId, AController* Controller, bool bServerVerifiedRope,
    float DistanceMeters)
{
    const FString PlayerId = ServerPlayerId(Controller);
    FAnomaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
    if (PlayerId.IsEmpty() || !Npc || Npc->bDead || !Npc->bUnconscious ||
        Npc->Status != EAnomaliaRecruitStatus::World || !bServerVerifiedRope ||
        !FMath::IsFinite(DistanceMeters) || DistanceMeters < 0.f ||
        DistanceMeters > BindRangeMeters ||
        (!Npc->BoundByPlayerId.IsEmpty() && Npc->BoundByPlayerId != PlayerId))
        return false;
    Npc->BoundByPlayerId = PlayerId;
    return true;
}

bool UAnomaliaNpcRecruitmentSubsystem::DragNpc(
    const FString& NpcId, AController* Controller, float DistanceMeters,
    bool bClimbing, float& OutSpeedMultiplier)
{
    OutSpeedMultiplier = 1.f;
    const FString PlayerId = ServerPlayerId(Controller);
    FAnomaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
    if (PlayerId.IsEmpty() || !Npc || Npc->BoundByPlayerId != PlayerId ||
        Npc->Status != EAnomaliaRecruitStatus::World ||
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

bool UAnomaliaNpcRecruitmentSubsystem::AdmitNpc(
    const FString& StationId, const FString& NpcId, AController* Controller)
{
    FAnomaliaRecruitmentStation* Station = Stations.Find(StationId);
    FAnomaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
    if (!Station || !Station->bActive || !CanManage(*Station, Controller) ||
        !Npc || Npc->bDead || !Npc->bUnconscious ||
        Npc->Status != EAnomaliaRecruitStatus::World ||
        Npc->BoundByPlayerId != Station->OwnerId || Station->RecruitIds.Contains(NpcId))
        return false;
    Npc->BoundByPlayerId.Empty();
    Npc->StationId = StationId;
    Npc->Level = FMath::Clamp(Npc->Level, 1, 100);
    Npc->TrainingProgress = 0.f;
    Npc->Status = EAnomaliaRecruitStatus::Training;
    Station->RecruitIds.Add(NpcId);
    return true;
}

TArray<FString> UAnomaliaNpcRecruitmentSubsystem::AdvanceTraining(
    const FString& StationId, float DeltaSeconds, int32 ConsumedSupplies)
{
    TArray<FString> Ready;
    FAnomaliaRecruitmentStation* Station = Stations.Find(StationId);
    if (!IsAuthoritative() || !Station || !Station->bActive ||
        !FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.f || ConsumedSupplies <= 0)
        return Ready;
    for (const FString& NpcId : Station->RecruitIds)
    {
        FAnomaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
        if (!Npc || Npc->Status != EAnomaliaRecruitStatus::Training) continue;
        Npc->TrainingProgress = FMath::Clamp(
            Npc->TrainingProgress +
                DeltaSeconds / (TrainingBaseSeconds * FMath::Max(1, Npc->Level)) * 100.f,
            0.f, 100.f);
        if (Npc->TrainingProgress >= 100.f)
        {
            Npc->Status = EAnomaliaRecruitStatus::Ready;
            Ready.Add(NpcId);
        }
    }
    return Ready;
}

bool UAnomaliaNpcRecruitmentSubsystem::BeginDeployment(
    const FString& StationId, const FString& NpcId, AController* Controller,
    bool bServerVerifiedPlacement, EAnomaliaRecruitRole Role,
    FAnomaliaRecruitNpcState& OutNpc)
{
    FAnomaliaRecruitmentStation* Station = Stations.Find(StationId);
    FAnomaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
    if (!bServerVerifiedPlacement || !Station || !Station->bActive ||
        !CanManage(*Station, Controller) || !Station->RecruitIds.Contains(NpcId) ||
        !Npc || Npc->Status != EAnomaliaRecruitStatus::Ready ||
        Npc->StationId != StationId)
        return false;
    Npc->Status = EAnomaliaRecruitStatus::PendingDeployment;
    Npc->Role = Role;
    OutNpc = *Npc;
    OutNpc.OwnerId = Station->OwnerId;
    OutNpc.BoundByPlayerId.Empty();
    OutNpc.bUnconscious = false;
    OutNpc.Torpor = 0.f;
    OutNpc.Status = EAnomaliaRecruitStatus::Deployed;
    OutNpc.StationId.Empty();
    return true;
}

bool UAnomaliaNpcRecruitmentSubsystem::FinishDeployment(
    const FString& StationId, const FString& NpcId, AController* Controller,
    bool bWorldSpawnSucceeded)
{
    FAnomaliaRecruitmentStation* Station = Stations.Find(StationId);
    FAnomaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
    if (!Station || !CanManage(*Station, Controller) ||
        !Station->RecruitIds.Contains(NpcId) || !Npc ||
        Npc->Status != EAnomaliaRecruitStatus::PendingDeployment)
        return false;
    if (!bWorldSpawnSucceeded)
    {
        Npc->Status = EAnomaliaRecruitStatus::Ready;
        return true; // Roll back reservation; the NPC remains in the station.
    }
    Npc->Status = EAnomaliaRecruitStatus::Deployed;
    Npc->OwnerId = Station->OwnerId;
    Npc->BoundByPlayerId.Empty();
    Npc->bUnconscious = false;
    Npc->Torpor = 0.f;
    Npc->StationId.Empty();
    Station->RecruitIds.RemoveSingle(NpcId);
    return true;
}

bool UAnomaliaNpcRecruitmentSubsystem::AssignRole(
    const FString& NpcId, AController* Controller,
    EAnomaliaRecruitRole Role, FName WorkshopType)
{
    FAnomaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
    const FString PlayerId = ServerPlayerId(Controller);
    if (!Npc || Npc->Status != EAnomaliaRecruitStatus::Deployed ||
        PlayerId.IsEmpty() || PlayerId != Npc->OwnerId ||
        (!WorkshopType.IsNone() && !IsWorkRole(Role)))
        return false;
    Npc->Role = Role;
    Npc->WorkshopType = WorkshopType;
    return true;
}

bool UAnomaliaNpcRecruitmentSubsystem::GetNpc(
    const FString& NpcId, FAnomaliaRecruitNpcState& OutNpc) const
{
    const FAnomaliaRecruitNpcState* Npc = Npcs.Find(NpcId);
    if (!Npc) return false;
    OutNpc = *Npc;
    return true;
}

bool UAnomaliaNpcRecruitmentSubsystem::GetStation(
    const FString& StationId, FAnomaliaRecruitmentStation& OutStation) const
{
    const FAnomaliaRecruitmentStation* Station = Stations.Find(StationId);
    if (!Station) return false;
    OutStation = *Station;
    return true;
}
