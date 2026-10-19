#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "AnomaliaServerSettingsSubsystem.generated.h"

/** Settings belong to one server only; no player profiles or worlds are shared. */
USTRUCT(BlueprintType)
struct FAnomaliaServerSettings
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Server")
    FString ServerName = TEXT("ANOMALIA PRIMEVAL OUTBOUNDUN");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Server")
    int32 Port = 2303;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Server")
    int32 MaxPlayers = 16;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Server")
    FString GameMode = TEXT("pve");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Gameplay")
    float TimeMultiplier = 1.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Gameplay")
    bool bThirdPerson = true;
};

UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaServerSettingsSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    /** Loads Saved/Servers/<ServerId>/config.json; a missing file uses safe defaults. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Server")
    bool LoadServerSettings(const FString& ServerId, FString& Error);

    /** Saves only the selected server's settings; never deletes or migrates another server. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Server")
    bool SaveServerSettings(FString& Error);

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Server")
    FAnomaliaServerSettings GetServerSettings() const { return Settings; }

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Server")
    FString GetServerId() const { return ActiveServerId; }

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Server")
    void SetServerSettings(const FAnomaliaServerSettings& InSettings) { Settings = InSettings; }

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Server")
    FString GetServerSaveDirectory() const;

private:
    FString ActiveServerId = TEXT("main");
    FAnomaliaServerSettings Settings;
    static bool IsSafeServerId(const FString& ServerId);
};
