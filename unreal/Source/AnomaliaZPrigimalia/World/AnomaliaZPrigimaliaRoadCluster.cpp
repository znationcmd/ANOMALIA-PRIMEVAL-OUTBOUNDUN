#include "AnomaliaZPrigimaliaRoadCluster.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"

AAnomaliaZPrigimaliaRoadCluster::AAnomaliaZPrigimaliaRoadCluster()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = false;
    RoadInstances = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
        TEXT("RoadInstances"));
    RootComponent = RoadInstances;
    RoadInstances->SetMobility(EComponentMobility::Static);
    RoadInstances->SetCollisionProfileName(TEXT("BlockAll"));
    RoadInstances->SetGenerateOverlapEvents(false);
}

bool AAnomaliaZPrigimaliaRoadCluster::ConfigureRoadMesh(UStaticMesh* SharedMesh)
{
    if (!IsValid(SharedMesh) || RoadInstances == nullptr || RoadInstances->GetInstanceCount() != 0)
    {
        return false;
    }
    return RoadInstances->SetStaticMesh(SharedMesh);
}

int32 AAnomaliaZPrigimaliaRoadCluster::AddRoadPieceWorld(const FTransform& WorldTransform)
{
    if (RoadInstances == nullptr || RoadInstances->GetStaticMesh() == nullptr ||
        RoadInstances->GetInstanceCount() >= MaxRoadPiecesPerActor)
    {
        return INDEX_NONE;
    }
    // Each instance retains its own grade/heading/scale while sharing collision
    // profile and material with the source City Sample mesh.
    return RoadInstances->AddInstance(WorldTransform, true);
}

int32 AAnomaliaZPrigimaliaRoadCluster::RoadPieceCount() const
{
    return RoadInstances ? RoadInstances->GetInstanceCount() : 0;
}
