#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AnomaliaPerformanceLibrary.generated.h"

/** Local graphics preferences only: never saved to a dedicated server profile. */
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaPerformanceLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** Presets include PC, PS5, Xbox Series X/S and Android/iOS targets.
      * Use GetGraphicsPresets for the complete current list.
      * The console presets are experimental and do not certify 4K60. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Graphics")
    static bool ApplyGraphicsPreset(const FString& PresetName);

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Graphics")
    static TArray<FString> GetGraphicsPresets();
};
