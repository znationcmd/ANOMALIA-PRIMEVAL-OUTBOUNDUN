#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "AnomaliaZPrigimaliaNpcRecruitmentSubsystem.generated.h"

class AController;

/** Native UE5 port of src/npc-recruitment.js. Fictional NPCs, non-lethal gameplay. */
UENUM(BlueprintType)
enum class EAnomaliaZPrigimaliaRecruitRole : uint8
{
    Fighter, Archer, Performer, Blacksmith, Tanner, Carpenter, Cook, Farmer
};

UENUM(BlueprintType)
enum class EAnomaliaZPrigimaliaRecruitStatus : uint8
{
    World, Training, Ready, PendingDeployment, Deployed
};

USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaRecruitNpcState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Id;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Name = TEXT("Recrue");
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString OwnerId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName AppearanceId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FName> EquipmentIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TMap<FName, FString> ExtensionData;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 Level = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float Health = 100.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float Torpor = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float TrainingProgress = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) EAnomaliaZPrigimaliaRecruitRole Role = EAnomaliaZPrigimaliaRecruitRole::Fighter;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) EAnomaliaZPrigimaliaRecruitStatus Status = EAnomaliaZPrigimaliaRecruitStatus::World;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bDead = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bUnconscious = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString BoundByPlayerId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString StationId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName WorkshopType;
};

USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaRecruitmentStation
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly) FString Id;
    UPROPERTY(BlueprintReadOnly) FString OwnerId;
    UPROPERTY(BlueprintReadOnly) TArray<FString> RecruitIds;
    UPROPERTY(BlueprintReadOnly) bool bActive = true;
};

/**
 * SERVER-SIDE STATE ONLY; neither replicated nor persistent yet.
 * Controller identities come from AnomaliaZPrigimaliaGameMode, never client-provided strings.
 * Call from trusted server actors after validating combat hits, rope inventory,
 * distance, supplied resources and spawn placement.
 */
UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaNpcRecruitmentSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    /** Called only by authoritative NPC spawning/restore logic. */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Recruitment")
    bool RegisterWorldNpc(const FAnomaliaZPrigimaliaRecruitNpcState& Npc);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Recruitment")
    bool RegisterStation(const FString& StationId, AController* OwnerController);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Recruitment")
    bool ApplyNonlethalStrike(const FString& NpcId, float TorporAmount = 25.f);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Recruitment")
    bool BindNpc(const FString& NpcId, AController* Controller, bool bServerVerifiedRope, float DistanceMeters);

    /** Returns false and clears the rope if climbing or beyond 14 m. */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Recruitment")
    bool DragNpc(const FString& NpcId, AController* Controller, float DistanceMeters, bool bClimbing, float& OutSpeedMultiplier);

    /** Returns true if NPC was moved to station's *data*; despawn world actor separately. */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Recruitment")
    bool AdmitNpc(const FString& StationId, const FString& NpcId, AController* Controller);

    /** Supply consumption must be validated/performed by authoritative inventory logic. */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Recruitment")
    TArray<FString> AdvanceTraining(const FString& StationId, float DeltaSeconds, int32 ConsumedSupplies);

    /** Reserves one ready recruit and supplies all data for safe world-spawn checks. */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Recruitment")
    bool BeginDeployment(const FString& StationId, const FString& NpcId, AController* Controller, bool bServerVerifiedPlacement, EAnomaliaZPrigimaliaRecruitRole Role, FAnomaliaZPrigimaliaRecruitNpcState& OutNpc);

    /** Commit only after spawn succeeded; false rolls reservation back to Ready. */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Recruitment")
    bool FinishDeployment(const FString& StationId, const FString& NpcId, AController* Controller, bool bWorldSpawnSucceeded);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Recruitment")
    bool AssignRole(const FString& NpcId, AController* Controller, EAnomaliaZPrigimaliaRecruitRole Role, FName WorkshopType);

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Recruitment")
    bool GetNpc(const FString& NpcId, FAnomaliaZPrigimaliaRecruitNpcState& OutNpc) const;

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Recruitment")
    bool GetStation(const FString& StationId, FAnomaliaZPrigimaliaRecruitmentStation& OutStation) const;

private:
    UPROPERTY() TMap<FString, FAnomaliaZPrigimaliaRecruitNpcState> Npcs;
    UPROPERTY() TMap<FString, FAnomaliaZPrigimaliaRecruitmentStation> Stations;

    bool IsAuthoritative() const;
    FString ServerPlayerId(const AController* Controller) const;
    bool CanManage(const FAnomaliaZPrigimaliaRecruitmentStation& Station, const AController* Controller) const;
};
