#include "AnomaliaChaosRoadVehicle.h"
#include "AnomaliaTransportMovement.h"
#include "ChaosWheeledVehicleMovementComponent.h"
#include "VehicleAnimationInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "PhysicsEngine/PhysicsAsset.h"
#include "PhysicsEngine/SkeletalBodySetup.h"
#include "PhysicsEngine/AggregateGeom.h"
#include "Engine/World.h"
#include "CollisionQueryParams.h"
#include "GameFramework/FloatingPawnMovement.h"

UAnomaliaRoadFrontWheel::UAnomaliaRoadFrontWheel()
{
    WheelRadius=40.f; WheelWidth=28.f; WheelMass=20.f;
    bAffectedBySteering=true; bAffectedByEngine=true; bAffectedByBrake=true;
    bAffectedByHandbrake=false; MaxSteerAngle=35.f;
    // A finite tire contact sweep avoids intermittent point-ray support at speed.
    SweepShape=ESweepShape::Spherecast;
    bABSEnabled=true;
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
    RoadGlass=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RoadGlass"));RoadGlass->SetupAttachment(Chassis);
    RoadGlass->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    const TCHAR* WheelNames[]={TEXT("RoadWheelFL"),TEXT("RoadWheelFR"),TEXT("RoadWheelRL"),TEXT("RoadWheelRR")};
    for(int32 Index=0;Index<4;++Index)
    {
        auto* Wheel=CreateDefaultSubobject<UStaticMeshComponent>(FName(WheelNames[Index]));
        Wheel->SetupAttachment(Chassis);Wheel->SetCollisionEnabled(ECollisionEnabled::NoCollision);RoadWheels.Add(Wheel);
    }
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
    if(!RoadMesh || !RoadMesh->GetPhysicsAsset() || !RoadBodyMesh || !RoadWheelMesh || !RoadAnimation ||
       !RoadAnimation->IsChildOf(UVehicleAnimationInstance::StaticClass()) || WheelBones.Num()!=4 ||
       !FMath::IsFinite(WheelRadiusCm) || WheelRadiusCm<10.f || WheelRadiusCm>100.f) return false;
    TSet<FName> Unique;
    if(RoadWheelMeshes.Num()!=0 || RoadWheelHubTargetsCm.Num()!=0)
    {
        if(RoadWheelMeshes.Num()!=4 || RoadWheelHubTargetsCm.Num()!=4)return false;
        for(int32 Index=0;Index<4;++Index)
            if(!RoadWheelMeshes[Index] || RoadWheelHubTargetsCm[Index].ContainsNaN() ||
               RoadWheelHubTargetsCm[Index].GetAbsMax()>1000.f)return false;
    }
    for(const FName Bone:WheelBones)
    {
        if(Bone.IsNone() || Unique.Contains(Bone) || RoadMesh->GetRefSkeleton().FindBoneIndex(Bone)==INDEX_NONE) return false;
        Unique.Add(Bone);
    }
    return true;
}

FTransform AAnomaliaChaosRoadVehicle::ReferenceBoneTransform(FName Bone) const
{
    const FReferenceSkeleton& Skeleton=RoadMesh->GetRefSkeleton();
    int32 Index=Skeleton.FindBoneIndex(Bone);
    FTransform Result=FTransform::Identity;
    while(Index!=INDEX_NONE)
    {
        Result=Result*Skeleton.GetRefBonePose()[Index];
        Index=Skeleton.GetParentIndex(Index);
    }
    return Result;
}

