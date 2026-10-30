#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "AnomaliaZPrigimaliaWorldDefinition.h"
#include "AnomaliaZPrigimaliaWorldStateSubsystem.generated.h"

class AAnomaliaZPrigimaliaWorldMechanism;
class AAnomaliaZPrigimaliaSurvivor;
class UAnomaliaZPrigimaliaInventoryComponent;
class FJsonObject;

/** One journal per server and map. Actors replicate projections, the subsystem never replicates. */
UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaWorldStateSubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()
public:
    bool Configure(const FString& Server, const FString& Map, FString& Error);
    bool Register(AAnomaliaZPrigimaliaWorldMechanism* Actor);
    void Unregister(AAnomaliaZPrigimaliaWorldMechanism* Actor);
    bool Interact(AAnomaliaZPrigimaliaWorldMechanism* Actor, AAnomaliaZPrigimaliaSurvivor* User, FString& Error);
    bool HasPendingPlayer(const FString& Player) const;
    bool IsReady() const { return bReady; }
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|World")
    bool StartWorldEvent(FName EventId, float DurationSeconds);
    UFUNCTION(BlueprintPure, Category="ANOMALIA|World") bool IsEventActive(FName EventId) const;
    const FAnomaliaZPrigimaliaMechanismState* FindState(FName Id) const { return States.Find(Id); }
    virtual bool DoesSupportWorldType(EWorldType::Type Type) const override;
    virtual void Tick(float DeltaTime) override;
    virtual TStatId GetStatId() const override;
private:
    friend class FAnomaliaZPrigimaliaReactiveWorldTest;
    FString ServerId, StateId;
    bool bReady = false, bConfigured = false;
    float Accumulator = 0;
    TMap<FName,FAnomaliaZPrigimaliaMechanismState> States;
    TMap<FName,TWeakObjectPtr<AAnomaliaZPrigimaliaWorldMechanism>> Actors;
    FName Event;
    double EventEndsUtc = 0;
    TSharedPtr<FJsonObject> Pending;
    TWeakObjectPtr<UAnomaliaZPrigimaliaInventoryComponent> PendingInventory;
    bool Save(FString& Error);
    bool Read(const FString& Raw, FString& Error);
    bool Recover(FString& Error);
    bool CommitWithInventory(AAnomaliaZPrigimaliaSurvivor* User, const TMap<FName,int32>& Cost, FString& Error);
    void RefreshActors();
    void SolvePower();
};
