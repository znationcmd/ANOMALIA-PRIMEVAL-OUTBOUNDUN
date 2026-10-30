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

/** One independent Unreal World Partition map, never a region of another map. */
USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaWorldMapCard
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Maps") FString MapId;
    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Maps") FString DisplayName;
    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Maps") FString UnrealPackage;
    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Maps") int32 WidthKm = 0;
    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Maps") int32 HeightKm = 0;
    /** Exact side lengths, including fractional-kilometre maps such as F.A.L.C. */
    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Maps") float WidthKmExact = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Maps") float HeightKmExact = 0.f;
    /** Not an online indicator. Only set after independent native gameplay tests. */
    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Maps") bool bPlayableValidated = false;
};

USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaServerCard
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Servers")
    FString ServerId;

    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Servers")
    FString DisplayName;

    /** Stable chosen world ID; independent from the server slot and the player's saves. */
    UPROPERTY(BlueprintReadOnly, Category="ANOMALIA|Servers")
    FString MapId;

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

    /** Ten separate maps; readiness is intentionally false until verified in an actual build. */
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Maps")
    static TArray<FAnomaliaZPrigimaliaWorldMapCard> GetIndependentWorldMaps();

    /** Only returns a match for the exact canonical map ID, not a fuzzy shared terrain. */
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Servers")
    static TArray<FAnomaliaZPrigimaliaServerCard> FilterByMap(
        const TArray<FAnomaliaZPrigimaliaServerCard>& Servers, const FString& MapId,
        bool bOnlyOnline);
};
