#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaZPrigimaliaTransportEnvironment.generated.h"
class UBoxComponent;
class USplineComponent;

/** Server map configuration for navigable water. No fake water rendering or infinite ocean assumption. */
UCLASS(Blueprintable)
class ANOMALIAZPRIGIMALIA_API AAnomaliaZPrigimaliaNavigableWater : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaZPrigimaliaNavigableWater();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Water")
    TObjectPtr<UBoxComponent> Bounds;
    /** Local surface elevation inside this axis-aligned water region, in cm. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Water")
    float SurfaceOffset = 0.f;
    bool Sample(const FVector& Position, double& SurfaceZ, double& BottomZ) const;
};

/** Author a track spline in the map; actual rail meshes are supplied separately. */
UCLASS(Blueprintable)
class ANOMALIAZPRIGIMALIA_API AAnomaliaZPrigimaliaRailTrack : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaZPrigimaliaRailTrack();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Rail")
    TObjectPtr<USplineComponent> Track;
    /** Server identity for future route persistence. Must be unique within the server map. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Rail")
    FName RouteId;
};
