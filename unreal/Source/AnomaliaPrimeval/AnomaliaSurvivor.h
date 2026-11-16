#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AnomaliaSurvivor.generated.h"

class USpringArmComponent;
class UCameraComponent;
class UAnomaliaInventoryComponent;
class UAnomaliaInventoryWidget;
class AAnomaliaRefrigerator;
class UAnomaliaRefrigeratorWidget;

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

    /** UI calls on the locally owned pawn; server validates reach and available items. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Fridge")
    void RequestDepositToFridge(AAnomaliaRefrigerator* Fridge, FName ItemId, int32 Count);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Fridge")
    void RequestWithdrawFromFridge(AAnomaliaRefrigerator* Fridge, FName ItemId, int32 Count);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Fridge")
    void CloseFridgeInterface();

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

    UFUNCTION(Server, Reliable)
    void ServerDepositToFridge(AAnomaliaRefrigerator* Fridge, FName ItemId, int32 Count);

    UFUNCTION(Server, Reliable)
    void ServerWithdrawFromFridge(AAnomaliaRefrigerator* Fridge, FName ItemId, int32 Count);

    /** Server checks the closest available vehicle; clients cannot choose an arbitrary target. */
    UFUNCTION(Server, Reliable)
    void ServerTryEnterVehicle();
};
