#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaRefrigerator.generated.h"

class USceneComponent;
class UStaticMeshComponent;
class AAnomaliaPowerGenerator;
class AAnomaliaSurvivor;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FAnomaliaRefrigeratorUpdated);

USTRUCT(BlueprintType)
struct FAnomaliaRefrigeratorItem
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Fridge")
    FName ItemId;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Fridge")
    int32 Count = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Fridge")
    float Freshness01 = 1.f;
};

/** Authoritative world fridge: a placed Blueprint supplies the mesh and a generator reference.
 * Player requests must travel through the owning AAnomaliaSurvivor's server RPCs. */
UCLASS(Blueprintable)
class ANOMALIAPRIMEVAL_API AAnomaliaRefrigerator : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaRefrigerator();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Fridge")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Fridge")
    TObjectPtr<UStaticMeshComponent> VisualMesh;

    /** Must be unique, stable and explicitly assigned to each placed fridge; empty disables saving. */
    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category="ANOMALIA|Fridge|Persistence")
    FString PersistentId;

    /** Assign a generator placed within its cable range. */
    UPROPERTY(EditInstanceOnly, Replicated, BlueprintReadOnly, Category="ANOMALIA|Fridge|Electricity")
    TObjectPtr<AAnomaliaPowerGenerator> PowerGenerator;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Fridge", meta=(ClampMin="0", ClampMax="12"))
    float SetPointC = 4.f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Fridge", meta=(ClampMin="-15", ClampMax="45"))
    float AmbientTemperatureC = 22.f;

    UPROPERTY(Replicated, BlueprintReadOnly, Category="ANOMALIA|Fridge")
    float InternalTemperatureC = 22.f;

    UPROPERTY(Replicated, BlueprintReadOnly, Category="ANOMALIA|Fridge")
    bool bSwitchedOn = true;

    UPROPERTY(Replicated, BlueprintReadOnly, Category="ANOMALIA|Fridge")
    bool bCoolingActive = false;

    /** Shared by nearby players; server is the sole authority for quantities and freshness. */
    UPROPERTY(ReplicatedUsing=OnRep_Contents, BlueprintReadOnly, Category="ANOMALIA|Fridge")
    TArray<FAnomaliaRefrigeratorItem> Contents;

    UPROPERTY(BlueprintAssignable, Category="ANOMALIA|Fridge")
    FAnomaliaRefrigeratorUpdated OnRefrigeratorUpdated;

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Fridge")
    bool SetSwitchedOnServer(bool bOn);

    /** Called only by an owning player's validated server RPC or trusted server code. */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Fridge")
    bool DepositOnServer(AAnomaliaSurvivor* Player, FName ItemId, int32 Count);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Fridge")
    bool WithdrawOnServer(AAnomaliaSurvivor* Player, FName ItemId, int32 Count);

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Fridge")
    int32 GetUsedCapacity() const;

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Fridge")
    int32 GetMaxCapacity() const { return 40; }

    virtual void Tick(float DeltaSeconds) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    UFUNCTION()
    void OnRep_Contents();

private:
    bool bPersistenceEnabled = false;
    float UnsavedSeconds = 0.f;
    float AgingSeconds = 0.f;

    bool IsPlayerInReach(const AAnomaliaSurvivor* Player) const;
    bool GetSavePath(FString& OutFile) const;
    bool LoadServerState();
    bool SaveServerState() const;
    void NotifyChanged();
    static bool CanStore(FName ItemId);
    static bool ValidScopeId(const FString& Text);
};
