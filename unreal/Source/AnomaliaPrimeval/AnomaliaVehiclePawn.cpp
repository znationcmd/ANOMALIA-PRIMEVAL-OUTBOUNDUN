#include "AnomaliaVehiclePawn.h"
#include "Camera/CameraComponent.h"
#include "Components/InputComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/FloatingPawnMovement.h"
#include "GameFramework/SpringArmComponent.h"
#include "Net/UnrealNetwork.h"

AAnomaliaVehiclePawn::AAnomaliaVehiclePawn()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = true;
    SetReplicateMovement(true);
    Collision = CreateDefaultSubobject<USphereComponent>(TEXT("Collision"));
    Collision->InitSphereRadius(160.f);
    Collision->SetCollisionProfileName(TEXT("Pawn"));
    RootComponent = Collision;
    Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
    Body->SetupAttachment(Collision);
    Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    CameraBoom->SetupAttachment(Collision);
    CameraBoom->TargetArmLength = 650.f;
    CameraBoom->bUsePawnControlRotation = true;
    FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
    FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
    FollowCamera->bUsePawnControlRotation = false;
    Movement = CreateDefaultSubobject<UFloatingPawnMovement>(TEXT("Movement"));
    Movement->UpdatedComponent = Collision;
    AutoPossessPlayer = EAutoReceiveInput::Disabled;
}

void AAnomaliaVehiclePawn::BeginPlay()
{
    Super::BeginPlay();
    ApplyDefinition();
}

bool AAnomaliaVehiclePawn::ConfigureVehicle(FName NewVehicleId)
{
    if (!HasAuthority()) return false;
    FAnomaliaVehicleDefinition Definition;
    if (!UAnomaliaVehicleCatalog::FindVehicleDefinition(NewVehicleId, Definition)) return false;
    VehicleId = NewVehicleId;
    ApplyDefinition();
    ForceNetUpdate();
    return true;
}

FAnomaliaVehicleDefinition AAnomaliaVehiclePawn::GetVehicleDefinition() const
{
    FAnomaliaVehicleDefinition Result;
    UAnomaliaVehicleCatalog::FindVehicleDefinition(VehicleId, Result);
    return Result;
}

void AAnomaliaVehiclePawn::ApplyDefinition()
{
    const FAnomaliaVehicleDefinition Definition = GetVehicleDefinition();
    // Data speeds are in km/h; UE movement is in cm/s.
    Movement->MaxSpeed = Definition.MaxSpeedKmh * (100000.f / 3600.f);
    Movement->Acceleration = FMath::Max(150.f, Movement->MaxSpeed * 0.55f);
    Movement->Deceleration = Movement->Acceleration * 1.4f;
    OnVehicleConfigured(Definition);
}

void AAnomaliaVehiclePawn::OnRep_VehicleId()
{
    ApplyDefinition();
}

void AAnomaliaVehiclePawn::ServerSetControls_Implementation(float Forward, float Steering)
{
    if (!IsPlayerControlled()) return;
    ForwardAxis = FMath::Clamp(Forward, -1.f, 1.f);
    SteeringAxis = FMath::Clamp(Steering, -1.f, 1.f);
}

void AAnomaliaVehiclePawn::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!HasAuthority()) return;
    const FAnomaliaVehicleDefinition Definition = GetVehicleDefinition();
    if (Definition.Id.IsNone()) return;
    if (FMath::Abs(ForwardAxis) > KINDA_SMALL_NUMBER)
    {
        AddMovementInput(GetActorForwardVector(), ForwardAxis);
    }
    const float TurnRate = Definition.Domain == EAnomaliaVehicleDomain::Water ||
        Definition.Domain == EAnomaliaVehicleDomain::Underwater ? 22.f : 65.f;
    if (FMath::Abs(SteeringAxis) > KINDA_SMALL_NUMBER)
    {
        AddActorWorldRotation(FRotator(0.f, SteeringAxis * TurnRate * DeltaSeconds, 0.f));
    }
}

void AAnomaliaVehiclePawn::InputForward(float Value)
{
    if (!IsLocallyControlled()) return;
    ForwardAxis = FMath::Clamp(Value, -1.f, 1.f);
    if (HasAuthority()) return;
    ServerSetControls(ForwardAxis, SteeringAxis);
}

void AAnomaliaVehiclePawn::InputSteering(float Value)
{
    if (!IsLocallyControlled()) return;
    SteeringAxis = FMath::Clamp(Value, -1.f, 1.f);
    if (HasAuthority()) return;
    ServerSetControls(ForwardAxis, SteeringAxis);
}

void AAnomaliaVehiclePawn::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);
    PlayerInputComponent->BindAxis(TEXT("MoveForward"), this, &AAnomaliaVehiclePawn::InputForward);
    PlayerInputComponent->BindAxis(TEXT("MoveRight"), this, &AAnomaliaVehiclePawn::InputSteering);
}

void AAnomaliaVehiclePawn::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaVehiclePawn, VehicleId);
}
