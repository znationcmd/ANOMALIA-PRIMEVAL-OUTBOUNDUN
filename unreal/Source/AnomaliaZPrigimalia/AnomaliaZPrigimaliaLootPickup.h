#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaZPrigimaliaLootPickup.generated.h"
class UStaticMeshComponent;
class UTextRenderComponent;

/** A generic labelled pickup until each item receives an authorised production mesh. */
UCLASS()
class ANOMALIAZPRIGIMALIA_API AAnomaliaZPrigimaliaLootPickup : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaZPrigimaliaLootPickup();
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Mesh;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UTextRenderComponent> Label;
    UPROPERTY(ReplicatedUsing=OnRep_Item, BlueprintReadOnly) FName ItemId;
    UPROPERTY(ReplicatedUsing=OnRep_Item, BlueprintReadOnly) int32 Count = 0;
    UPROPERTY(ReplicatedUsing=OnRep_Item, BlueprintReadOnly) FString DisplayName;
    // Identity is server owned, never an argument accepted from a client RPC.
    FString SpawnId, Generation;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    void Configure(FName Id, int32 Quantity, const FString& Name);
private:
    UFUNCTION() void OnRep_Item();
};
