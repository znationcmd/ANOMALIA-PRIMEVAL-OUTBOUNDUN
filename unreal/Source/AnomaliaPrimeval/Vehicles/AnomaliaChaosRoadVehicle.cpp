#include "AnomaliaChaosRoadVehicle.h"
#include "AnomaliaTransportMovement.h"
#include "ChaosWheeledVehicleMovementComponent.h"
#include "VehicleAnimationInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "GameFramework/FloatingPawnMovement.h"

UAnomaliaRoadFrontWheel::UAnomaliaRoadFrontWheel()
{
    WheelRadius=40.f; WheelWidth=28.f; WheelMass=20.f;
    bAffectedBySteering=true; bAffectedByEngine=true; bAffectedByBrake=true;
    bAffectedByHandbrake=false; MaxSteerAngle=35.f;
    SpringRate=25000.f; SpringPreload=50.f;
    SuspensionDampingRatio=.6f; SuspensionMaxRaise=20.f; SuspensionMaxDrop=20.f;
    RollbarScaling=.15f; FrictionForceMultiplier=2.f;
    MaxBrakeTorque=4000.f; MaxHandBrakeTorque=6000.f;
}

UAnomaliaRoadRearWheel::UAnomaliaRoadRearWheel()
{
    bAffectedBySteering=false; MaxSteerAngle=0.f; bAffectedByHandbrake=true;
}

AAnomaliaChaosRoadVehicle::AAnomaliaChaosRoadVehicle()
{
    Chassis=CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("ChaosChassis"));
    SetRootComponent(Chassis);
    Collision->SetupAttachment(Chassis);
    Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Body->SetVisibility(false); Body->SetHiddenInGame(true);
    Chassis->SetCollisionProfileName(TEXT("Vehicle"));
    Chassis->SetSimulatePhysics(false); // A validated Physics Asset must exist first.
    Chassis->SetIsReplicated(true);
    Movement->SetAutoActivate(false); Movement->PrimaryComponentTick.bStartWithTickEnabled=false;
    Movement->SetUpdatedComponent(nullptr);
    TransportMovement->SetAutoActivate(false); TransportMovement->PrimaryComponentTick.bStartWithTickEnabled=false;
    ChaosMovement=CreateDefaultSubobject<UChaosWheeledVehicleMovementComponent>(TEXT("ChaosRoadMovement"));
    ChaosMovement->SetUpdatedComponent(Chassis);
    ChaosMovement->SetIsReplicated(true);
    // Server feeds every input through the existing validated driver flow.
    // Driverless physics must still receive its parking brake after unpossession.
    ChaosMovement->SetRequiresControllerForInputs(false);
    ChaosMovement->Mass=1500.f;
    ChaosMovement->bReverseAsBrake=false;
    ChaosMovement->EngineSetup.MaxTorque=500.f;
    ChaosMovement->EngineSetup.MaxRPM=6500.f;
    ChaosMovement->EngineSetup.EngineIdleRPM=800.f;
    auto* Torque=ChaosMovement->EngineSetup.TorqueCurve.GetRichCurve();
    Torque->AddKey(0.f,.2f); Torque->AddKey(1000.f,.55f); Torque->AddKey(2500.f,.9f);
    Torque->AddKey(4000.f,1.f); Torque->AddKey(6000.f,.75f); Torque->AddKey(6500.f,.65f);
    auto& Gears=ChaosMovement->TransmissionSetup;
    Gears.bUseAutomaticGears=true; Gears.bUseAutoReverse=false;
    Gears.ForwardGearRatios={3.5f,2.2f,1.5f,1.f,.8f}; Gears.ReverseGearRatios={3.3f};
    Gears.FinalRatio=3.5f; Gears.ChangeUpRPM=5500.f; Gears.ChangeDownRPM=1800.f;
    Gears.GearChangeTime=.25f; Gears.TransmissionEfficiency=.94f;
    ChaosMovement->DifferentialSetup.DifferentialType=EVehicleDifferential::AllWheelDrive;
    ChaosMovement->DifferentialSetup.FrontRearSplit=.5f;
    auto* SteeringCurve=ChaosMovement->SteeringSetup.SteeringCurve.GetRichCurve();
    SteeringCurve->Reset(); // Chaos's steering curve speed axis is MPH.
    SteeringCurve->AddKey(0.f,1.f); SteeringCurve->AddKey(30.f,.7f);
    SteeringCurve->AddKey(60.f,.4f); SteeringCurve->AddKey(100.f,.25f);
}

bool AAnomaliaChaosRoadVehicle::HasValidRoadRig() const
{
    if(!RoadMesh || !RoadMesh->GetPhysicsAsset() || !RoadAnimation ||
       !RoadAnimation->IsChildOf(UVehicleAnimationInstance::StaticClass()) || WheelBones.Num()!=4 ||
       !FMath::IsFinite(WheelRadiusCm) || WheelRadiusCm<10.f || WheelRadiusCm>100.f) return false;
    TSet<FName> Unique;
    for(const FName Bone:WheelBones)
    {
        if(Bone.IsNone() || Unique.Contains(Bone) || RoadMesh->GetRefSkeleton().FindBoneIndex(Bone)==INDEX_NONE) return false;
        Unique.Add(Bone);
    }
    return true;
}

