#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AnomaliaSurvivor.generated.h"

class USpringArmComponent;
class UCameraComponent;
class UAnomaliaInventoryComponent;
class UAnomaliaInventoryWidget;
class AAnomaliaRefrigerator;
class AAnomaliaPowerGenerator;
class UAnomaliaRefrigeratorWidget;
class AAnomaliaBatteryCharger;
class AAnomaliaWorkLight;
class UAnomaliaPowerUtilityWidget;

UCLASS()
class ANOMALIAPRIMEVAL_API AAnomaliaSurvivor : public ACharacter
{
    GENERATED_BODY()
public:
    AAnomaliaSurvivor();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Camera")
    TObjectPtr<USpringArmComponent> CameraBoom;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Camera")
    TObjectPtr<UCameraComponent> FollowCamera;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Inventory")
    TObjectPtr<UAnomaliaInventoryComponent> InventoryComponent;

    UPROPERTY(Transient)
    TObjectPtr<UAnomaliaInventoryWidget> InventoryWidget;

    UPROPERTY(Transient)
    TObjectPtr<UAnomaliaRefrigeratorWidget> FridgeWidget;

    UPROPERTY(Transient)
    TObjectPtr<UAnomaliaPowerUtilityWidget> PowerUtilityWidget;

    /** UI calls on the locally owned pawn; server validates reach and available items. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Fridge")
    void RequestDepositToFridge(AAnomaliaRefrigerator* Fridge, FName ItemId, int32 Count);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Fridge")
    void RequestWithdrawFromFridge(AAnomaliaRefrigerator* Fridge, FName ItemId, int32 Count);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Fridge")
    void CloseFridgeInterface();

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Fridge")
    void RequestSetFridgeOn(AAnomaliaRefrigerator* Fridge, bool bOn);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Power")
    void RequestSetGeneratorRunning(AAnomaliaPowerGenerator* Generator, bool bOn);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Electricity")
    void RequestSetChargerOn(AAnomaliaBatteryCharger* Charger, bool bOn);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Electricity")
    void RequestInsertBattery(AAnomaliaBatteryCharger* Charger);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Electricity")
    void RequestRemoveBattery(AAnomaliaBatteryCharger* Charger);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Electricity")
    void RequestSetWorkLightOn(AAnomaliaWorkLight* Light, bool bOn);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Electricity")
    void RequestRefuelGenerator(AAnomaliaPowerGenerator* Generator);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Electricity")
    void RequestPickupGenerator(AAnomaliaPowerGenerator* Generator);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Electricity")
    void RequestPlaceGenerator(AAnomaliaPowerGenerator* Generator);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Electricity")
    void ClosePowerUtilityInterface();

    UPROPERTY(ReplicatedUsing=OnRep_Survival, BlueprintReadOnly, Category="ANOMALIA|Survival")
    float Hunger = 100.f;

    UPROPERTY(ReplicatedUsing=OnRep_Survival, BlueprintReadOnly, Category="ANOMALIA|Survival")
    float Thirst = 100.f;

    UPROPERTY(ReplicatedUsing=OnRep_Survival, BlueprintReadOnly, Category="ANOMALIA|Survival")
    float Health = 100.f;

    UFUNCTION(BlueprintImplementableEvent, Category="ANOMALIA|Survival")
    void OnSurvivalChanged();

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Survival")
    void RestoreSurvival(float Food, float Water, float HP);

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
    virtual void Tick(float DeltaSeconds) override;

protected:
    UFUNCTION()
    void OnRep_Survival();

private:
    void MoveForward(float Value);
    void MoveRight(float Value);
    void Turn(float Value);
    void LookUp(float Value);
    void InputInteract();
    void InputInventory();
    void OpenFridgeInterface(AAnomaliaRefrigerator* Fridge);
    void OpenPowerUtilityInterface(AActor* Device);

    UFUNCTION(Server, Reliable)
    void ServerDepositToFridge(AAnomaliaRefrigerator* Fridge, FName ItemId, int32 Count);

    UFUNCTION(Server, Reliable)
    void ServerWithdrawFromFridge(AAnomaliaRefrigerator* Fridge, FName ItemId, int32 Count);

    UFUNCTION(Server, Reliable)
    void ServerSetFridgeOn(AAnomaliaRefrigerator* Fridge, bool bOn);

    UFUNCTION(Server, Reliable)
    void ServerSetGeneratorRunning(AAnomaliaPowerGenerator* Generator, bool bOn);

    UFUNCTION(Server, Reliable)
    void ServerSetChargerOn(AAnomaliaBatteryCharger* Charger, bool bOn);

    UFUNCTION(Server, Reliable)
    void ServerInsertBattery(AAnomaliaBatteryCharger* Charger);

    UFUNCTION(Server, Reliable)
    void ServerRemoveBattery(AAnomaliaBatteryCharger* Charger);

    UFUNCTION(Server, Reliable)
    void ServerSetWorkLightOn(AAnomaliaWorkLight* Light, bool bOn);

    UFUNCTION(Server, Reliable)
    void ServerRefuelGenerator(AAnomaliaPowerGenerator* Generator);

    UFUNCTION(Server, Reliable)
    void ServerPickupGenerator(AAnomaliaPowerGenerator* Generator);

    UFUNCTION(Server, Reliable)
    void ServerPlaceGenerator(AAnomaliaPowerGenerator* Generator);

    /** Server checks the closest available vehicle; clients cannot choose an arbitrary target. */
    UFUNCTION(Server, Reliable)
    void ServerTryEnterVehicle();
};
