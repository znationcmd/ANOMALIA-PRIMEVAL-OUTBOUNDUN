#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AnomaliaSurvivor.generated.h"

class USpringArmComponent;
class UCameraComponent;
class UAnomaliaInventoryComponent;
class UAnomaliaInventoryWidget;
class UAnomaliaStatusWidget;
class UAnomaliaVitalsComponent;
class AAnomaliaHomesteadStation;

UCLASS()
class ANOMALIAPRIMEVAL_API AAnomaliaSurvivor : public ACharacter
{
    GENERATED_BODY()
public:
    AAnomaliaSurvivor();
    void CloseInventory();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Camera")
    TObjectPtr<USpringArmComponent> CameraBoom;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Camera")
    TObjectPtr<UCameraComponent> FollowCamera;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Inventory")
    TObjectPtr<UAnomaliaInventoryComponent> InventoryComponent;

    UPROPERTY(Transient)
    TObjectPtr<UAnomaliaInventoryWidget> InventoryWidget;

    UPROPERTY(Transient)
    TObjectPtr<UAnomaliaStatusWidget> StatusWidget;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Survival")
    TObjectPtr<UAnomaliaVitalsComponent> VitalsComponent;

    UPROPERTY(ReplicatedUsing=OnRep_Survival, BlueprintReadOnly, Category="ANOMALIA|Survival")
    float Hunger = 100.f;

    UPROPERTY(ReplicatedUsing=OnRep_Survival, BlueprintReadOnly, Category="ANOMALIA|Survival")
    float Thirst = 100.f;

    UPROPERTY(ReplicatedUsing=OnRep_Survival, BlueprintReadOnly, Category="ANOMALIA|Survival")
    float Health = 100.f;

    /** 0 = rested, 100 = exhausted; independent of sprint stamina. */
    UPROPERTY(ReplicatedUsing=OnRep_Rest, BlueprintReadOnly, Category="ANOMALIA|Rest")
    float Fatigue = 0.f;

    UPROPERTY(ReplicatedUsing=OnRep_Rest, BlueprintReadOnly, Category="ANOMALIA|Rest")
    bool bSleeping = false;

    UPROPERTY(ReplicatedUsing=OnRep_Rest, BlueprintReadOnly, Category="ANOMALIA|Rest")
    float SleepRemainingSeconds = 0.f;

    UFUNCTION(BlueprintImplementableEvent, Category="ANOMALIA|Rest")
    void OnRestChanged();

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Rest")
    void RestoreFatigue(float SavedFatigue);

    UFUNCTION(BlueprintImplementableEvent, Category="ANOMALIA|Survival")
    void OnSurvivalChanged();

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Survival")
    void RestoreSurvival(float Food, float Water, float HP);

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;

protected:
    UFUNCTION()
    void OnRep_Survival();

    UFUNCTION()
    void OnRep_Rest();

private:
    void MoveForward(float Value);
    void MoveRight(float Value);
    void Turn(float Value);
    void LookUp(float Value);
    void TurnRate(float Value);
    void LookUpRate(float Value);
    void InputInteract();
    void InputInventory();
    void StartSprint();
    void StopSprint();
    void InputRest();

    TWeakObjectPtr<AAnomaliaHomesteadStation> ActiveBed;

    UFUNCTION(Server, Reliable)
    void ServerRequestRest();

    /** Server checks the closest available vehicle; clients cannot choose an arbitrary target. */
    UFUNCTION(Server, Reliable)
    void ServerTryEnterVehicle();
};
