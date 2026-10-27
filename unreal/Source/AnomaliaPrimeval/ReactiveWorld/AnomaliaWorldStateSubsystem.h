#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "AnomaliaWorldDefinition.h"
#include "AnomaliaWorldStateSubsystem.generated.h"

class AAnomaliaWorldMechanism;
class AAnomaliaSurvivor;
class UAnomaliaInventoryComponent;
class FJsonObject;

/** One journal per server and map. Actors replicate projections, the subsystem never replicates. */
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaWorldStateSubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()
public:
    bool Configure(const FString& Server, const FString& Map, FString& Error);
    bool Register(AAnomaliaWorldMechanism* Actor);
    void Unregister(AAnomaliaWorldMechanism* Actor);
    bool Interact(AAnomaliaWorldMechanism* Actor, AAnomaliaSurvivor* User, FString& Error);
    bool HasPendingPlayer(const FString& Player) const;
    bool IsReady() const { return bReady; }
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|World")
    bool StartWorldEvent(FName EventId, float DurationSeconds);
    UFUNCTION(BlueprintPure, Category="ANOMALIA|World") bool IsEventActive(FName EventId) const;
    const FAnomaliaMechanismState* FindState(FName Id) const { return States.Find(Id); }
    virtual bool DoesSupportWorldType(EWorldType::Type Type) const override;
    virtual void Tick(float DeltaTime) override;
    virtual TStatId GetStatId() const override;
private:
    friend class FAnomaliaReactiveWorldTest;
    FString ServerId, StateId;
    bool bReady = false, bConfigured = false;
    float Accumulator = 0;
    TMap<FName,FAnomaliaMechanismState> States;
    TMap<FName,TWeakObjectPtr<AAnomaliaWorldMechanism>> Actors;
    FName Event;
    double EventEndsUtc = 0;
    TSharedPtr<FJsonObject> Pending;
    TWeakObjectPtr<UAnomaliaInventoryComponent> PendingInventory;
    bool Save(FString& Error);
    bool Read(const FString& Raw, FString& Error);
    bool Recover(FString& Error);
    bool CommitWithInventory(AAnomaliaSurvivor* User, const TMap<FName,int32>& Cost, FString& Error);
    void RefreshActors();
    void SolvePower();
};
