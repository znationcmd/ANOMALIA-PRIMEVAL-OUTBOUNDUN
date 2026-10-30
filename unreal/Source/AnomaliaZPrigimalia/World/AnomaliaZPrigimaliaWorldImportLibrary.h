#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AnomaliaZPrigimaliaWorldImportLibrary.generated.h"
UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaWorldImportLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 /** Editor-only creation in the dedicated new ANOMALIA_Archipelago_v2 world. Never edits another world. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateArchipelagoLandscape();
 /** New separate world with original urban terrain pads. Never alters the v2 archipelago. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateInhabitedArchipelagoLandscape();
 UFUNCTION(BlueprintPure, Category="ANOMALIA|World")
 static double InhabitedArchipelagoHeight(double EastMeters, double NorthMeters);
 UFUNCTION(BlueprintPure, Category="ANOMALIA|World")
 static TArray<FVector2D> InhabitedSettlementSites();
 /** Unsaved editor inspection/refresh only. Does not import heights or save packages. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static FString RefreshArchipelagoRenderResources(bool bRefresh = true);
 /** Copy descriptor values to JSON; no borrowed FActorDesc/FGuid wrappers cross into Python. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static FString GetArchipelagoActorDescriptors();
 /** Transient editor streaming only. Rejects the complete request if any GUID is invalid or unrelated. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static bool SetArchipelagoActorsLoaded(const TArray<FString>& ActorGuids, bool bLoaded);
 /** Read-only house audit. All actor/mesh/struct lifetimes stay native; Python receives JSON only. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static FString AuditInhabitedResidential(const TArray<FString>& MeshPaths, const TArray<FString>& HouseLabels);
 UFUNCTION(BlueprintPure, Category="ANOMALIA|World")
 static double ArchipelagoHeight(double EastMeters, double NorthMeters);
};
