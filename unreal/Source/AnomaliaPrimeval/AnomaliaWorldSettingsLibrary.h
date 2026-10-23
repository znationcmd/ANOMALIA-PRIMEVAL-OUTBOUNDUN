#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AnomaliaWorldSettingsLibrary.generated.h"

/** Native counterpart of src/world-settings-ui.js. Stored per server/world, not browser localStorage. */
USTRUCT(BlueprintType)
struct FAnomaliaWorldSettings
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|WorldSettings")
    FString Mode = TEXT("pve");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|WorldSettings") float Difficulty = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|WorldSettings") float Xp = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|WorldSettings") float Harvest = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|WorldSettings") float Loot = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|WorldSettings") float FoodDrain = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|WorldSettings") float WaterDrain = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|WorldSettings") float StaminaDrain = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|WorldSettings") float Taming = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|WorldSettings") float Breeding = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|WorldSettings") float Hatching = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|WorldSettings") float Maturation = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|WorldSettings") float DayLength = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|WorldSettings") float NightLength = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|WorldSettings")
    int32 MaxPlayers = 8;
};

UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaWorldSettingsLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /** Mirrors JS normalization: invalid mode/numbers use defaults; finite numbers are clamped. */
    UFUNCTION(BlueprintPure, Category="ANOMALIA|WorldSettings")
    static FAnomaliaWorldSettings NormalizeWorldSettings(const FAnomaliaWorldSettings& Input);

    /** Standalone server-world settings. Missing file returns defaults + "World state not found". */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|WorldSettings")
    static bool LoadWorldSettings(const FString& ServerId, FAnomaliaWorldSettings& OutSettings, FString& OutError);

    /** Writes only Saved/Servers/<validated server ID>/World/world-settings.json, atomically. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|WorldSettings")
    static bool SaveWorldSettings(const FString& ServerId, const FAnomaliaWorldSettings& Settings, FString& OutError);
};
