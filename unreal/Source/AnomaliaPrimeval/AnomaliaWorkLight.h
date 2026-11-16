#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaWorkLight.generated.h"

class USceneComponent;
class UStaticMeshComponent;
class USpotLightComponent;
class AAnomaliaPowerGenerator;

/** Construction floodlight; actual replicated light emission follows generator power. */
UCLASS(Blueprintable)
class ANOMALIAPRIMEVAL_API AAnomaliaWorkLight : public AActor
{
    GENERATED_BODY()

public:
    AAnomaliaWorkLight();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Electricity")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Electricity")
    TObjectPtr<UStaticMeshComponent> VisualMesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Electricity")
    TObjectPtr<USpotLightComponent> FloodBeam;

    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category="ANOMALIA|Electricity|Persistence")
    FString PersistentId;

    UPROPERTY(EditInstanceOnly, Replicated, BlueprintReadOnly, Category="ANOMALIA|Electricity")
    TObjectPtr<AAnomaliaPowerGenerator> PowerGenerator;

    UPROPERTY(Replicated, BlueprintReadOnly, Category="ANOMALIA|Electricity")
    bool bSwitchedOn = true;

    UPROPERTY(ReplicatedUsing=OnRep_Lit, BlueprintReadOnly, Category="ANOMALIA|Electricity")
    bool bIsLit = false;

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Electricity")
    bool SetSwitchedOnServer(bool bOn);

    virtual void Tick(float DeltaSeconds) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    UFUNCTION()
    void OnRep_Lit();

private:
    float SaveElapsedSeconds = 0.f;
    bool bPersistenceEnabled = false;
    bool GetSavePath(FString& OutFile) const;
    bool LoadServerState();
    bool SaveServerState() const;
};
