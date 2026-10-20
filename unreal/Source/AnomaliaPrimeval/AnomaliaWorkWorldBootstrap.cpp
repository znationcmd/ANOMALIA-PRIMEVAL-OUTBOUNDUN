#include "AnomaliaWorkWorldBootstrap.h"
#include "AnomaliaAmbientAgent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "UObject/ConstructorHelpers.h"

AAnomaliaWorkWorldBootstrap::AAnomaliaWorkWorldBootstrap()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = false;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    RootComponent = SceneRoot;

    RoadMesh = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Roads"));
    RoadMesh->SetupAttachment(SceneRoot);
    RoadMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision); // Overlay, not drivable road physics.

    BuildingMesh = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Buildings"));
    BuildingMesh->SetupAttachment(SceneRoot);
    BuildingMesh->SetCollisionProfileName(TEXT("BlockAll"));

    RoofMesh = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Roofs"));
    RoofMesh->SetupAttachment(SceneRoot);
    RoofMesh->SetCollisionProfileName(TEXT("BlockAll"));

    TreeTrunks = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("TreeTrunks"));
    TreeTrunks->SetupAttachment(SceneRoot);
    TreeTrunks->SetCollisionProfileName(TEXT("BlockAll"));

    TreeCrowns = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("TreeCrowns"));
    TreeCrowns->SetupAttachment(SceneRoot);
    TreeCrowns->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cone(TEXT("/Engine/BasicShapes/Cone.Cone"));
    if (Cube.Succeeded())
    {
        RoadMesh->SetStaticMesh(Cube.Object);
        BuildingMesh->SetStaticMesh(Cube.Object);
        RoofMesh->SetStaticMesh(Cube.Object);
        TreeTrunks->SetStaticMesh(Cube.Object);
    }
    if (Cone.Succeeded()) TreeCrowns->SetStaticMesh(Cone.Object);
}

bool AAnomaliaWorkWorldBootstrap::SampleLandscape(float X, float Y, FVector& OutGround) const
{
    if (!GetWorld()) return false;
    FHitResult Hit;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(AnomaliaWorkLandscapeProbe), false);
    Params.AddIgnoredActor(this);
    // Landscape must be loaded around the origin; no bridge/building/sky is accepted as terrain.
    const bool bHit = GetWorld()->LineTraceSingleByChannel(
        Hit, FVector(X, Y, 500000.f), FVector(X, Y, -500000.f),
        ECC_Visibility, Params);
    if (!bHit || !Hit.GetActor() ||
        !Hit.GetActor()->GetClass()->GetName().Contains(TEXT("Landscape")))
        return false;
    OutGround = Hit.ImpactPoint;
    return true;
}

void AAnomaliaWorkWorldBootstrap::BeginPlay()
{
    Super::BeginPlay();
    if (!GetWorld() || !HasAuthority()) return;
    // Opt-in preview; never affect other maps or dedicated servers.
    if (!GetWorld()->GetMapName().EndsWith(TEXT("ANOMALIA_WorkMap_Test")) ||
        GetWorld()->GetNetMode() == NM_DedicatedServer)
        return;

    FVector Ground;
    if (!SampleLandscape(0.f, 0.f, Ground))
    {
        UE_LOG(LogTemp, Warning, TEXT("ANOMALIA Work preview: no loaded Landscape at (0,0); nothing spawned."));
        return;
    }
    BuildRoads();
    BuildBuildings();
    BuildTrees();
    SpawnPreviewAgents();
    UE_LOG(LogTemp, Log, TEXT("ANOMALIA Work preview: roads=%d, buildings=%d, trees=%d, agents<=%d"),
        RoadMesh->GetInstanceCount(), BuildingMesh->GetInstanceCount(),
        TreeTrunks->GetInstanceCount(), AgentCount);
}

void AAnomaliaWorkWorldBootstrap::BuildRoads()
{
    // Two perpendicular prototype streets. Cubes sit above terrain: not a flattened highway.
    constexpr float StepCm = 1500.f;
    for (int32 Index = -40; Index <= 40; ++Index)
    {
        const float Along = static_cast<float>(Index) * StepCm;
        for (int32 Axis = 0; Axis < 2; ++Axis)
        {
            const float X = Axis == 0 ? Along : 0.f;
            const float Y = Axis == 0 ? 0.f : Along;
            FVector Ground;
            if (!SampleLandscape(X, Y, Ground) || Ground.Z <= 50.f) continue;
            const FVector Scale = Axis == 0 ? FVector(15.f, 9.f, 0.08f) : FVector(9.f, 15.f, 0.08f);
            RoadMesh->AddInstance(FTransform(FRotator::ZeroRotator,
                Ground + FVector(0.f, 0.f, 7.f), Scale), true);
        }
    }
}

