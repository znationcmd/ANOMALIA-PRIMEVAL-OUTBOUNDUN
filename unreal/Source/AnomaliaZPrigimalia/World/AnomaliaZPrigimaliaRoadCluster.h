#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaZPrigimaliaRoadCluster.generated.h"

class UHierarchicalInstancedStaticMeshComponent;
class UStaticMesh;

/**
 * One streamable actor per 128 m road cell and reusable mesh.
 * Unlike thousands of AStaticMeshActors, all segments in the same
 * road cell use one hierarchical instanced mesh component. Each keeps
 * its exact world transform (grade, yaw, width, collision).
 *
 * Existing World Partition actors are never migrated or deleted by
 * creating this class. Existing map remains untouched until PIE checks.
 */
UCLASS(Blueprintable)
class ANOMALIAZPRIGIMALIA_API AAnomaliaZPrigimaliaRoadCluster : public AActor
{
    GENERATED_BODY()

public:
    AAnomaliaZPrigimaliaRoadCluster();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Road Optimization")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> RoadInstances;

    /** Only one shared mesh asset per cell, not a duplicated mesh per segment. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Road Optimization")
    bool ConfigureRoadMesh(UStaticMesh* SharedMesh);

    /** Add a road piece in WORLD coordinates; returns INDEX_NONE on refusal. */
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Road Optimization")
    int32 AddRoadPieceWorld(const FTransform& WorldTransform);

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Road Optimization")
    int32 RoadPieceCount() const;

    /** Hard cap prevents unbounded always-loaded road clusters. */
    static constexpr int32 MaxRoadPiecesPerActor = 256;
};
