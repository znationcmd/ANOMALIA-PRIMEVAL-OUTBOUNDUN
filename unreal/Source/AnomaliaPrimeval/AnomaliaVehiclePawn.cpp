#include "AnomaliaVehiclePawn.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaSessionWidget.h"
#include "GameFramework/PlayerController.h"
#include "Vehicles/AnomaliaTransportMovement.h"
#include "Vehicles/AnomaliaRailCarriage.h"
#include "Vehicles/AnomaliaTransportEnvironment.h"
#include "Components/SplineComponent.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Misc/PackageName.h"
#include "GameFramework/Controller.h"
#include "Camera/CameraComponent.h"
#include "Components/InputComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
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
    DriverEntryPoint=CreateDefaultSubobject<USceneComponent>(TEXT("DriverEntryPoint"));
    DriverEntryPoint->SetupAttachment(Collision);
    DriverSeatPoint=CreateDefaultSubobject<USceneComponent>(TEXT("DriverSeatPoint"));
    DriverSeatPoint->SetupAttachment(Collision);
    DriverExitPoint=CreateDefaultSubobject<USceneComponent>(TEXT("DriverExitPoint"));
    DriverExitPoint->SetupAttachment(Collision);
    AutoPossessPlayer = EAutoReceiveInput::Disabled;
    AutoPossessAI = EAutoPossessAI::Disabled; // Parked level vehicles must remain available to the player.
}

void AAnomaliaVehiclePawn::BeginPlay()
{
    Super::BeginPlay();
    ApplyDefinition();
    if(HasAuthority() && IsValid(InitialRailTrack))
        TransportMovement->AssignTrack(InitialRailTrack,InitialRailDistanceCm);
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
    Movement->SetComponentTickEnabled(HasAuthority() && !TransportMovement->IsTransport() && !UsesPhysicsRoadSimulation());
    if(!UsesPhysicsRoadSimulation()) RefreshVehicleVisual();
    OnVehicleConfigured(Definition);
}

void AAnomaliaVehiclePawn::RefreshVehicleVisual()
{
    if(!bPresentationCaptured)
    {
        OriginalBodyTransform=Body->GetRelativeTransform();
        OriginalCameraDistance=CameraBoom->TargetArmLength;
        bPresentationCaptured=true;
    }
    if(AutomaticModel.IsValid() && Body->GetStaticMesh()==AutomaticModel.Get())
    {
        Body->SetStaticMesh(nullptr);
        Body->SetRelativeTransform(OriginalBodyTransform);
        CameraBoom->TargetArmLength=OriginalCameraDistance;
    }
    AutomaticModel.Reset();
    FAnomaliaVehicleDefinition Definition;
    if(!UAnomaliaVehicleCatalog::FindVehicleDefinition(VehicleId,Definition)) return;
    // IDs come from the fixed server-authorized catalogue, never from an arbitrary client path.
    const FString Id=VehicleId.ToString();
    const FString Package=TEXT("/Game/Anomalia/Vehicles/")+Id+TEXT("/SM_")+Id;
    UStaticMesh* Mesh=PresentationMeshOverride.Get();
    if(!Mesh)
    {
        if(!FPackageName::DoesPackageExist(Package)) return; // Keep the Blueprint's own art, if any.
        Mesh=LoadObject<UStaticMesh>(nullptr,*(Package+TEXT(".SM_")+Id));
    }
    if(!Mesh) return;
    Body->SetStaticMesh(Mesh);
    const float ArtYaw=FMath::IsFinite(PresentationYawDegrees)?PresentationYawDegrees:0.f;
    const FRotator Orientation(0,(VehicleId==FName(TEXT("airliner"))?180.f:0.f)+ArtYaw,0);
    const FBoxSphereBounds Bounds=Mesh->GetBounds();
    const FVector BottomCenter(Bounds.Origin.X,Bounds.Origin.Y,Bounds.Origin.Z-Bounds.BoxExtent.Z);
    Body->SetRelativeRotation(Orientation);
    Body->SetRelativeLocation(-Orientation.RotateVector(BottomCenter)-FVector(0,0,Collision->GetUnscaledSphereRadius()));
    CameraBoom->TargetArmLength=FMath::Max(OriginalCameraDistance,static_cast<float>(Bounds.BoxExtent.GetMax()*2.5));
    AutomaticModel=Mesh;
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
    const bool bPowered=bDriver && !bStale && FuelPercent > KINDA_SMALL_NUMBER && IsEngineProvidingPower();
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
        SimulateRoadDrive(DeltaSeconds,ForwardAxis,SteeringAxis,BrakeAxis,bPowered,!bDriver||bStale);
    }
    UpdateMetroCoaches();
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
    if (!HasAuthority() || !IsValid(DriverController) || !IsValid(Survivor) || HasDriver() || !IsDriveReady()) return false;
    if (Survivor->GetController() != DriverController || Survivor->Health <= 0.f) return false;
    if (!CanEnterFrom(Survivor)) return false;
    ClearControls();
    LastControlReceived=GetWorld()->GetTimeSeconds();
    ParkedSurvivor = Survivor;
    DriverController->Possess(this);
    if (GetController() != DriverController) { ParkedSurvivor.Reset(); return false; }
    Survivor->SetActorHiddenInGame(true);
    Survivor->SetActorEnableCollision(false);
    if(bUseAuthoredDriverPoints)
        Survivor->AttachToComponent(DriverSeatPoint,FAttachmentTransformRules::SnapToTargetNotIncludingScale);
    return true;
}

