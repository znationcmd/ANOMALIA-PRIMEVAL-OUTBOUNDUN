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
 /** Strictly isolated candidate built from user-authored DRAZOVIA coastal image.
     Requires TerrainSource/DRAZOVIA/DRAZOVIA.r16 (3025x3025 little endian).
     Never touches /Game/Maps/ANOMALIA_Inhabited_v2 or SKARVIK. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateDrazoviaTopoCandidateLandscape();
 /** Create an isolated candidate from the NEW iZurvive reference (not the older FALC/Drazovia photo).
     Source: TerrainSource/DRAZOVIA_NEW_REFERENCE/DRAZOVIA_NEW_TOPO_48KM_3025.r16.
     Strictly refuses original Inhabited_v2 and existing candidate landscapes. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateDrazoviaIzurviveCandidateLandscape();
 // Native v2 candidate: isolated from the previous failed attempt and old world.
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateDrazoviaIzurviveCandidateV2Landscape();
 /** Verify the native LandscapeComponents array, not Python's generic actor component enumeration. */
 UFUNCTION(BlueprintPure, Category="ANOMALIA|World")
 static int32 InspectDrazoviaIzurviveCandidateV2Components(AActor* Candidate);
 // V3 preserves the complete 576-component Landscape before grid redistribution.
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateDrazoviaIzurviveCandidateV3Landscape();
 UFUNCTION(BlueprintPure, Category="ANOMALIA|World")
 static int32 InspectDrazoviaIzurviveCandidateV3Components(AActor* Candidate);
 /** Editor-only 30/20 km named World Partition landscape creation; no overwrites. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateNamedWorldLandscape(const FString& MapIdentifier);
 /** Checks native Landscape components BEFORE deferred partition migration. Preview map only. */
 UFUNCTION(BlueprintPure, Category="ANOMALIA|World")
 static int32 InspectNamedWorldPreviewComponents(AActor* Candidate, const FString& MapIdentifier);
 /** Import ONE verified 5km CHERNASKALUXRIA source tile into its owned world.
     253x253 R16 samples -> four landscape components. Never merges another map. */
 UFUNCTION(BlueprintCallable, Category="ANOMALIA|World")
 static AActor* CreateChernaskaluxriaLandscapeTile(int32 Col,int32 Row);
 /** Checks native components before World Partition grid/proxy redistribution. */
 UFUNCTION(BlueprintPure, Category="ANOMALIA|World")
 static int32 InspectChernaskaluxriaTileComponents(AActor* Candidate);
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
