#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "AnomaliaGameMode.generated.h"

UCLASS(Blueprintable)
class ANOMALIAPRIMEVAL_API AAnomaliaGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    virtual void InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage) override;
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Server")
    FString GetActiveServerMode() const { return ActiveMode; }
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Server")
    int32 GetConfiguredMaxPlayers() const { return ConfiguredMaxPlayers; }
private:
    FString ActiveMode = TEXT("pve");
    int32 ConfiguredMaxPlayers = 16;
};