bool AAnomaliaVehiclePawn::CanEnterFrom(const AAnomaliaSurvivor* Survivor) const
{
    if(!IsValid(Survivor) || Survivor->GetWorld()!=GetWorld() || !GetWorld())return false;
    const FVector Entry=bUseAuthoredDriverPoints?DriverEntryPoint->GetComponentLocation():GetActorLocation();
    const float Range=bUseAuthoredDriverPoints?250.f:450.f;
    if(FVector::DistSquared(Entry,Survivor->GetActorLocation())>FMath::Square(Range))return false;
    FVector Eye;FRotator Rotation;Survivor->GetActorEyesViewPoint(Eye,Rotation);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaVehicleEntry),true);
    Query.AddIgnoredActor(this);Query.AddIgnoredActor(Survivor);FHitResult Hit;
    return !GetWorld()->LineTraceSingleByChannel(Hit,Eye,Entry,ECC_Visibility,Query);
}

bool AAnomaliaVehiclePawn::FindSafeDriverExit(const AAnomaliaSurvivor* Survivor,FVector& Location,FString* Diagnostics) const
{
    if(Diagnostics)*Diagnostics=FString::Printf(TEXT("vehicle=%s origin=%s radius=%.2f"),*VehicleId.ToString(),*GetActorLocation().ToCompactString(),Collision->GetScaledSphereRadius());
    if(!IsValid(Survivor) || Survivor->GetWorld()!=GetWorld() || !GetWorld())return false;
    const auto* Capsule=Survivor->GetCapsuleComponent();
    const float Radius=Capsule->GetScaledCapsuleRadius(),HalfHeight=Capsule->GetScaledCapsuleHalfHeight();
    FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaVehicleExit),false);
    Query.AddIgnoredActor(this);Query.AddIgnoredActor(Survivor);
    TArray<FVector> Candidates;
    if(bUseAuthoredDriverPoints)Candidates.Add(DriverExitPoint->GetComponentLocation());
    else
    {
        // Legacy models have no validated crew markers. Keep their compatibility
        // path, but never blindly teleport a player through terrain or a wall.
        for(const FVector Direction:{GetActorRightVector(),-GetActorRightVector(),-GetActorForwardVector()})
            Candidates.Add(GetActorLocation()+Direction*350.f);
    }
    for(const FVector Candidate:Candidates)
    {
        const auto Reject=[&](const FString& Reason){if(Diagnostics)*Diagnostics+=TEXT("; candidate=")+Candidate.ToCompactString()+TEXT(" ")+Reason;};
        FHitResult Floor;
        if(!GetWorld()->LineTraceSingleByChannel(Floor,Candidate+FVector(0,0,HalfHeight+150.f),
             Candidate-FVector(0,0,600.f),ECC_Pawn,Query)){Reject(TEXT("NO_FLOOR"));continue;}
        const FString FloorInfo=FString::Printf(TEXT("floor=%s z=%.2f nz=%.3f"),*GetNameSafe(Floor.GetActor()),Floor.ImpactPoint.Z,Floor.ImpactNormal.Z);
        if(Floor.ImpactNormal.Z<Survivor->GetCharacterMovement()->GetWalkableFloorZ()){Reject(TEXT("SLOPE ")+FloorInfo);continue;}
        const float ExpectedFloor=bUseAuthoredDriverPoints?Candidate.Z:GetExpectedSupportFloorZ();
        if(Floor.ImpactPoint.Z>ExpectedFloor+Survivor->GetCharacterMovement()->MaxStepHeight ||
           Floor.ImpactPoint.Z<ExpectedFloor-200.f){Reject(TEXT("HEIGHT ")+FloorInfo+FString::Printf(TEXT(" expected=%.2f"),ExpectedFloor));continue;}
        const FVector Centre(Floor.ImpactPoint.X,Floor.ImpactPoint.Y,Floor.ImpactPoint.Z+HalfHeight+2.f);
        if(GetWorld()->OverlapBlockingTestByChannel(Centre,FQuat::Identity,ECC_Pawn,
              FCollisionShape::MakeCapsule(Radius,HalfHeight),Query)){Reject(TEXT("DESTINATION_BLOCKED ")+FloorInfo);continue;}
        // Refuse exit points overlapping our actual root, which is ignored above
        // only to allow tracing outward from a seated driver.
        if(FVector::Dist2D(Centre,GetActorLocation())<Collision->GetScaledSphereRadius()+Radius+5.f){Reject(TEXT("VEHICLE_CLEARANCE"));continue;}
        FHitResult PathHit;
        // Start above the vehicle's support plane, which can be a pavement
        // higher than the destination road. A diagonal sweep starting at the
        // destination height would falsely begin inside that pavement.
        const float ClearanceZ=FMath::Max(Centre.Z,GetExpectedSupportFloorZ()+HalfHeight+2.f);
        const FVector Start(GetActorLocation().X,GetActorLocation().Y,ClearanceZ);
        const FVector HighEnd(Centre.X,Centre.Y,ClearanceZ);
        if(GetWorld()->SweepSingleByChannel(PathHit,Start,HighEnd,FQuat::Identity,ECC_Pawn,
             FCollisionShape::MakeCapsule(Radius,HalfHeight),Query)){Reject(FString::Printf(TEXT("PATH_BLOCKED actor=%s at=%s normal=%s startPenetrating=%d "),*GetNameSafe(PathHit.GetActor()),*PathHit.ImpactPoint.ToCompactString(),*PathHit.ImpactNormal.ToCompactString(),PathHit.bStartPenetrating?1:0)+FloorInfo);continue;}
        if(!HighEnd.Equals(Centre,.01f) && GetWorld()->SweepSingleByChannel(PathHit,HighEnd,Centre,FQuat::Identity,ECC_Pawn,
             FCollisionShape::MakeCapsule(Radius,HalfHeight),Query)){Reject(TEXT("LOWERING_BLOCKED ")+FloorInfo);continue;}
        if(Diagnostics)*Diagnostics+=TEXT("; SAFE ")+Centre.ToCompactString();
        Location=Centre;return true;
    }
    return false;
}

