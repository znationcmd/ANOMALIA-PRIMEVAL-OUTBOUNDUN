#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "AnomaliaZPrigimaliaWorldDefinition.generated.h"

class UStaticMesh;

UENUM(BlueprintType)
enum class EAnomaliaZPrigimaliaWorldMechanism : uint8 { Repair, Generator, Junction, Consumer, Access, Portal };
UENUM(BlueprintType)
enum class EAnomaliaZPrigimaliaRepairState : uint8 { Destroyed, Repairing, Repaired, Disabled };

/** Designer-authored recipes. Runtime state belongs to the server, never to this asset. */
UCLASS(BlueprintType)
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaWorldDefinition : public UDataAsset
{
    GENERATED_BODY()
public:
    UAnomaliaZPrigimaliaWorldDefinition()
    { Materials.Add(TEXT("metal_sheet"),100);Materials.Add(TEXT("plank"),50); }
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FName DefinitionId;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) EAnomaliaZPrigimaliaWorldMechanism Kind = EAnomaliaZPrigimaliaWorldMechanism::Repair;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TMap<FName,int32> Materials;
    /** Ordered art stages; no engine primitives or external assets are substituted. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TArray<TSoftObjectPtr<UStaticMesh>> RepairStages;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TSoftObjectPtr<UStaticMesh> RepairedMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0")) float RepairSeconds = 10;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FName FuelItem = TEXT("gasoline");
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0")) float FuelSecondsPerItem = 300;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0")) float OutputWatts = 1000;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0")) float DemandWatts = 100;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="1")) float CableRangeCm = 3000;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FName RequiredCard;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) bool bConsumeCard = false;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) bool bRequiresPower = false;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TMap<FName,int32> PortalComponents;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FName RequiredEvent = TEXT("electromagnetic_storm");
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="1")) float PortalSeconds = 120;
};

USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaMaterialDeposit
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) FName Key;
    UPROPERTY(BlueprintReadOnly) int32 Value = 0;
};

USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaMechanismState
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) EAnomaliaZPrigimaliaRepairState Repair = EAnomaliaZPrigimaliaRepairState::Destroyed;
    UPROPERTY(BlueprintReadOnly) TArray<FAnomaliaZPrigimaliaMaterialDeposit> Deposited;
    UPROPERTY(BlueprintReadOnly) double RepairEndsUtc = 0;
    UPROPERTY(BlueprintReadOnly) double FuelSeconds = 0;
    UPROPERTY(BlueprintReadOnly) bool bSwitchedOn = false;
    UPROPERTY(BlueprintReadOnly) bool bUnlocked = false;
    UPROPERTY(BlueprintReadOnly) double PortalEndsUtc = 0;
    int32 GetDeposited(FName Id) const
    { for(const auto& Pair:Deposited) if(Pair.Key==Id) return Pair.Value;return 0; }
    void AddDeposited(FName Id,int32 Units)
    {
        for(auto& Pair:Deposited) if(Pair.Key==Id) {Pair.Value+=Units;return;}
        FAnomaliaZPrigimaliaMaterialDeposit Pair;Pair.Key=Id;Pair.Value=Units;Deposited.Add(Pair);
    }
};
