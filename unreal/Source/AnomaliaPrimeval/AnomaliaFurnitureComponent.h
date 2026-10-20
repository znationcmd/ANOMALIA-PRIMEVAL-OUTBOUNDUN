#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AnomaliaFurnitureSubsystem.h"
#include "AnomaliaFurnitureComponent.generated.h"

class UInputComponent;
class AAnomaliaHomesteadStation;

/** Owning-player RPC gateway. Owner/server IDs are never supplied by clients. */
UCLASS(ClassGroup=(ANOMALIA), meta=(BlueprintSpawnableComponent))
class ANOMALIAPRIMEVAL_API UAnomaliaFurnitureComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UAnomaliaFurnitureComponent();
    void BindInput(UInputComponent* Input);
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Furniture")
    void RequestPlace(FName Type, FVector Location, float Yaw);
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Furniture")
    void RequestMove(const FString& PlacementId, FVector Location, float Yaw);
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Furniture")
    void RequestRemove(const FString& PlacementId, bool bConfirmed);
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Furniture")
    void RequestUndo();
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Furniture")
    void RequestRedo();
    UFUNCTION(BlueprintImplementableEvent, Category="ANOMALIA|Furniture")
    void OnFurnitureResult(bool bSuccess, const FString& Message);
protected:
    UFUNCTION(Server, Reliable)
    void ServerRequest(EAnomaliaFurnitureCommand Command, FName Type, const FString& PlacementId,
        FVector Location, float Yaw, bool bConfirmed);
    UFUNCTION(Client, Reliable)
    void ClientResult(bool bSuccess, const FString& Message);
private:
    double LastRequestTime = -1.0;
    TWeakObjectPtr<AAnomaliaHomesteadStation> Selected;
    bool ViewHit(FHitResult& Hit, bool bIgnoreSelection) const;
    void PlaceBedFromView();
    void SelectFromView();
    void MoveSelectedToView();
    void RotateSelected();
    void InputUndo();
    void InputRedo();
};
