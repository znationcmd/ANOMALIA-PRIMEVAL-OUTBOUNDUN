#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaZPrigimaliaSceneryCluster.generated.h"
class UHierarchicalInstancedStaticMeshComponent;
/** One spatially streamed cluster per species and kilometre, authored by the editor. */
UCLASS()
class ANOMALIAZPRIGIMALIA_API AAnomaliaZPrigimaliaSceneryCluster : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaZPrigimaliaSceneryCluster();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|World")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> Instances;
};
