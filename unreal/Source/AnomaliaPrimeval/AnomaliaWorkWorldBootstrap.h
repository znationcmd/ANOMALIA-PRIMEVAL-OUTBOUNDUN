#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaWorkWorldBootstrap.generated.h"

class USceneComponent;
class UInstancedStaticMeshComponent;

/**
 * Opt-in, local PIE preview for the 48km Work Landscape.
 * Place ONE actor on ANOMALIA_WorkMap_Test and press Play.
 * Shows a bounded mock city around the origin. No edits to the .umap or saves.
 * Final roads, architecture, navigation and streamed open world remain separate work.
 */
UCLASS(Blueprintable)
class ANOMALIAPRIMEVAL_API AAnomaliaWorkWorldBootstrap : public AActor
{
    GENERATED_BODY()

public:
    AAnomaliaWorkWorldBootstrap();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Work Preview")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Work Preview")
    TObjectPtr<UInstancedStaticMeshComponent> RoadMesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Work Preview")
    TObjectPtr<UInstancedStaticMeshComponent> BuildingMesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Work Preview")
    TObjectPtr<UInstancedStaticMeshComponent> RoofMesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Work Preview")
    TObjectPtr<UInstancedStaticMeshComponent> TreeTrunks;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Work Preview")
    TObjectPtr<UInstancedStaticMeshComponent> TreeCrowns;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Work Preview", meta=(ClampMin="0", ClampMax="24"))
    int32 AgentCount = 12;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ANOMALIA|Work Preview", meta=(ClampMin="0", ClampMax="128"))
    int32 TreeCount = 60;

    /** Visuals are generated in PIE only; actors do not persist in Content or Saved. */
    virtual void BeginPlay() override;

private:
    bool SampleLandscape(float X, float Y, FVector& OutGround) const;
    void BuildRoads();
    void BuildBuildings();
    void BuildTrees();
    void SpawnPreviewAgents();
};
