#include "AnomaliaHomesteadStation.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaInventoryComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/StaticMesh.h"

AAnomaliaHomesteadStation::AAnomaliaHomesteadStation()
{
    bReplicates = true;
    SetReplicateMovement(false);
    PrimaryActorTick.bCanEverTick = false;
    DisplayMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DisplayMesh"));
    RootComponent = DisplayMesh;
    DisplayMesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    // Temporary visible editor/gameplay placeholder; final farm/furniture meshes are still needed.
    static ConstructorHelpers::FObjectFinder<UStaticMesh> TestCube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (TestCube.Succeeded()) DisplayMesh->SetStaticMesh(TestCube.Object);
}

FName AAnomaliaHomesteadStation::GetHarvestItemId() const
{
    switch (ObjectType)
    {
        case EAnomaliaHomesteadObject::Cow: return TEXT("milk");
        case EAnomaliaHomesteadObject::Chicken: return TEXT("eggs");
        case EAnomaliaHomesteadObject::Beehive: return TEXT("honey");
        default: return NAME_None;
    }
}

bool AAnomaliaHomesteadStation::TryHarvest(AAnomaliaSurvivor* Survivor)
{
    if (!HasAuthority() || !IsValid(Survivor) || !Survivor->HasAuthority() ||
        !Survivor->GetController() || Survivor->Health <= 0.f ||
        !Survivor->InventoryComponent || !GetWorld() || Survivor->GetWorld() != GetWorld())
        return false;
    const FName ItemId = GetHarvestItemId();
    if (ItemId.IsNone() ||
        FVector::DistSquared(Survivor->GetActorLocation(), GetActorLocation()) > FMath::Square(275.f))
        return false;
    const float Now = GetWorld()->GetTimeSeconds();
    if (Now < NextHarvestTime) return false;
    // Only commit cooldown after successful inventory addition; full inventories do not lose goods.
    if (!Survivor->InventoryComponent->TryAddItem(ItemId, 1)) return false;
    NextHarvestTime = Now + 120.f;
    ForceNetUpdate();
    return true;
}

void AAnomaliaHomesteadStation::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaHomesteadStation, ObjectType);
    DOREPLIFETIME(AAnomaliaHomesteadStation, NextHarvestTime);
}
