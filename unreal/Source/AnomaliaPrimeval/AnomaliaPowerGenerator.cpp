#include "AnomaliaPowerGenerator.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Net/UnrealNetwork.h"

AAnomaliaPowerGenerator::AAnomaliaPowerGenerator()
{
    bReplicates = true;
    PrimaryActorTick.bCanEverTick = true;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    RootComponent = SceneRoot;
    VisualMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VisualMesh"));
    VisualMesh->SetupAttachment(SceneRoot);
}

bool AAnomaliaPowerGenerator::SetRunningOnServer(bool bStart)
{
    if (!HasAuthority() || (bStart && FuelLitres <= 0.f)) return false;
    bRunning = bStart;
    ForceNetUpdate();
    return true;
}

bool AAnomaliaPowerGenerator::RefuelOnServer(float Litres)
{
    if (!HasAuthority() || !FMath::IsFinite(Litres) || Litres <= 0.f || Litres > 30.f) return false;
    FuelLitres = FMath::Clamp(FuelLitres + Litres, 0.f, 30.f);
    ForceNetUpdate();
    return true;
}

bool AAnomaliaPowerGenerator::IsSupplyingActor(const AActor* Target) const
{
    return IsValid(Target) && Target->GetWorld() == GetWorld() &&
        bRunning && FuelLitres > 0.f &&
        FVector::DistSquared(Target->GetActorLocation(), GetActorLocation()) <= FMath::Square(MaxCableDistanceCm);
}

void AAnomaliaPowerGenerator::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!HasAuthority() || !bRunning) return;
    FuelLitres = FMath::Max(0.f, FuelLitres - FMath::Max(0.f, DeltaSeconds) * LitresPerHour / 3600.f);
    if (FuelLitres <= 0.f) bRunning = false;
}

void AAnomaliaPowerGenerator::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaPowerGenerator, bRunning);
    DOREPLIFETIME(AAnomaliaPowerGenerator, FuelLitres);
}
