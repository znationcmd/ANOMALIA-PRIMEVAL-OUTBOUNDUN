#include "AnomaliaVehiclePawn.h"
#include "AnomaliaSurvivor.h"
#include "Vehicles/AnomaliaTransportMovement.h"
#include "Engine/World.h"
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
    TransportMovement = CreateDefaultSubobject<UAnomaliaTransportMovement>(TEXT("TransportMovement"));
    TransportMovement->SetUpdatedComponent(Collision);
    InteriorCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("InteriorCamera"));
    InteriorCamera->SetupAttachment(Collision);
    InteriorCamera->SetRelativeLocation(FVector(80.f,0.f,90.f));
    InteriorCamera->bUsePawnControlRotation = true;
    InteriorCamera->SetAutoActivate(false);
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
    Movement->MaxSpeed = Definition.MaxSpeedKmh * SpeedMultiplier * (100000.f / 3600.f);
    Movement->Acceleration = FMath::Max(150.f, Movement->MaxSpeed * 0.55f);
    Movement->Deceleration = Movement->Acceleration * 1.4f;
    TransportMovement->Configure(Definition, SpeedMultiplier);
    // Only one movement system may move the collision root. Clients receive authoritative actor movement.
    Movement->SetComponentTickEnabled(HasAuthority() && !TransportMovement->IsTransport());
    OnVehicleConfigured(Definition);
}

void AAnomaliaVehiclePawn::OnRep_VehicleId()
{
    ApplyDefinition();
}

bool AAnomaliaVehiclePawn::ConfigureRuntimeTuning(float InitialFuelPercent, float ConsumptionPerSecond, float NewSpeedMultiplier)
{
    if (!HasAuthority() || !FMath::IsFinite(InitialFuelPercent) ||
        !FMath::IsFinite(ConsumptionPerSecond) || !FMath::IsFinite(NewSpeedMultiplier) ||
        InitialFuelPercent < 0.f || InitialFuelPercent > 100.f ||
        ConsumptionPerSecond < 0.f || ConsumptionPerSecond > 10.f ||
        NewSpeedMultiplier < 0.1f || NewSpeedMultiplier > 3.f) return false;
    FuelPercent = InitialFuelPercent;
    FuelConsumptionPerSecond = ConsumptionPerSecond;
    SpeedMultiplier = NewSpeedMultiplier;
    ApplyDefinition();
    OnFuelChanged(FuelPercent);
    ForceNetUpdate();
    return true;
}

void AAnomaliaVehiclePawn::OnRep_Tuning()
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

UPawnMovementComponent* AAnomaliaVehiclePawn::GetMovementComponent() const
{
    return TransportMovement && TransportMovement->IsTransport() ?
        static_cast<UPawnMovementComponent*>(TransportMovement.Get()) : static_cast<UPawnMovementComponent*>(Movement.Get());
}

void AAnomaliaVehiclePawn::ClearControls()
{
    ForwardAxis=SteeringAxis=PitchAxis=RollAxis=VerticalAxis=BrakeAxis=0.f;
}

void AAnomaliaVehiclePawn::UnPossessed()
{
    ClearControls();
    LastControlReceived=-1;
    Super::UnPossessed();
}

void AAnomaliaVehiclePawn::ServerSetControls_Implementation(float Forward,float Steering)
{
    ServerSetTransportControls_Implementation(Forward,Steering,0,0,0,0);
}

void AAnomaliaVehiclePawn::ServerSetTransportControls_Implementation(float Forward,float Steering,float Pitch,float Roll,float Vertical,float Brake)
{
    if (!IsPlayerControlled() || !FMath::IsFinite(Forward) || !FMath::IsFinite(Steering) ||
        !FMath::IsFinite(Pitch) || !FMath::IsFinite(Roll) || !FMath::IsFinite(Vertical) || !FMath::IsFinite(Brake)) return;
    ForwardAxis=FMath::Clamp(Forward,-1.f,1.f);
    SteeringAxis=FMath::Clamp(Steering,-1.f,1.f);
    PitchAxis=FMath::Clamp(Pitch,-1.f,1.f);
    RollAxis=FMath::Clamp(Roll,-1.f,1.f);
    VerticalAxis=FMath::Clamp(Vertical,-1.f,1.f);
    BrakeAxis=FMath::Clamp(Brake,0.f,1.f);
    LastControlReceived=GetWorld()->GetTimeSeconds();
}

