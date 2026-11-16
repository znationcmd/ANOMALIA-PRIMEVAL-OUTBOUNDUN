#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaPowerGenerator.generated.h"

class USceneComponent;
class UStaticMeshComponent;

/** Place a Blueprint child with an actual generator mesh. No generic client fuel/ownership RPC is exposed. */
UCLASS(Blueprintable)
class ANOMALIAPRIMEVAL_API AAnomaliaPowerGenerator : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaPowerGenerator();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Power")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Power")
    TObjectPtr<UStaticMeshComponent> VisualMesh;

    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category="ANOMALIA|Power|Persistence")
    FString PersistentId;

    UPROPERTY(Replicated, BlueprintReadOnly, Category="ANOMALIA|Power")
    bool bRunning = false;

    UPROPERTY(Replicated, BlueprintReadOnly, Category="ANOMALIA|Power")
    float FuelLitres = 10.f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Power", meta=(ClampMin="0.01", ClampMax="30"))
    float LitresPerHour = 0.6f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Power", meta=(ClampMin="100", ClampMax="5000"))
    float MaxCableDistanceCm = 1500.f;

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Power")
    bool SetRunningOnServer(bool bStart);

    /** Trusted server gameplay calls this only after consuming a real fuel item. */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Power")
    bool RefuelOnServer(float Litres);

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Power")
    bool IsSupplyingActor(const AActor* Target) const;

    virtual void Tick(float DeltaSeconds) override;

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
    bool bPersistenceEnabled = false;
    float SaveElapsedSeconds = 0.f;
    bool GetSavePath(FString& OutFile) const;
    bool LoadServerState();
    bool SaveServerState() const;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