void AAnomaliaVehiclePawn::ServerExitVehicle_Implementation()
{
    if (!HasAuthority() || !IsPlayerControlled() || !ParkedSurvivor.IsValid() || !CanDriverExitNow()) return;
    AController* DriverController = GetController();
    AAnomaliaSurvivor* Survivor = ParkedSurvivor.Get();
    if (!IsValid(DriverController) || !IsValid(Survivor)) return;
    // Restore the existing character, preserving survival state and inventory references.
    FVector ExitLocation;
    FString ExitDiagnostic;
    if(!FindSafeDriverExit(Survivor,ExitLocation,&ExitDiagnostic)){UE_LOG(LogTemp,Warning,TEXT("ANOMALIA vehicle exit refused: %s"),*ExitDiagnostic);return;}
    const FVector ExitVelocity=GetDriverExitVelocity();
    if(!TransportMovement->IsTransport())Movement->StopMovementImmediately();
    Survivor->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
    Survivor->SetActorLocation(ExitLocation, false, nullptr, ETeleportType::TeleportPhysics);
    Survivor->SetActorEnableCollision(true);
    Survivor->SetActorHiddenInGame(false);
    DriverController->Possess(Survivor);
    if(DriverController->GetPawn()==Survivor && !ExitVelocity.IsNearlyZero())
        Survivor->LaunchCharacter(ExitVelocity,true,true);
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
    PlayerInputComponent->BindAction(TEXT("Pause"),IE_Pressed,this,&AAnomaliaVehiclePawn::InputPause);
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
    DOREPLIFETIME(AAnomaliaVehiclePawn, PresentationMeshOverride);
    DOREPLIFETIME(AAnomaliaVehiclePawn, PresentationYawDegrees);
    DOREPLIFETIME(AAnomaliaVehiclePawn, FuelPercent);
    DOREPLIFETIME(AAnomaliaVehiclePawn, SpeedMultiplier);
}

