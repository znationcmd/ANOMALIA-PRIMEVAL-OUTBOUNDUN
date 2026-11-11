#include "AnomaliaTransportEnvironment.h"
#include "Components/BoxComponent.h"
#include "Components/SplineComponent.h"

AAnomaliaNavigableWater::AAnomaliaNavigableWater()
{
    PrimaryActorTick.bCanEverTick=false;
    Bounds=CreateDefaultSubobject<UBoxComponent>(TEXT("NavigableBounds"));
    Bounds->SetBoxExtent(FVector(10000,10000,5000));
    Bounds->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    RootComponent=Bounds;
}
bool AAnomaliaNavigableWater::Sample(const FVector& Position,double& SurfaceZ,double& BottomZ) const
{
    if(Position.ContainsNaN() || !FMath::IsFinite(SurfaceOffset)) return false;
    // Axis-aligned regions are intentional: rotated/scaled region transforms do not fake sloping water.
    const FBox Box=Bounds->Bounds.GetBox();
    SurfaceZ=GetActorLocation().Z+SurfaceOffset;
    BottomZ=Box.Min.Z;
    return Position.X>=Box.Min.X && Position.X<=Box.Max.X && Position.Y>=Box.Min.Y && Position.Y<=Box.Max.Y &&
        SurfaceZ>BottomZ+200 && SurfaceZ<=Box.Max.Z && Position.Z>=BottomZ && Position.Z<=SurfaceZ+400;
}
AAnomaliaRailTrack::AAnomaliaRailTrack()
{
    PrimaryActorTick.bCanEverTick=false;
    Track=CreateDefaultSubobject<USplineComponent>(TEXT("Track"));
    RootComponent=Track;
}
