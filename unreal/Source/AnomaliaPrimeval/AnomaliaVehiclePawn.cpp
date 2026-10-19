#include "AnomaliaVehiclePawn.h"
#include "AnomaliaSurvivor.h"
#include "GameFramework/Controller.h"
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

bool AAnomaliaVehiclePawn::RefuelOnServer(float AmountPercent)
{
    if (!HasAuthority() || !FMath::IsFinite(AmountPercent) || AmountPercent <= 0.f) return false;
    const float Previous = FuelPercent;
    FuelPercent = FMath::Clamp(FuelPercent + AmountPercent, 0.f, 100.f);
    if (FuelPercent > Previous) { OnFuelChanged(FuelPercent); ForceNetUpdate(); return true; }
    return false;
}

void AAnomaliaVehiclePawn::OnRep_Fuel()
{
    OnFuelChanged(FuelPercent);
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
    if (FuelPercent > KINDA_SMALL_NUMBER && FMath::Abs(ForwardAxis) > KINDA_SMALL_NUMBER)
    {
        AddMovementInput(GetActorForwardVector(), ForwardAxis);
        const float OldFuel = FuelPercent;
        FuelPercent = FMath::Max(0.f, FuelPercent - FMath::Abs(ForwardAxis) * FuelConsumptionPerSecond * DeltaSeconds);
        if (FMath::FloorToInt(OldFuel) != FMath::FloorToInt(FuelPercent) || FuelPercent <= KINDA_SMALL_NUMBER)
        {
            OnFuelChanged(FuelPercent);
            ForceNetUpdate();
        }
    }
    const float TurnRate = Definition.Domain == EAnomaliaVehicleDomain::Water ||
        Definition.Domain == EAnomaliaVehicleDomain::Underwater ? 22.f : 65.f;
    if (FuelPercent > KINDA_SMALL_NUMBER && FMath::Abs(SteeringAxis) > KINDA_SMALL_NUMBER)
    {
        AddActorWorldRotation(FRotator(0.f, SteeringAxis * TurnRate * DeltaSeconds, 0.f));
    }
}

bool AAnomaliaVehiclePawn::HasDriver() const
{
    return GetController() != nullptr || ParkedSurvivor.IsValid();
}

bool AAnomaliaVehiclePawn::EnterVehicle(AController* DriverController, AAnomaliaSurvivor* Survivor)
{
    if (!HasAuthority() || !IsValid(DriverController) || !IsValid(Survivor) || HasDriver()) return false;
    if (Survivor->GetController() != DriverController || Survivor->Health <= 0.f) return false;
    if (FVector::DistSquared(GetActorLocation(), Survivor->GetActorLocation()) > FMath::Square(450.f)) return false;
    ParkedSurvivor = Survivor;
    DriverController->Possess(this);
    if (GetController() != DriverController) { ParkedSurvivor.Reset(); return false; }
    Survivor->SetActorHiddenInGame(true);
    Survivor->SetActorEnableCollision(false);
    return true;
}

void AAnomaliaVehiclePawn::ServerExitVehicle_Implementation()
{
    if (!HasAuthority() || !IsPlayerControlled() || !ParkedSurvivor.IsValid()) return;
    AController* DriverController = GetController();
    AAnomaliaSurvivor* Survivor = ParkedSurvivor.Get();
    if (!IsValid(DriverController) || !IsValid(Survivor)) return;
    // Restore the existing character, preserving survival state and inventory references.
    const FVector ExitLocation = GetActorLocation() + GetActorRightVector() * 350.f + FVector(0.f, 0.f, 120.f);
    Survivor->SetActorLocation(ExitLocation, false, nullptr, ETeleportType::TeleportPhysics);
    Survivor->SetActorEnableCollision(true);
    Survivor->SetActorHiddenInGame(false);
    DriverController->Possess(Survivor);
    if (GetController() == nullptr) { ParkedSurvivor.Reset(); ForwardAxis = 0.f; SteeringAxis = 0.f; }
}

void AAnomaliaVehiclePawn::InputExitVehicle()
{
    if (!IsLocallyControlled()) return;
    if (HasAuthority()) ServerExitVehicle_Implementation();
    else ServerExitVehicle();
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
    PlayerInputComponent->BindAction(TEXT("Interact"), IE_Pressed, this, &AAnomaliaVehiclePawn::InputExitVehicle);
}

void AAnomaliaVehiclePawn::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaVehiclePawn, VehicleId);
    DOREPLIFETIME(AAnomaliaVehiclePawn, FuelPercent);
}