void AAnomaliaVehiclePawn::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!FMath::IsFinite(DeltaSeconds) || DeltaSeconds<=0) return;
    if (IsLocallyControlled() && !HasAuthority())
    {
        ControlSendElapsed+=DeltaSeconds;
        if(ControlSendElapsed>=0.05f)
        {
            ControlSendElapsed=0;
            ServerSetTransportControls(ForwardAxis,SteeringAxis,PitchAxis,RollAxis,VerticalAxis,BrakeAxis);
        }
    }
    if (!HasAuthority()) return;
    const bool bDriver=IsPlayerControlled();
    const bool bStale=bDriver && !IsLocallyControlled() && GetWorld()->GetTimeSeconds()-LastControlReceived>1.0;
    if (!bDriver || bStale) ClearControls();
    const FAnomaliaVehicleDefinition Definition=GetVehicleDefinition();
    if (Definition.Id.IsNone()) return;
    const bool bPowered=bDriver && !bStale && FuelPercent > KINDA_SMALL_NUMBER;
    if (TransportMovement->IsTransport())
    {
        AnomaliaTransport::Controls Controls;
        Controls.Throttle=ForwardAxis; Controls.Yaw=SteeringAxis; Controls.Pitch=PitchAxis;
        Controls.Roll=RollAxis; Controls.Vertical=VerticalAxis;
        Controls.Brake=(!bDriver||bStale)?1:BrakeAxis;
        TransportMovement->Simulate(DeltaSeconds,Controls,bPowered);
    }
    else
    {
        if(bPowered) AddMovementInput(GetActorForwardVector(),ForwardAxis);
        if(bPowered && FMath::Abs(SteeringAxis)>KINDA_SMALL_NUMBER)
            AddActorWorldRotation(FRotator(0,SteeringAxis*65.f*DeltaSeconds,0));
    }
    // Aircraft consume fuel while maintaining powered lift, even at neutral forward input.
    const float Demand=Definition.Domain==EAnomaliaVehicleDomain::Air?
        FMath::Max(0.2f,FMath::Abs(ForwardAxis)+0.25f*FMath::Abs(VerticalAxis)):FMath::Abs(ForwardAxis);
    if(bPowered && Demand>KINDA_SMALL_NUMBER)
    {
        const float OldFuel=FuelPercent;
        FuelPercent=FMath::Max(0.f,FuelPercent-Demand*FuelConsumptionPerSecond*FMath::Min(DeltaSeconds,0.25f));
        if(FMath::FloorToInt(OldFuel)!=FMath::FloorToInt(FuelPercent)||FuelPercent<=KINDA_SMALL_NUMBER)
        { OnFuelChanged(FuelPercent); ForceNetUpdate(); }
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
    ClearControls();
    LastControlReceived=GetWorld()->GetTimeSeconds();
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

void AAnomaliaVehiclePawn::InputForward(float Value) { if(IsLocallyControlled()) ForwardAxis=FMath::IsFinite(Value)?FMath::Clamp(Value,-1.f,1.f):0; }
void AAnomaliaVehiclePawn::InputSteering(float Value) { if(IsLocallyControlled()) SteeringAxis=FMath::IsFinite(Value)?FMath::Clamp(Value,-1.f,1.f):0; }
void AAnomaliaVehiclePawn::InputPitch(float Value) { if(IsLocallyControlled()) PitchAxis=FMath::IsFinite(Value)?FMath::Clamp(Value,-1.f,1.f):0; }
void AAnomaliaVehiclePawn::InputRoll(float Value) { if(IsLocallyControlled()) RollAxis=FMath::IsFinite(Value)?FMath::Clamp(Value,-1.f,1.f):0; }
void AAnomaliaVehiclePawn::InputVertical(float Value) { if(IsLocallyControlled()) VerticalAxis=FMath::IsFinite(Value)?FMath::Clamp(Value,-1.f,1.f):0; }
void AAnomaliaVehiclePawn::InputBrake(float Value) { if(IsLocallyControlled()) BrakeAxis=FMath::IsFinite(Value)?FMath::Clamp(Value,0.f,1.f):0; }
void AAnomaliaVehiclePawn::InputTurn(float Value) { if(IsLocallyControlled()) AddControllerYawInput(Value); }
void AAnomaliaVehiclePawn::InputLookUp(float Value) { if(IsLocallyControlled()) AddControllerPitchInput(Value); }
void AAnomaliaVehiclePawn::InputCamera()
{
    if(!IsLocallyControlled()) return;
    const bool bInterior=!InteriorCamera->IsActive();
    FollowCamera->SetActive(!bInterior);
    InteriorCamera->SetActive(bInterior);
}

void AAnomaliaVehiclePawn::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);
    PlayerInputComponent->BindAxis(TEXT("MoveForward"),this,&AAnomaliaVehiclePawn::InputForward);
    PlayerInputComponent->BindAxis(TEXT("MoveRight"),this,&AAnomaliaVehiclePawn::InputSteering);
    PlayerInputComponent->BindAxis(TEXT("VehiclePitch"),this,&AAnomaliaVehiclePawn::InputPitch);
    PlayerInputComponent->BindAxis(TEXT("VehicleRoll"),this,&AAnomaliaVehiclePawn::InputRoll);
    PlayerInputComponent->BindAxis(TEXT("VehicleVertical"),this,&AAnomaliaVehiclePawn::InputVertical);
    PlayerInputComponent->BindAxis(TEXT("VehicleBrake"),this,&AAnomaliaVehiclePawn::InputBrake);
    PlayerInputComponent->BindAxis(TEXT("Turn"),this,&AAnomaliaVehiclePawn::InputTurn);
    PlayerInputComponent->BindAxis(TEXT("LookUp"),this,&AAnomaliaVehiclePawn::InputLookUp);
    PlayerInputComponent->BindAction(TEXT("VehicleCamera"),IE_Pressed,this,&AAnomaliaVehiclePawn::InputCamera);
    PlayerInputComponent->BindAction(TEXT("Interact"),IE_Pressed,this,&AAnomaliaVehiclePawn::InputExitVehicle);
}

void AAnomaliaVehiclePawn::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaVehiclePawn, VehicleId);
    DOREPLIFETIME(AAnomaliaVehiclePawn, FuelPercent);
    DOREPLIFETIME(AAnomaliaVehiclePawn, SpeedMultiplier);
}