void AAnomaliaChaosRoadVehicle::ApplyRoadRig()
{
    Movement->SetComponentTickEnabled(false); Movement->SetUpdatedComponent(nullptr);
    TransportMovement->SetComponentTickEnabled(false);
    Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Body->SetVisibility(false); Body->SetHiddenInGame(true);
    Chassis->SetSkeletalMesh(RoadMesh);
    Chassis->SetAnimInstanceClass(RoadAnimation);
    const bool bAuthoredWheels=RoadWheelMeshes.Num()==4 && RoadWheelHubTargetsCm.Num()==4;
    // Modular original art follows a real animated skeleton, with its vendor
    // suspension geometry hidden. Hidden bones must continue to refresh.
    Chassis->SetVisibility(!bAuthoredWheels,false);
    Chassis->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    Body->SetStaticMesh(RoadBodyMesh);Body->SetRelativeTransform(FTransform::Identity);
    Body->SetVisibility(RoadBodyMesh!=nullptr);Body->SetHiddenInGame(RoadBodyMesh==nullptr);
    RoadGlass->SetStaticMesh(RoadGlassMesh);RoadGlass->SetVisibility(RoadGlassMesh!=nullptr);
    for(int32 Index=0;Index<RoadWheels.Num();++Index)
    {
        RoadWheels[Index]->SetStaticMesh(bAuthoredWheels?RoadWheelMeshes[Index]:RoadWheelMesh);
        if(WheelBones.IsValidIndex(Index))
        {
            // Static wheel art has its own axle convention. Do not inherit the
            // rig bone's bind rotation: that laid the reference tires on their sides.
            RoadWheels[Index]->AttachToComponent(Chassis,FAttachmentTransformRules::SnapToTargetNotIncludingScale);
        }
    }
    ChaosMovement->WheelSetups.Reset();
    if(!HasValidRoadRig()) { Chassis->SetSimulatePhysics(false); return; }
    for(int32 Index=0;Index<4;++Index)
    {
        FChaosWheelSetup Setup;
        Setup.BoneName=WheelBones[Index];
        if(bAuthoredWheels)
            Setup.AdditionalOffset=RoadWheelHubTargetsCm[Index]-ReferenceBoneTransform(WheelBones[Index]).GetTranslation();
        Setup.WheelClass=Index<2?UAnomaliaRoadFrontWheel::StaticClass():UAnomaliaRoadRearWheel::StaticClass();
        ChaosMovement->WheelSetups.Add(Setup);
    }
    ChaosMovement->SetUpdatedComponent(Chassis);
    if(GetWorld() && GetWorld()->IsGameWorld())
    {
        // A road chassis is one rigid body, not the template's articulated
        // suspension ragdoll. Override this component only; keep shared art intact.
        const FName RootBone=RoadMesh->GetRefSkeleton().GetBoneName(0);
        RuntimeChassisPhysics=NewObject<UPhysicsAsset>(this,NAME_None,RF_Transient);
        USkeletalBodySetup* ChassisBody=NewObject<USkeletalBodySetup>(RuntimeChassisPhysics);
        ChassisBody->BoneName=RootBone;
        ChassisBody->PhysicsType=PhysType_Simulated;
        const FBoxSphereBounds ArtBounds=RoadBodyMesh->GetBounds();
        FKBoxElem Shape;
        Shape.X=FMath::Clamp(float(ArtBounds.BoxExtent.X)*1.5f,100.f,1000.f);
        Shape.Y=FMath::Clamp(float(ArtBounds.BoxExtent.Y)*1.5f,60.f,400.f);
        Shape.Z=FMath::Clamp(float(ArtBounds.BoxExtent.Z),20.f,60.f);
        // Keep the underside above the contact patch; wheels carry the vehicle.
        Shape.Center=FVector(ArtBounds.Origin.X,ArtBounds.Origin.Y,WheelRadiusCm*.5f+Shape.Z*.5f);
        ChassisBody->AggGeom.BoxElems.Add(Shape);
        RuntimeChassisPhysics->SkeletalBodySetups.Add(ChassisBody);
        RuntimeChassisPhysics->BoundsBodies.Add(0);
        RuntimeChassisPhysics->BodySetupIndexMap.Add(RootBone,0);
        Chassis->SetPhysicsAsset(RuntimeChassisPhysics,true);
        Chassis->SetSimulatePhysics(HasAuthority());
        Chassis->SetMassOverrideInKg(RootBone,ChaosMovement->Mass,true);
        ChaosMovement->SetComponentTickEnabled(HasAuthority());
        ChaosMovement->RecreatePhysicsState();
        for(int32 Index=0;Index<ChaosMovement->Wheels.Num();++Index)
            ChaosMovement->SetWheelRadius(Index,WheelRadiusCm);
        // This pawn deliberately preserves ANOMALIA's existing crew/fuel base.
        // Bind the vehicle animation interface explicitly instead of relying on a template pawn cast.
        if(auto* Animation=Cast<UVehicleAnimationInstance>(Chassis->GetAnimInstance()))
            Animation->SetWheeledVehicleComponent(ChaosMovement);
    }
    UpdateWheelVisuals();
}

