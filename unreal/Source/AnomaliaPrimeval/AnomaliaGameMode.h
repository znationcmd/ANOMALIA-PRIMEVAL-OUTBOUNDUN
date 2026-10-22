#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "AnomaliaConfigLibrary.h"
#include "AnomaliaGameMode.generated.h"

class AAnomaliaVehiclePawn;
class AController;
class APlayerController;

UCLASS()
class ANOMALIAPRIMEVAL_API AAnomaliaGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AAnomaliaGameMode();

    /** Unique server identifier; never reuse another server's Saved/Servers directory. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="ANOMALIA|Server")
    FString ServerId = TEXT("main");

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Server")
    FAnomaliaServerSettings ActiveServerSettings;

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Server")
    FString GetActiveServerMode() const { return ActiveServerSettings.Mode; }

protected:
    /** Loads a bounded list of initial vehicles only from this server's own Saved directory. */
    virtual void BeginPlay() override;
    virtual void HandleStartingNewPlayer_Implementation(APlayerController* NewPlayer) override;
    void SpawnConfiguredVehicles();
    /** Server-only import of its own validated Editor/world.json placeables. */
    void SpawnConfiguredHomestead();
    void LoadPersistentPlayer(APlayerController* PlayerController);
    bool SavePersistentPlayer(AController* Controller);
    void SaveAllPlayerProfiles();

    FTimerHandle ProfileSaveTimer;
    FTimerHandle ProfileRecoveryTimer;
    TSet<FString> PendingProfileLoads;
    void RetryPendingProfileLoads();
    virtual void InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage) override;

public:

    FString GetPersistentPlayerId(const AController* Controller) const;
    bool SaveLocalGame();

    /** Called by trusted server logic only. Not a client spawn RPC. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Server|Vehicles")
    AAnomaliaVehiclePawn* SpawnServerVehicle(FName VehicleId, const FTransform& SpawnTransform);
    virtual void Logout(AController* Exiting) override;
};
