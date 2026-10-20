#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "Furniture/AnomaliaFurnitureRules.h"
#include "AnomaliaFurnitureSubsystem.generated.h"

class AAnomaliaSurvivor;
class AAnomaliaHomesteadStation;
class FJsonObject;

UENUM(BlueprintType)
enum class EAnomaliaFurnitureCommand : uint8 { Place, Move, Remove, Undo, Redo };

/** Server-owned prototype furniture transactions. Does not edit legacy Editor/world.json. */
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaFurnitureSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()
public:
    bool LoadWorld(const FString& InServerId, FString& Error);
    bool Execute(AAnomaliaSurvivor* Caller, EAnomaliaFurnitureCommand Command,
        FName Type, const FString& Id, const FVector& Location, float Yaw, bool Confirmed, FString& Error);
private:
    AnomaliaFurniture::Layout Layout;
    FString ServerId, LoadedRaw;
    bool bReady = false;
    TSharedPtr<FJsonObject> SavedRoot;
    TMap<FString, TWeakObjectPtr<AAnomaliaHomesteadStation>> Actors;
    FString FilePath() const;
    bool Persist(const AnomaliaFurniture::Layout& Candidate, FString& Error);
    AAnomaliaHomesteadStation* SpawnRecord(const AnomaliaFurniture::Record& Record);
    bool ValidateChangedPose(AAnomaliaSurvivor* Caller, const AnomaliaFurniture::Record& Record, FString& Error) const;
};
