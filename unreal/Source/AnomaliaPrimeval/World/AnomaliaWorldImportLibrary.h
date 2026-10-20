#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AnomaliaWorldImportLibrary.generated.h"
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaWorldImportLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 /** Editor-only creation in the dedicated new ANOMALIA_Archipelago_v1 world. Never edits another world. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateArchipelagoLandscape();
 UFUNCTION(BlueprintPure, Category="ANOMALIA|World")
 static double ArchipelagoHeight(double EastMeters, double NorthMeters);
};
