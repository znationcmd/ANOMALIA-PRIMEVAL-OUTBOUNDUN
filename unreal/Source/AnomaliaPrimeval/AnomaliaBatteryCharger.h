#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaBatteryCharger.generated.h"

class USceneComponent;
class UStaticMeshComponent;
class UPointLightComponent;
class AAnomaliaPowerGenerator;
class AAnomaliaSurvivor;

UCLASS(Blueprintable)
class ANOMALIAPRIMEVAL_API AAnomaliaBatteryCharger : public AActor
{
    GENERATED_BODY()

public:
    AAnomaliaBatteryCharger();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Electricity")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Electricity")
    TObjectPtr<UStaticMeshComponent> VisualMesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Electricity")
    TObjectPtr<UPointLightComponent> StatusLED;

    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category="ANOMALIA|Electricity|Persistence")
    FString PersistentId;

    UPROPERTY(EditInstanceOnly, Replicated, BlueprintReadOnly, Category="ANOMALIA|Electricity")
    TObjectPtr<AAnomaliaPowerGenerator> PowerGenerator;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Electricity", meta=(ClampMin="1.0", ClampMax="100.0"))
    float ChargePercentPerHour = 25.f;

    UPROPERTY(Replicated, BlueprintReadOnly, Category="ANOMALIA|Electricity")
    bool bSwitchedOn = true;

    UPROPERTY(Replicated, BlueprintReadOnly, Category="ANOMALIA|Electricity")
    bool bHasBattery = false;

    UPROPERTY(Replicated, BlueprintReadOnly, Category="ANOMALIA|Electricity")
    float BatteryCharge01 = 0.f;

    UPROPERTY(Replicated, BlueprintReadOnly, Category="ANOMALIA|Electricity")
    bool bCharging = false;

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Electricity")
    bool InsertBatteryOnServer(AAnomaliaSurvivor* Player);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Electricity")
    bool RemoveBatteryOnServer(AAnomaliaSurvivor* Player);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Electricity")
    bool SetSwitchedOnServer(bool bOn);

    virtual void Tick(float DeltaSeconds) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
    float SaveElapsedSeconds = 0.f;
    bool bPersistenceEnabled = false;
    bool IsPlayerInReach(const AAnomaliaSurvivor* Player) const;
    bool GetSavePath(FString& OutFile) const;
    bool LoadServerState();
    bool SaveServerState() const;
};
