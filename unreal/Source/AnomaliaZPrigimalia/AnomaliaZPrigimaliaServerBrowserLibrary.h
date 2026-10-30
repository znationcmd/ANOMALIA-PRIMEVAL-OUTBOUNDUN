#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AnomaliaZPrigimaliaServerBrowserLibrary.generated.h"

/** Visible menu filters; game mode is enforced by separately configured servers. */
UENUM(BlueprintType)
enum class EAnomaliaZPrigimaliaServerFilter : uint8
{
    All, PVE, PVP, RP
};

USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaServerCard
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Servers")
    FString ServerId;

    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Servers")
    FString DisplayName;

    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Servers")
    EAnomaliaZPrigimaliaServerFilter Mode = EAnomaliaZPrigimaliaServerFilter::PVE;

    /** A planned official slot is NOT an actual running server. */
    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Servers")
    bool bProvisioned = false;

    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Servers")
    bool bOnline = false;

    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Servers")
    int32 CurrentPlayers = 0;

    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Servers")
    int32 MaxPlayers = 16;

    /** -1 = not measured / unknown. */
    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Servers")
    int32 PingMs = -1;
};

UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaServerBrowserLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** Defines 5 PVE + 5 PVP + 5 RP official provisioning slots. None are claimed online. */
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Servers")
    static TArray<FAnomaliaZPrigimaliaServerCard> GetOfficialServerTemplates();

    /** Can filter real server results later, or offline provisioning templates now. */
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Servers")
    static TArray<FAnomaliaZPrigimaliaServerCard> FilterByMode(
        const TArray<FAnomaliaZPrigimaliaServerCard>& Servers, EAnomaliaZPrigimaliaServerFilter Mode,
        bool bOnlyOnline);
};
