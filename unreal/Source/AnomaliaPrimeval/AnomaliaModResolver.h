#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AnomaliaModResolver.generated.h"

/**
 * Pure native port of src/mod-manager.js.
 * This resolver NEVER downloads, installs or runs third-party mod packages.
 */
USTRUCT(BlueprintType)
struct FAnomaliaModManifest
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Id;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Version;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Sha256;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FString> Dependencies;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TArray<FString> Compatibility;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bSigned = false;
};

USTRUCT(BlueprintType)
struct FAnomaliaModResolution
{
    GENERATED_BODY()

    /** All requested mods and dependencies, in dependency-first order. */
    UPROPERTY(BlueprintReadOnly) TArray<FAnomaliaModManifest> Required;
    UPROPERTY(BlueprintReadOnly) TArray<FAnomaliaModManifest> Downloads;
    UPROPERTY(BlueprintReadOnly) TArray<FAnomaliaModManifest> AlreadyInstalled;
    UPROPERTY(BlueprintReadOnly) bool bRequiresConsent = true;
};

UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaModResolver : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Mods")
    static bool ValidateModManifest(const FAnomaliaModManifest& Manifest, FString& OutError);

    /** Detects missing dependencies, duplicate IDs and dependency cycles. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Mods")
    static bool ResolveMods(
        const TArray<FString>& Requested,
        const TArray<FAnomaliaModManifest>& Catalog,
        const TArray<FAnomaliaModManifest>& Installed,
        FAnomaliaModResolution& OutResolution,
        FString& OutError);

    /** Only safe relative .json paths are accepted, as with the JS mapping prototype. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Mods")
    static bool ValidatePlacementManifest(const TArray<FString>& RelativeFiles, FString& OutError);

private:
    static bool ValidModId(const FString& Id);
    static bool ValidVersion(const FString& Version);
    static bool ValidSha256(const FString& Hash);
};
