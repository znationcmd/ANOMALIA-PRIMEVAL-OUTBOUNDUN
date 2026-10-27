#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaWorldDefinition.h"
#include "AnomaliaWorldMechanism.generated.h"

class USceneComponent;
class UStaticMeshComponent;
class UBoxComponent;
class UPointLightComponent;
class AAnomaliaDoorActor;
class AAnomaliaSurvivor;

/** Native placeable for UE5/Blueprints. E is routed through the owned survivor RPC. */
UCLASS(Blueprintable)
class ANOMALIAPRIMEVAL_API AAnomaliaWorldMechanism : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaWorldMechanism();
    /** Must be unique within this map. Never derived from load order or object path. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|World") FName StableId;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|World") TObjectPtr<UAnomaliaWorldDefinition> Definition;
    /** Explicit undirected cable edges; proximity alone never establishes a connection. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Power") TArray<FName> ConnectedNodeIds;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Access") TObjectPtr<AAnomaliaDoorActor> ControlledDoor;
    /** Portal destination must be authored on the server in this loaded map. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Portal") TObjectPtr<AActor> Destination;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UStaticMeshComponent> Presentation;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UBoxComponent> InteractionBounds;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UPointLightComponent> PoweredLight;
    UPROPERTY(ReplicatedUsing=OnRep_State, BlueprintReadOnly) FAnomaliaMechanismState State;
    UPROPERTY(ReplicatedUsing=OnRep_State, BlueprintReadOnly) bool bPowered = false;
    UPROPERTY(ReplicatedUsing=OnRep_State, BlueprintReadOnly) bool bOverloaded = false;
    UPROPERTY(Replicated, BlueprintReadOnly) FName ActiveWorldEvent;
    UPROPERTY(Replicated, BlueprintReadOnly) double WorldEventEndsUtc = 0;
    /** Trusted server only. No target or material quantities are accepted from a client. */
    bool TryInteract(AAnomaliaSurvivor* User);
    bool CanInteract(const AAnomaliaSurvivor* User) const;
    void ApplyServerState(const FAnomaliaMechanismState& NewState, bool Power, bool Overload);
    UFUNCTION(BlueprintImplementableEvent, Category="ANOMALIA|World") void OnWorldStateChanged();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Props) const override;
    virtual void Tick(float DeltaSeconds) override;
protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    UFUNCTION() void OnRep_State();
};
