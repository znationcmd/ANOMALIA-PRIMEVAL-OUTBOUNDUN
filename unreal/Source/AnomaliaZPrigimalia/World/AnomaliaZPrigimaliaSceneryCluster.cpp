#include "AnomaliaZPrigimaliaSceneryCluster.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
AAnomaliaZPrigimaliaSceneryCluster::AAnomaliaZPrigimaliaSceneryCluster()
{
    PrimaryActorTick.bCanEverTick=false;
    Instances=CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("Instances"));
    RootComponent=Instances;
    Instances->SetMobility(EComponentMobility::Static);
    Instances->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}