namespace
{
    FVector TireAxle(const UStaticMesh* Mesh)
    {
        const FVector Extent=Mesh->GetBounds().BoxExtent;
        if(Extent.X<Extent.Y && Extent.X<Extent.Z)return FVector::ForwardVector;
        if(Extent.Z<Extent.Y && Extent.Z<Extent.X)return FVector::UpVector;
        return FVector::RightVector;
    }
}

void AAnomaliaChaosRoadVehicle::UpdateWheelVisuals()
{
    if(!HasValidRoadRig())return;
    const bool bAuthored=RoadWheelHubTargetsCm.Num()==4;
    for(int32 Index=0;Index<RoadWheels.Num();++Index)
    {
        UStaticMeshComponent* Visual=RoadWheels[Index];
        if(!Visual || !Visual->GetStaticMesh())continue;
        auto* Wheel=ChaosMovement->Wheels.IsValidIndex(Index)?ChaosMovement->Wheels[Index].Get():nullptr;
        FVector Hub=bAuthored?RoadWheelHubTargetsCm[Index]:ReferenceBoneTransform(WheelBones[Index]).GetTranslation();
        if(Wheel)Hub.Z+=Wheel->GetSuspensionOffset();
        const FQuat ArtToAxle=FQuat::FindBetweenNormals(TireAxle(Visual->GetStaticMesh()),FVector::RightVector);
        // Native Chaos values drive the actual steering, spin and suspension.
        // No extra bind-pose rotation or duplicated authored hub offset is applied.
        const FRotator Motion(Wheel?Wheel->GetRotationAngle():0.f,Wheel?Wheel->GetSteerAngle():0.f,0.f);
        Visual->SetRelativeLocation(Hub);
        Visual->SetRelativeRotation(Motion.Quaternion()*ArtToAxle);
    }
}

bool AAnomaliaChaosRoadVehicle::AreWheelVisualsUpright() const
{
    if(RoadWheels.Num()!=4)return false;
    const FVector Up=Chassis->GetUpVector();
    for(const auto& Visual:RoadWheels)
    {
        if(!Visual || !Visual->GetStaticMesh())return false;
        const FVector Axle=Visual->GetComponentQuat().RotateVector(TireAxle(Visual->GetStaticMesh()));
        if(FMath::Abs(FVector::DotProduct(Axle,Up))>.1f)return false;
    }
    return true;
}

void AAnomaliaChaosRoadVehicle::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    UpdateWheelVisuals();
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
    if(!Super::ConfigureVehicle(NewVehicleId))return false;
    ApplyRoadRig();return true;
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
    // A suspension rig's render bounds can extend well below the support plane.
    // Use the actual floor instead of rejecting every safe exit from that rig.
    if(GetWorld())
    {
        FHitResult Floor;FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaRoadSupport),true);
        Query.AddIgnoredActor(this);
        const FVector Origin=GetActorLocation();
        if(GetWorld()->LineTraceSingleByChannel(Floor,Origin+FVector(0,0,50),Origin-FVector(0,0,600),ECC_Pawn,Query) && Floor.ImpactNormal.Z>.5f)
            return Floor.ImpactPoint.Z;
    }
    return GetActorLocation().Z-WheelRadiusCm;
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
