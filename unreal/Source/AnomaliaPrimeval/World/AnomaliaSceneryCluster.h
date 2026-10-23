#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaSceneryCluster.generated.h"
class UHierarchicalInstancedStaticMeshComponent;
/** One spatially streamed cluster per species and kilometre, authored by the editor. */
UCLASS()
class ANOMALIAPRIMEVAL_API AAnomaliaSceneryCluster : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaSceneryCluster();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|World")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> Instances;
};
