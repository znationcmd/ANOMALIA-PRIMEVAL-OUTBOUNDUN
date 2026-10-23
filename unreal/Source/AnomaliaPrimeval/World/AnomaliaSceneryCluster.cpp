#include "AnomaliaSceneryCluster.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
AAnomaliaSceneryCluster::AAnomaliaSceneryCluster()
{
    PrimaryActorTick.bCanEverTick=false;
    Instances=CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("Instances"));
    RootComponent=Instances;
    Instances->SetMobility(EComponentMobility::Static);
    Instances->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}
