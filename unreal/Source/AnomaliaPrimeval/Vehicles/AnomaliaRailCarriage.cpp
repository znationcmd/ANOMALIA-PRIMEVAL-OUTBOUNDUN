#include "AnomaliaRailCarriage.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
AAnomaliaRailCarriage::AAnomaliaRailCarriage()
{
    bReplicates=true; SetReplicateMovement(true); bNetUseOwnerRelevancy=true;
    RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    Body=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body")); Body->SetupAttachment(RootComponent);
    // Visual-only coaches until swept consist collision and passenger carrying have been validated.
    Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}
void AAnomaliaRailCarriage::BeginPlay()
{
    Super::BeginPlay();
    auto* Mesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Anomalia/Props/Metro1/SM_metro_wagon.SM_metro_wagon"));
    if(!Mesh) return;
    Body->SetStaticMesh(Mesh);
    const auto Bounds=Mesh->GetBounds();
    Body->SetRelativeLocation(-FVector(Bounds.Origin.X,Bounds.Origin.Y,Bounds.Origin.Z-Bounds.BoxExtent.Z)-FVector(0,0,160));
}
