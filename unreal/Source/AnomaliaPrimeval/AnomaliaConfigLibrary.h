#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AnomaliaConfigLibrary.generated.h"

/** ANOMALIA UE5 configuration. Saved/Servers/<server-id> is the only writable server scope. */
USTRUCT(BlueprintType)
struct FAnomaliaServerSettings
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Server")
    FString Name = TEXT("ANOMALIA PRIMEVAL OUTBOUNDUN");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Server")
    int32 Port = 2303;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Server")
    int32 MaxPlayers = 16;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Server")
    FString Mode = TEXT("pve");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Server")
    bool bThirdPerson = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Server")
    float TimeMultiplier = 1.0f;

    /** Per-server survival tuning, never shared with other server IDs. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Survival", meta=(ClampMin="0.0", ClampMax="10.0"))
    float HungerDrainPerSecond = 0.015f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Survival", meta=(ClampMin="0.0", ClampMax="10.0"))
    float ThirstDrainPerSecond = 0.025f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Survival", meta=(ClampMin="0.0", ClampMax="10.0"))
    float StarvationDamagePerSecond = 0.25f;

    /** First-pass constant ambient environment; weather and clothing are later systems. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Survival", meta=(ClampMin="-50.0", ClampMax="60.0"))
    float AmbientTemperatureC = 20.f;

        // Intentionally no password/admin key in this Blueprint struct.
};

UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaConfigLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Configuration")
    static bool LoadServerSettings(const FString& ServerId, FAnomaliaServerSettings& OutSettings, FString& OutError);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Configuration")
    static bool SaveServerSettings(const FString& ServerId, const FAnomaliaServerSettings& Settings, FString& OutError);

    /** User data is never stored in the server configuration or another player's profile. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Persistence")
    static bool LoadPlayerProfile(const FString& ServerId, const FString& PlayerId, FString& OutJson, FString& OutError);

    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Persistence")
    static bool SavePlayerProfile(const FString& ServerId, const FString& PlayerId, const FString& Json, FString& OutError);

    // Atomic server/map-scoped state, separate from player profiles and configuration.
    static bool LoadWorldState(const FString& ServerId, const FString& StateId, FString& OutJson, FString& OutError);
    static bool SaveWorldState(const FString& ServerId, const FString& StateId, const FString& Json, FString& OutError);

private:
    static bool ValidId(const FString& Id);
    static FString ServerRoot(const FString& ServerId);
    static bool WriteJsonSafely(const FString& File, const FString& Json, FString& OutError);
};
