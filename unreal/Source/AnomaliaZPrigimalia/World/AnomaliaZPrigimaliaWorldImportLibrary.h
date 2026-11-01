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
 /** Original 48km archipelago terrain in a NEW isolated SKARVIK_ISLANDS_v1 package.
     Never overwrite either the original Archipelago or populated graded SKARVIK. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateSkarvikIslandsV1Landscape();
 /** Create ONLY a new 48x48km SKARVIK City world in its separate package, preserving original SKARVIK. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateSkarvikCityLandscape();
 /** Build a NEW, non-destructive 48km SKARVIK terrain with graded plots for 124 settlements; v1 and D: untouched. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateSkarvikGradedLandscape();
 /** Build a new 48x48km single final island-and-mainland graded coast in a NEW
     World Partition package. Never replace original graded 1039-building map. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateSkarvikFinalCoastalLandscape();
 /** Exact native source height for dry-land relocation, city pad and island cores. */
 UFUNCTION(BlueprintPure, Category="ANOMALIA|World")
 static double SkarvikFinalCoastalHeight(double EastMeters,double NorthMeters);
 /** Height of the graded v2 buildable terrain in metres; source height v1 is unchanged. */
 UFUNCTION(BlueprintPure, Category="ANOMALIA|World")
 static double SkarvikGradedHeight(double EastMeters,double NorthMeters);
 /** Original SM5-compatible geography for the prospective SKARVIK city world. */
 UFUNCTION(BlueprintPure, Category="ANOMALIA|World")
 static double SkarvikCityHeight(double EastMeters,double NorthMeters);
 /** New separate world with original urban terrain pads. Never alters the v2 archipelago. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateInhabitedArchipelagoLandscape();
 /** Create a unique native World Partition landscape ONLY for one of 4 planned new worlds. Never alters the 11 original worlds. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateNewFourLandscape(const FString& MapIdentifier);
 /** Height metres in one of the 4 new worlds. Water masks are design targets, not rendered water. */
 UFUNCTION(BlueprintPure, Category="ANOMALIA|World")
 static double NewFourWorldHeight(const FString& MapIdentifier,double EastMeters,double NorthMeters);
 /** Editor-only 30/20 km named World Partition landscape creation; no overwrites. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateNamedWorldLandscape(const FString& MapIdentifier);
 UFUNCTION(BlueprintPure, Category="ANOMALIA|World")
 static double NamedWorldHeight(const FString& MapIdentifier,double EastMeters,double NorthMeters);
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