void AAnomaliaChaosRoadVehicle::ApplyRoadRig()
{
    Movement->SetComponentTickEnabled(false); Movement->SetUpdatedComponent(nullptr);
    TransportMovement->SetComponentTickEnabled(false);
    Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Body->SetVisibility(false); Body->SetHiddenInGame(true);
    Chassis->SetSkeletalMesh(RoadMesh);
    Chassis->SetAnimInstanceClass(RoadAnimation);
    ChaosMovement->WheelSetups.Reset();
    if(!HasValidRoadRig()) { Chassis->SetSimulatePhysics(false); return; }
    for(int32 Index=0;Index<4;++Index)
    {
        FChaosWheelSetup Setup;
        Setup.BoneName=WheelBones[Index];
        Setup.WheelClass=Index<2?UAnomaliaRoadFrontWheel::StaticClass():UAnomaliaRoadRearWheel::StaticClass();
        ChaosMovement->WheelSetups.Add(Setup);
    }
    ChaosMovement->SetUpdatedComponent(Chassis);
    if(GetWorld() && GetWorld()->IsGameWorld())
    {
        Chassis->SetSimulatePhysics(HasAuthority());
        Chassis->SetMassOverrideInKg(NAME_None,ChaosMovement->Mass,true);
        ChaosMovement->SetComponentTickEnabled(HasAuthority());
        ChaosMovement->RecreatePhysicsState();
        for(int32 Index=0;Index<ChaosMovement->Wheels.Num();++Index)
            ChaosMovement->SetWheelRadius(Index,WheelRadiusCm);
        // This pawn deliberately preserves ANOMALIA's existing crew/fuel base.
        // Bind the vehicle animation interface explicitly instead of relying on a template pawn cast.
        if(auto* Animation=Cast<UVehicleAnimationInstance>(Chassis->GetAnimInstance()))
            Animation->SetWheeledVehicleComponent(ChaosMovement);
    }
}

void AAnomaliaChaosRoadVehicle::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform); ApplyRoadRig();
}
void AAnomaliaChaosRoadVehicle::BeginPlay()
{
    Super::BeginPlay(); ApplyRoadRig();
}
UPawnMovementComponent* AAnomaliaChaosRoadVehicle::GetMovementComponent() const { return ChaosMovement; }
bool AAnomaliaChaosRoadVehicle::ConfigureVehicle(FName NewVehicleId)
{
    FAnomaliaVehicleDefinition Definition;
    if(!UAnomaliaVehicleCatalog::FindVehicleDefinition(NewVehicleId,Definition) || Definition.Domain!=EAnomaliaVehicleDomain::Ground) return false;
    return Super::ConfigureVehicle(NewVehicleId);
}
bool AAnomaliaChaosRoadVehicle::IsChaosDriveReady() const { return IsDriveReady(); }
bool AAnomaliaChaosRoadVehicle::IsDriveReady() const
{
    return HasValidRoadRig() && ChaosMovement->HasValidPhysicsState() &&
        ChaosMovement->Wheels.Num()==4 && Chassis->IsSimulatingPhysics();
}
bool AAnomaliaChaosRoadVehicle::CanDriverExitNow() const
{
    return FMath::Abs(ChaosMovement->GetForwardSpeed())<100.f && Chassis->GetPhysicsLinearVelocity().Size()<150.f;
}
float AAnomaliaChaosRoadVehicle::GetExpectedSupportFloorZ() const
{
    return Chassis->Bounds.Origin.Z-Chassis->Bounds.BoxExtent.Z;
}
void AAnomaliaChaosRoadVehicle::SimulateRoadDrive(float DeltaSeconds,float Throttle,float Steering,float Brake,
    bool bPowered,bool bDriverMissing)
{
    if(!HasAuthority() || !IsDriveReady()) return;
    float Demand=bPowered?FMath::Abs(Throttle):0.f;
    const float Speed=ChaosMovement->GetForwardSpeed();
    const int32 DesiredGear=Throttle<-.05f?-1:1;
    if(Demand>.05f && ((DesiredGear<0 && Speed>30.f)||(DesiredGear>0 && Speed<-30.f)))
    { Demand=0.f; Brake=1.f; }
    else if(Demand>.05f && FMath::Abs(Speed)<30.f &&
       ((DesiredGear<0 && ChaosMovement->GetCurrentGear()>=0)||(DesiredGear>0 && ChaosMovement->GetCurrentGear()<=0)))
        ChaosMovement->SetTargetGear(DesiredGear,true);
    ChaosMovement->SetThrottleInput(Demand);
    ChaosMovement->SetSteeringInput(Steering);
    ChaosMovement->SetBrakeInput(bDriverMissing?1.f:Brake);
    ChaosMovement->SetHandbrakeInput(bDriverMissing);
}
