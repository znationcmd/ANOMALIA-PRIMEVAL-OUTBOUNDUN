#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaZPrigimaliaWorldDefinition.h"
#include "AnomaliaZPrigimaliaWorldMechanism.generated.h"

class USceneComponent;
class UStaticMeshComponent;
class UBoxComponent;
class UPointLightComponent;
class AAnomaliaZPrigimaliaDoorActor;
class AAnomaliaZPrigimaliaSurvivor;

/** Native placeable for UE5/Blueprints. E is routed through the owned survivor RPC. */
UCLASS(Blueprintable)
class ANOMALIAZPRIGIMALIA_API AAnomaliaZPrigimaliaWorldMechanism : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaZPrigimaliaWorldMechanism();
    /** Must be unique within this map. Never derived from load order or object path. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|World") FName StableId;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|World") TObjectPtr<UAnomaliaZPrigimaliaWorldDefinition> Definition;
    /** Explicit undirected cable edges; proximity alone never establishes a connection. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Power") TArray<FName> ConnectedNodeIds;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Access") TObjectPtr<AAnomaliaZPrigimaliaDoorActor> ControlledDoor;
    /** Portal destination must be authored on the server in this loaded map. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Portal") TObjectPtr<AActor> Destination;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UStaticMeshComponent> Presentation;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UBoxComponent> InteractionBounds;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UPointLightComponent> PoweredLight;
    UPROPERTY(ReplicatedUsing=OnRep_State, BlueprintReadOnly) FAnomaliaZPrigimaliaMechanismState State;
    UPROPERTY(ReplicatedUsing=OnRep_State, BlueprintReadOnly) bool bPowered = false;
    UPROPERTY(ReplicatedUsing=OnRep_State, BlueprintReadOnly) bool bOverloaded = false;
    UPROPERTY(Replicated, BlueprintReadOnly) FName ActiveWorldEvent;
    UPROPERTY(Replicated, BlueprintReadOnly) double WorldEventEndsUtc = 0;
    /** Trusted server only. No target or material quantities are accepted from a client. */
    bool TryInteract(AAnomaliaZPrigimaliaSurvivor* User);
    bool CanInteract(const AAnomaliaZPrigimaliaSurvivor* User) const;
    void ApplyServerState(const FAnomaliaZPrigimaliaMechanismState& NewState, bool Power, bool Overload);
    UFUNCTION(BlueprintImplementableEvent, Category="ANOMALIA|World") void OnWorldStateChanged();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Props) const override;
    virtual void Tick(float DeltaSeconds) override;
protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    UFUNCTION() void OnRep_State();
};
