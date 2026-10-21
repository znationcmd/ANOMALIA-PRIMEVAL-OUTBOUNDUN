#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AnomaliaWorldImportLibrary.generated.h"
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaWorldImportLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 /** Editor-only creation in the dedicated new ANOMALIA_Archipelago_v2 world. Never edits another world. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateArchipelagoLandscape();
 /** Unsaved editor inspection/refresh only. Does not import heights or save packages. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static FString RefreshArchipelagoRenderResources();
 UFUNCTION(BlueprintPure, Category="ANOMALIA|World")
 static double ArchipelagoHeight(double EastMeters, double NorthMeters);
};
