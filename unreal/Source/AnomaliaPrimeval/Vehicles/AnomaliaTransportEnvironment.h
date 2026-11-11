#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaTransportEnvironment.generated.h"
class UBoxComponent;
class USplineComponent;

/** Server map configuration for navigable water. No fake water rendering or infinite ocean assumption. */
UCLASS(Blueprintable)
class ANOMALIAPRIMEVAL_API AAnomaliaNavigableWater : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaNavigableWater();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Water")
    TObjectPtr<UBoxComponent> Bounds;
    /** Local surface elevation inside this axis-aligned water region, in cm. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Water")
    float SurfaceOffset = 0.f;
    bool Sample(const FVector& Position, double& SurfaceZ, double& BottomZ) const;
};

/** Author a track spline in the map; actual rail meshes are supplied separately. */
UCLASS(Blueprintable)
class ANOMALIAPRIMEVAL_API AAnomaliaRailTrack : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaRailTrack();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Rail")
    TObjectPtr<USplineComponent> Track;
    /** Server identity for future route persistence. Must be unique within the server map. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Rail")
    FName RouteId;
};