void AAnomaliaVehiclePawn::EndPlay(const EEndPlayReason::Type Reason)
{
    if(HasAuthority()) for(AAnomaliaRailCarriage* Coach : MetroCoaches) if(IsValid(Coach)) Coach->Destroy();
    MetroCoaches.Empty();
    Super::EndPlay(Reason);
}

void AAnomaliaVehiclePawn::UpdateMetroCoaches()
{
    if(!HasAuthority()) return;
    if(VehicleId!=FName(TEXT("metro")))
    {
        for(AAnomaliaRailCarriage* Coach : MetroCoaches) if(IsValid(Coach)) Coach->Destroy();
        MetroCoaches.Empty(); return;
    }
    AAnomaliaRailTrack* Route=TransportMovement->GetRailTrack();
    USplineComponent* Track=IsValid(Route)?Route->Track.Get():nullptr;
    if(!Track || Track->GetSplineLength()<=0)
    {
        for(AAnomaliaRailCarriage* Coach : MetroCoaches) if(IsValid(Coach)) Coach->SetActorHiddenInGame(true);
        return;
    }
    // Fixed prototype centre spacing follows the route through curves; no straight parent attachment.
    while(MetroCoaches.Num()<3)
    {
        FActorSpawnParameters Params; Params.Owner=this;
        Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        auto* Coach=GetWorld()->SpawnActor<AAnomaliaRailCarriage>(AAnomaliaRailCarriage::StaticClass(),GetActorTransform(),Params);
        if(!Coach) return;
        Collision->IgnoreActorWhenMoving(Coach,true);
        MetroCoaches.Add(Coach);
    }
    for(int32 Index=0;Index<MetroCoaches.Num();++Index)
    {
        auto* Coach=MetroCoaches[Index].Get(); if(!IsValid(Coach)) continue;
        const double Distance=TransportMovement->GetTrackDistance()-(Index+1)*1850.;
        const double Length=Track->GetSplineLength();
        const bool Visible=Track->IsClosedLoop() || (Distance>=0 && Distance<=Length);
        Coach->SetActorHiddenInGame(!Visible);
        if(!Visible) continue; // Never pile coaches up at an open route endpoint.
        const double Wrapped=Track->IsClosedLoop()?FMath::Fmod(FMath::Fmod(Distance,Length)+Length,Length):Distance;
        Coach->SetActorTransform(Track->GetTransformAtDistanceAlongSpline(Wrapped,ESplineCoordinateSpace::World,false),false,nullptr,ETeleportType::TeleportPhysics);
    }
}

AAnomaliaSurvivor* AAnomaliaVehiclePawn::GetStoredDriverSurvivor() const { return ParkedSurvivor.Get(); }
void AAnomaliaVehiclePawn::InputPause() { UAnomaliaSessionWidget::Open(Cast<APlayerController>(Controller)); }



void AAnomaliaVehiclePawn::SimulateRoadDrive(float DeltaSeconds,float Throttle,float Steering,float Brake,
    bool bPowered,bool bDriverMissing)
{
    if(Brake>0.f) Movement->Velocity=FMath::VInterpConstantTo(Movement->Velocity,FVector::ZeroVector,DeltaSeconds,Movement->Deceleration*4.f);
    else if(bPowered) AddMovementInput(GetActorForwardVector(),Throttle);
    if(bPowered && FMath::Abs(Steering)>KINDA_SMALL_NUMBER)
        AddActorWorldRotation(FRotator(0,Steering*65.f*DeltaSeconds,0));
}

bool AAnomaliaVehiclePawn::SetDriverControlsOnServer(AController* Driver,float Throttle,float Steering,float Brake)
{
    if(!HasAuthority() || !IsValid(Driver) || Driver!=GetController() || Driver->GetPawn()!=this ||
       !Driver->IsPlayerController() || !FMath::IsFinite(Throttle) || !FMath::IsFinite(Steering) || !FMath::IsFinite(Brake)) return false;
    ServerSetTransportControls_Implementation(Throttle,Steering,0,0,0,Brake);
    return true;
}

bool AAnomaliaVehiclePawn::ExitDriverOnServer(AController* Driver)
{
    if(!HasAuthority() || !IsValid(Driver) || Driver!=GetController() || Driver->GetPawn()!=this) return false;
    ServerExitVehicle_Implementation();
    return Driver->GetPawn()!=this;
}

float AAnomaliaVehiclePawn::GetExpectedSupportFloorZ() const
{
    return GetActorLocation().Z-Collision->GetScaledSphereRadius();
}
