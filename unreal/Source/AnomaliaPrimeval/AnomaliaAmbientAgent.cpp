#include "AnomaliaAmbientAgent.h"
#include "AnomaliaSurvivor.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

AAnomaliaAmbientAgent::AAnomaliaAmbientAgent()
{
    bReplicates = true;
    SetReplicateMovement(true);
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = 0.12f;
    Collision = CreateDefaultSubobject<USphereComponent>(TEXT("Collision"));
    Collision->InitSphereRadius(48.f);
    Collision->SetCollisionProfileName(TEXT("Pawn"));
    RootComponent = Collision;
    PrototypeVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PrototypeVisual"));
    PrototypeVisual->SetupAttachment(Collision);
    PrototypeVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    if (Sphere.Succeeded()) PrototypeVisual->SetStaticMesh(Sphere.Object);
}

void AAnomaliaAmbientAgent::BeginPlay()
{
    Super::BeginPlay();
    UpdatePrototypeVisual();
}

void AAnomaliaAmbientAgent::ConfigureKind(EAnomaliaAmbientKind NewKind)
{
    if (!HasAuthority()) return;
    Kind = NewKind;
    UpdatePrototypeVisual();
    ForceNetUpdate();
}

void AAnomaliaAmbientAgent::OnRep_Kind() { UpdatePrototypeVisual(); }

void AAnomaliaAmbientAgent::UpdatePrototypeVisual()
{
    FVector Scale(1.2f, 0.65f, 1.f);
    switch (Kind)
    {
        case EAnomaliaAmbientKind::Boar: Scale = FVector(1.1f, 0.8f, 0.8f); break;
        case EAnomaliaAmbientKind::Wolf: Scale = FVector(1.3f, 0.55f, 0.85f); break;
        case EAnomaliaAmbientKind::Dinosaur: Scale = FVector(3.5f, 1.25f, 2.2f); break;
        case EAnomaliaAmbientKind::Civilian: Scale = FVector(0.55f, 0.45f, 1.7f); break;
        case EAnomaliaAmbientKind::Guard: Scale = FVector(0.65f, 0.5f, 1.8f); break;
        default: break;
    }
    PrototypeVisual->SetRelativeScale3D(Scale);
}

void AAnomaliaAmbientAgent::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    if (!HasAuthority() || !GetWorld()) return;

    const bool bPredator = Kind == EAnomaliaAmbientKind::Wolf ||
        Kind == EAnomaliaAmbientKind::Dinosaur;
    const bool bTimid = Kind == EAnomaliaAmbientKind::Deer ||
        Kind == EAnomaliaAmbientKind::Boar;
    float Speed = bPredator ? 165.f : (bTimid ? 125.f : 95.f);
    FVector ClosestPlayer = FVector::ZeroVector;
    float BestDistSq = FMath::Square(1700.f);
    for (TActorIterator<AAnomaliaSurvivor> It(GetWorld()); It; ++It)
    {
        if (!IsValid(*It) || It->Health <= 0.f || !It->GetController()) continue;
        const float D = FVector::DistSquared2D(GetActorLocation(), It->GetActorLocation());
        if (D < BestDistSq) { BestDistSq = D; ClosestPlayer = It->GetActorLocation(); }
    }
    if (!ClosestPlayer.IsNearlyZero() && (bPredator || bTimid))
    {
        TravelDirection = (ClosestPlayer - GetActorLocation()).GetSafeNormal2D();
        if (bTimid) TravelDirection *= -1.f;
        Speed *= 1.4f;
        DecisionCountdown = 0.5f;
    }
    else
    {
        DecisionCountdown -= DeltaTime;
        if (DecisionCountdown <= 0.f)
        {
            const float Angle = FMath::FRandRange(-PI, PI);
            TravelDirection = FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.f);
            DecisionCountdown = FMath::FRandRange(2.f, 5.f);
        }
    }

    const FVector NextXY = GetActorLocation() + TravelDirection * Speed * DeltaTime;
    const FVector RayStart = NextXY + FVector(0, 0, 1200.f);
    const FVector RayEnd = NextXY - FVector(0, 0, 3000.f);
    FHitResult Ground;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaAgentGround), false, this);
    if (!GetWorld()->LineTraceSingleByChannel(Ground, RayStart, RayEnd, ECC_Visibility, Query)) return;
    FVector Target = NextXY;
    Target.Z = Ground.ImpactPoint.Z + 65.f;
    FHitResult Obstacle;
    SetActorLocation(Target, true, &Obstacle);
    if (Obstacle.bBlockingHit)
    {
        TravelDirection *= -1.f;
        DecisionCountdown = 1.f;
    }
    else
        SetActorRotation(TravelDirection.Rotation());
}

void AAnomaliaAmbientAgent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaAmbientAgent, Kind);
}
