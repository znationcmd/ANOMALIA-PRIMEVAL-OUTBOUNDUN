#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AnomaliaConfigFusionLibrary.generated.h"

/**
 * Non-destructive JSON/INI config merger from src/config-fusion.js.
 * This library handles *data* only: it never reads, deletes, or overwrites files.
 */
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaConfigFusionLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /** Parse the INI subset accepted by the JavaScript prototype into JSON section objects. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|ConfigFusion")
    static bool ParseIniToJson(const FString& IniText, FString& OutSectionsJson, FString& OutError);

    /** Flatten {"Section":{"Key":"value"}} into {"Section.Key":"value"}. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|ConfigFusion")
    static bool FlattenIniJson(const FString& SectionsJson, FString& OutFlatJson, FString& OutError);

    /**
     * Layer precedence: defaults < legacy < canonical < server.
     * Result JSON contains values, conflicts and precedence; JSON value types are preserved.
     */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|ConfigFusion")
    static bool MergeConfigJson(
        const FString& DefaultsJson, const FString& LegacyJson,
        const FString& CanonicalJson, const FString& ServerJson,
        FString& OutReportJson, FString& OutError);

    /** Read-only manifest of native config domain names and preserved legacy filenames. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|ConfigFusion")
    static bool BuildFusionReport(
        const TArray<FString>& PresentFilePaths, FString& OutReportJson, FString& OutError);
};
