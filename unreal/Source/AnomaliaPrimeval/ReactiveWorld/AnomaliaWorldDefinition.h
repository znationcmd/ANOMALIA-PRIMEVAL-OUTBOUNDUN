#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "AnomaliaWorldDefinition.generated.h"

class UStaticMesh;

UENUM(BlueprintType)
enum class EAnomaliaWorldMechanism : uint8 { Repair, Generator, Junction, Consumer, Access, Portal };
UENUM(BlueprintType)
enum class EAnomaliaRepairState : uint8 { Destroyed, Repairing, Repaired, Disabled };

/** Designer-authored recipes. Runtime state belongs to the server, never to this asset. */
UCLASS(BlueprintType)
class ANOMALIAPRIMEVAL_API UAnomaliaWorldDefinition : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FName DefinitionId;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) EAnomaliaWorldMechanism Kind = EAnomaliaWorldMechanism::Repair;
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
struct FAnomaliaMaterialDeposit
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) FName Key;
    UPROPERTY(BlueprintReadOnly) int32 Value = 0;
};

USTRUCT(BlueprintType)
struct FAnomaliaMechanismState
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) EAnomaliaRepairState Repair = EAnomaliaRepairState::Destroyed;
    UPROPERTY(BlueprintReadOnly) TArray<FAnomaliaMaterialDeposit> Deposited;
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
        FAnomaliaMaterialDeposit Pair;Pair.Key=Id;Pair.Value=Units;Deposited.Add(Pair);
    }
};
