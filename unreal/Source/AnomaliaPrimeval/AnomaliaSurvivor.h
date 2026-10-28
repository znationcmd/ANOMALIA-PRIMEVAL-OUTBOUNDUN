#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Vehicles/AnomaliaVehicleSurvival.h"
#include "AnomaliaSurvivor.generated.h"

class USpringArmComponent;
class USkeletalMeshComponent;
class USkeletalMesh;
class UCameraComponent;
class UAnomaliaInventoryComponent;
class UAnomaliaInventoryWidget;
class UAnomaliaStatusWidget;
class UAnomaliaVitalsComponent;
class UAnomaliaItemEffectsComponent;
class AAnomaliaHomesteadStation;
class AAnomaliaChaosRoadVehicle;

UCLASS()
class ANOMALIAPRIMEVAL_API AAnomaliaSurvivor : public ACharacter
{
    GENERATED_BODY()
public:
    AAnomaliaSurvivor();
    void CloseInventory();
    void AssignQuickbarStack(int32 SlotIndex,int32 StackId);
    int32 GetQuickbarStackId(int32 SlotIndex) const;
    void ActivateQuickbarSlot(int32 SlotIndex);
    bool RequestVehicleService(AAnomaliaChaosRoadVehicle* Vehicle,EAnomaliaVehicleServiceAction Action,int32 StackId=0,int32 ExpectedCount=0);
    UFUNCTION(Server,Reliable) void ServerVehicleService(AAnomaliaChaosRoadVehicle* Vehicle,EAnomaliaVehicleServiceAction Action,int32 StackId,int32 ExpectedCount);

    /** Cosmetic modular clothing follows the main body skeleton. No third-party meshes are bundled. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Appearance")
    TObjectPtr<USkeletalMeshComponent> JacketMesh;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Appearance")
    TObjectPtr<USkeletalMeshComponent> PantsMesh;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Appearance")
    TObjectPtr<USkeletalMeshComponent> BootsMesh;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Appearance")
    TObjectPtr<USkeletalMeshComponent> GlovesMesh;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Appearance")
    TObjectPtr<USkeletalMeshComponent> HeadgearMesh;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Appearance")
    TObjectPtr<USkeletalMeshComponent> BackpackMesh;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Appearance")
    TObjectPtr<USkeletalMeshComponent> VestMesh;

    /** Apply an approved, skeleton-compatible cosmetic mesh; game equipment rules remain server-owned. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Appearance")
    bool SetClothingMesh(FName Slot, USkeletalMesh* MeshAsset);

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

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|ItemEffects")
    TObjectPtr<UAnomaliaItemEffectsComponent> ItemEffectsComponent;

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
    virtual float TakeDamage(float Amount, const FDamageEvent& Event, AController* InstigatorController, AActor* Causer) override;

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
    void InputMeleeAttack();
    UFUNCTION(Server,Reliable) void ServerMeleeAttack();
    void StartSprint();
    void BeginPaceAdjustment();
    void EndPaceAdjustment();
    void IncreasePace();
    void DecreasePace();
    void ToggleTacticalCrouch();
    void StopSprint();
    void InputRest();
    void InputPause();
    void InputCamera();
    void InputQuickbar1(); void InputQuickbar2(); void InputQuickbar3(); void InputQuickbar4(); void InputQuickbar5();
    void InputQuickbar6(); void InputQuickbar7(); void InputQuickbar8(); void InputQuickbar9(); void InputQuickbar0();
    /** Only the owning local player uses this to prevent wheel/weapon conflicts. */
    bool bAdjustPaceWithWheel = false;
    UPROPERTY(Transient) TArray<int32> QuickbarStackIds;
    double NextMeleeAttackTime=0.0;
    TWeakObjectPtr<AAnomaliaHomesteadStation> ActiveBed;

    UFUNCTION(Server, Reliable)
    void ServerRequestRest();

    /** Server checks the closest available vehicle; clients cannot choose an arbitrary target. */
    UFUNCTION(Server, Reliable)
    void ServerTryEnterVehicle();
};