void AAnomaliaWorkWorldBootstrap::BuildBuildings()
{
    // Buildings flank the east-west street; leave clear road and spawn-space near center.
    // All measurements are centimetres; Engine Cube is 100cm per side.
    FRandomStream Random(6423);
    for (int32 Side : {-1, 1})
    {
        for (int32 Block = -5; Block <= 5; ++Block)
        {
            if (Block == 0) continue;
            const float X = static_cast<float>(Block) * 10000.f;
            const float Y = static_cast<float>(Side) * 3800.f;
            FVector Ground;
            if (!SampleLandscape(X, Y, Ground) || Ground.Z <= 50.f) continue;
            const float Height = Random.FRandRange(500.f, 1450.f);
            const float Width = Random.FRandRange(1000.f, 1700.f);
            const float Depth = Random.FRandRange(850.f, 1150.f);
            BuildingMesh->AddInstance(FTransform(FRotator::ZeroRotator,
                Ground + FVector(0.f, 0.f, Height * 0.5f),
                FVector(Width / 100.f, Depth / 100.f, Height / 100.f)), true);
            RoofMesh->AddInstance(FTransform(FRotator::ZeroRotator,
                Ground + FVector(0.f, 0.f, Height + 30.f),
                FVector(Width / 100.f + 0.6f, Depth / 100.f + 0.6f, 0.6f)), true);
        }
    }
}

void AAnomaliaWorkWorldBootstrap::BuildTrees()
{
    FRandomStream Random(9343);
    const int32 SafeCount = FMath::Clamp(TreeCount, 0, 128);
    for (int32 I = 0; I < SafeCount * 4 && TreeTrunks->GetInstanceCount() < SafeCount; ++I)
    {
        const float X = Random.FRandRange(-85000.f, 85000.f);
        const float Y = Random.FRandRange(-85000.f, 85000.f);
        // Keep test roads and village plots clear.
        if (FMath::Abs(X) < 6500.f || FMath::Abs(Y) < 6500.f) continue;
        FVector Ground;
        if (!SampleLandscape(X, Y, Ground) || Ground.Z <= 50.f) continue;
        const float Height = Random.FRandRange(350.f, 680.f);
        TreeTrunks->AddInstance(FTransform(FRotator::ZeroRotator,
            Ground + FVector(0.f, 0.f, Height * 0.34f),
            FVector(0.5f, 0.5f, Height * 0.0068f)), true);
        TreeCrowns->AddInstance(FTransform(FRotator::ZeroRotator,
            Ground + FVector(0.f, 0.f, Height * 0.80f),
            FVector(3.6f, 3.6f, Height * 0.010f)), true);
    }
}

void AAnomaliaWorkWorldBootstrap::SpawnPreviewAgents()
{
    const int32 SafeCount = FMath::Clamp(AgentCount, 0, 24);
    FRandomStream Random(52517);
    const EAnomaliaAmbientKind Kinds[] = {
        EAnomaliaAmbientKind::Deer, EAnomaliaAmbientKind::Boar,
        EAnomaliaAmbientKind::Wolf, EAnomaliaAmbientKind::Dinosaur,
        EAnomaliaAmbientKind::Civilian, EAnomaliaAmbientKind::Guard
    };
    for (int32 I = 0; I < SafeCount; ++I)
    {
        const float X = Random.FRandRange(-48000.f, 48000.f);
        const float Y = Random.FRandRange(-48000.f, 48000.f);
        FVector Ground;
        if (!SampleLandscape(X, Y, Ground) || Ground.Z <= 50.f) continue;
        FActorSpawnParameters Params;
        Params.SpawnCollisionHandlingOverride =
            ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButDontSpawnIfColliding;
        AAnomaliaAmbientAgent* Agent = GetWorld()->SpawnActor<AAnomaliaAmbientAgent>(
            AAnomaliaAmbientAgent::StaticClass(),
            Ground + FVector(0.f, 0.f, 105.f), FRotator::ZeroRotator, Params);
        if (Agent) Agent->ConfigureKind(Kinds[I % UE_ARRAY_COUNT(Kinds)]);
    }
}
