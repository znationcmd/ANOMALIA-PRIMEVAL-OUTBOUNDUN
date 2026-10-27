#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Subsystems/WorldSubsystem.h"
#include "AnomaliaVehicleSurvival.generated.h"
class AAnomaliaSurvivor;
class UAnomaliaInventoryComponent;
class FJsonObject;
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FAnomaliaVehicleServicesUpdated);

UENUM(BlueprintType)
enum class EAnomaliaVehicleServiceAction : uint8
{
    TakeInitialKey, ToggleLock, InstallBattery, RemoveBattery, InstallRadiator,
    RemoveRadiator, InstallSparkPlug, RemoveSparkPlug, FillCoolant, Deposit, Withdraw, WithdrawToHands
};
USTRUCT(BlueprintType)
struct FAnomaliaVehicleSurvivalState
{
    GENERATED_BODY()
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly) FName KeyItemId;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly) bool bKeyIssued=false;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly) bool bLocked=false;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly) bool bBattery=true;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly) bool bRadiator=true;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly) bool bSparkPlug=true;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly) float BatteryCharge=1.f;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly) float Coolant=1.f;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly) float TemperatureC=20.f;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly) float EngineHealth=1.f;
};
/** Real inventory exchanges and ignition interlock; no client-supplied player/key identity. */
UCLASS(ClassGroup=(Anomalia),meta=(BlueprintSpawnableComponent))
class ANOMALIAPRIMEVAL_API UAnomaliaVehicleSurvivalComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UAnomaliaVehicleSurvivalComponent();
    UPROPERTY(EditAnywhere,BlueprintReadOnly) bool bEnabled=true;
    /** Set on authored/spawned persistent vehicles; empty uses stable placed map/actor identity. */
    UPROPERTY(EditInstanceOnly,BlueprintReadOnly) FString PersistentId;
    UPROPERTY(EditAnywhere,BlueprintReadOnly) FName BatteryAccessPanel=TEXT("hood");
    UPROPERTY(ReplicatedUsing=OnRep_State,VisibleAnywhere,BlueprintReadOnly) FAnomaliaVehicleSurvivalState State;
    UPROPERTY(BlueprintAssignable) FAnomaliaVehicleServicesUpdated OnServicesUpdated;
    UFUNCTION() void OnRep_State(FAnomaliaVehicleSurvivalState Previous);
    UPROPERTY(Replicated,VisibleAnywhere,BlueprintReadOnly) bool bReady=false;
    bool HasPhysicalKey(const AAnomaliaSurvivor* User) const;
    bool CanStart(const AAnomaliaSurvivor* User) const;
    bool Execute(AAnomaliaSurvivor* User,EAnomaliaVehicleServiceAction Action,int32 StackId,int32 ExpectedCount,FString& Error);
    void SimulateEngine(float DeltaSeconds,float Demand);
    void ApplyLocks();
    bool HasOpenPanel(FName Id) const;
    UAnomaliaInventoryComponent* GetCargo() const;
    TSharedPtr<FJsonObject> Export() const;
    bool Restore(const TSharedPtr<FJsonObject>& Row,FString& Error);
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
protected:
    virtual void BeginPlay() override;
private:
    friend class UAnomaliaVehicleServiceSubsystem;
    float SaveElapsed=0;
    bool ValidateAccess(AAnomaliaSurvivor* User,EAnomaliaVehicleServiceAction Action,FString& Error) const;
    bool Change(AAnomaliaSurvivor* User,EAnomaliaVehicleServiceAction Action,int32 StackId,int32 ExpectedCount,FString& Error);
};
/** One server ledger and recoverable player-profile journal, including unloaded vehicles. */
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaVehicleServiceSubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual bool DoesSupportWorldType(EWorldType::Type Type) const override;
    virtual TStatId GetStatId() const override;
    virtual void Tick(float Delta) override;
    bool Configure(const FString& Scope,FString& Error);
    bool RegisterVehicle(UAnomaliaVehicleSurvivalComponent* Component,FString& Error);
    bool Execute(UAnomaliaVehicleSurvivalComponent* Component,AAnomaliaSurvivor* User,EAnomaliaVehicleServiceAction Action,int32 StackId,int32 ExpectedCount,FString& Error);
    bool SaveVehicle(UAnomaliaVehicleSurvivalComponent* Component,FString& Error);
    bool HasPendingPlayer(const FString& PlayerId) const;
private:
    FString ServerId;
    bool bConfigured=false,bReady=false;
    float Elapsed=0;
    TSharedPtr<FJsonObject> Ledger;
    TWeakObjectPtr<UAnomaliaInventoryComponent> PendingInventory;
    bool Persist(FString& Error);
    bool Recover(FString& Error);
};
