#include "AnomaliaZPrigimaliaWaterSource.h"
#include "Components/SceneComponent.h"
#include "Net/UnrealNetwork.h"

AAnomaliaZPrigimaliaWaterSource::AAnomaliaZPrigimaliaWaterSource()
{
    bReplicates = true;
    bNetLoadOnClient = true;
    WaterPoint = CreateDefaultSubobject<USceneComponent>(TEXT("WaterPoint"));
    RootComponent = WaterPoint;
}

bool AAnomaliaZPrigimaliaWaterSource::CanFillFrom(const FVector& CharacterLocation) const
{
    return bAvailable && !IsActorBeingDestroyed() &&
        FMath::IsFinite(FillRadiusCm) && FillRadiusCm >= 50.f && FillRadiusCm <= 400.f &&
        !CharacterLocation.ContainsNaN() &&
        FVector::DistSquared(CharacterLocation, GetActorLocation()) <= FMath::Square(FillRadiusCm);
}

void AAnomaliaZPrigimaliaWaterSource::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaZPrigimaliaWaterSource, bPotable);
}
