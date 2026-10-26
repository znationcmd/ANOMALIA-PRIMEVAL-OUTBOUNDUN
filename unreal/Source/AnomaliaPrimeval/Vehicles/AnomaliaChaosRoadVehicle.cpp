#include "AnomaliaChaosRoadVehicle.h"
#include "AnomaliaTransportMovement.h"
#include "AnomaliaVehiclePanelComponent.h"
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
#include "Components/InputComponent.h"
#include "GameFramework/Controller.h"
#include "Net/UnrealNetwork.h"
#include "Components/SpotLightComponent.h"
#include "Components/PointLightComponent.h"
#include "GameFramework/GameStateBase.h"

UAnomaliaRoadFrontWheel::UAnomaliaRoadFrontWheel()
{
    WheelRadius=40.f; WheelWidth=23.3f; WheelMass=20.f;
    bAffectedBySteering=true; bAffectedByEngine=false; bAffectedByBrake=true;
    bAffectedByHandbrake=false; MaxSteerAngle=35.f;
    // Use the native suspension ray: the prior sphere sweep reported contact
    // with almost zero spring load at full droop, masking tire-load coupling.
    SweepShape=ESweepShape::Raycast;
    bABSEnabled=true;
    // UE 5.8.3 converts this property by 100: native stiffness is 45000.
    // Measured on both actual rigs; setting the property to 45000 was unstable.
    SpringRate=450.f; SpringPreload=50.f;
    SuspensionDampingRatio=.6f; SuspensionMaxRaise=12.f; SuspensionMaxDrop=10.f;
    RollbarScaling=.15f; FrictionForceMultiplier=1.f;
    WheelLoadRatio=1.f; bTractionControlEnabled=false;
    MaxBrakeTorque=1800.f; MaxHandBrakeTorque=0.f;
}

UAnomaliaRoadRearWheel::UAnomaliaRoadRearWheel()
{
    bAffectedBySteering=false; MaxSteerAngle=0.f; bAffectedByHandbrake=true;
    bAffectedByEngine=true; MaxBrakeTorque=1000.f; MaxHandBrakeTorque=2200.f;
}

AAnomaliaChaosRoadVehicle::AAnomaliaChaosRoadVehicle()
{
    Chassis=CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("ChaosChassis"));
    SetRootComponent(Chassis);
    DriverDoor=CreateDefaultSubobject<UAnomaliaVehiclePanelComponent>(TEXT("DriverDoor"));DriverDoor->SetupAttachment(Chassis);
    const TCHAR* PanelNames[]={TEXT("RoadPanel1"),TEXT("RoadPanel2"),TEXT("RoadPanel3"),TEXT("RoadPanel4"),TEXT("RoadPanel5")};
    for(const TCHAR* Name:PanelNames)
    {
        auto* Panel=CreateDefaultSubobject<UAnomaliaVehiclePanelComponent>(FName(Name));
        Panel->SetupAttachment(Chassis);AdditionalPanels.Add(Panel);
    }
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
    for(int32 Index=0;Index<2;++Index)
    {
        auto* Light=CreateDefaultSubobject<USpotLightComponent>(Index==0?TEXT("HeadlightLeft"):TEXT("HeadlightRight"));
        Light->SetupAttachment(Chassis);Light->SetRelativeLocation(FVector(230,Index==0?-72:72,65));
        Light->SetRelativeRotation(FRotator(-4,0,0));Light->SetIntensity(50000.f);
        Light->SetAttenuationRadius(6000.f);Light->SetInnerConeAngle(18);Light->SetOuterConeAngle(38);
        Light->SetVisibility(false);Headlights.Add(Light);
    }
    const TCHAR* Signals[]={TEXT("FrontLeftSignal"),TEXT("FrontRightSignal"),TEXT("RearLeftSignal"),TEXT("RearRightSignal")};
    for(int32 Index=0;Index<4;++Index)
    {
        auto* Light=CreateDefaultSubobject<UPointLightComponent>(Signals[Index]);Light->SetupAttachment(Chassis);
        Light->SetRelativeLocation(FVector(Index<2?233:-233,Index%2==0?-85:85,65));
        Light->SetLightColor(FLinearColor(1.f,.25f,.015f));Light->SetIntensity(300.f);
        Light->SetAttenuationRadius(100.f);Light->SetCastShadows(false);Light->SetVisibility(false);IndicatorLights.Add(Light);
    }
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
    ChaosMovement->DragCoefficient=.3f;
    ChaosMovement->ChassisWidth=182.f; ChaosMovement->ChassisHeight=145.f;
    ChaosMovement->DownforceCoefficient=0.f; // Road sedan, no artificial aero grip.
    ChaosMovement->EngineSetup.MaxTorque=320.f;
    ChaosMovement->EngineSetup.MaxRPM=6500.f;
    ChaosMovement->EngineSetup.EngineIdleRPM=800.f;
    auto* Torque=ChaosMovement->EngineSetup.TorqueCurve.GetRichCurve();
    Torque->AddKey(0.f,.2f); Torque->AddKey(1000.f,.55f); Torque->AddKey(2500.f,.9f);
    Torque->AddKey(4000.f,1.f); Torque->AddKey(6000.f,.75f); Torque->AddKey(6500.f,.65f);
    auto& Gears=ChaosMovement->TransmissionSetup;
    Gears.bUseAutomaticGears=true; Gears.bUseAutoReverse=false;
    Gears.ForwardGearRatios={3.5f,2.2f,1.5f,1.f,.8f}; Gears.ReverseGearRatios={3.3f};
    Gears.FinalRatio=3.5f; Gears.ChangeUpRPM=4500.f; Gears.ChangeDownRPM=1800.f;
    Gears.GearChangeTime=.25f; Gears.TransmissionEfficiency=.94f;
    ChaosMovement->DifferentialSetup.DifferentialType=EVehicleDifferential::RearWheelDrive;
    ChaosMovement->SteeringSetup.SteeringType=ESteeringType::Ackermann;
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
    if(AdditionalPanelDefinitions.Num()>AdditionalPanels.Num())return false;
    TSet<FName> PanelIds;PanelIds.Add(TEXT("driver_door"));
    for(const auto& Panel:AdditionalPanelDefinitions)
    {
        if(!Panel.Mesh || Panel.PanelId.IsNone() || PanelIds.Contains(Panel.PanelId) ||
           Panel.PivotCm.ContainsNaN() || Panel.PivotCm.GetAbsMax()>1000.f ||
           Panel.HingeAxis.ContainsNaN() || Panel.HingeAxis.SizeSquared()<SMALL_NUMBER ||
           !FMath::IsFinite(Panel.OpenAngleDegrees) || FMath::Abs(Panel.OpenAngleDegrees)>170.f)return false;
        PanelIds.Add(Panel.PanelId);
    }
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
    DriverDoor->SetStaticMesh(DriverDoorMesh);DriverDoor->SetRelativeLocation(DriverDoorPivotCm);
    DriverDoor->SetVisibility(DriverDoorMesh!=nullptr);DriverDoor->SetHiddenInGame(DriverDoorMesh==nullptr);
    DriverDoor->SetCollisionEnabled(DriverDoorMesh?ECollisionEnabled::QueryAndPhysics:ECollisionEnabled::NoCollision);
    TSet<FName> PanelIds;PanelIds.Add(DriverDoor->PanelId);
    for(int32 Index=0;Index<AdditionalPanels.Num();++Index)
    {
        auto* Panel=AdditionalPanels[Index].Get();
        const auto* Definition=AdditionalPanelDefinitions.IsValidIndex(Index)?&AdditionalPanelDefinitions[Index]:nullptr;
        const bool bValid=Definition && Definition->Mesh && !Definition->PanelId.IsNone() &&
            !PanelIds.Contains(Definition->PanelId) && !Definition->HingeAxis.ContainsNaN() &&
            Definition->HingeAxis.SizeSquared()>SMALL_NUMBER && !Definition->PivotCm.ContainsNaN() &&
            FMath::IsFinite(Definition->OpenAngleDegrees) && FMath::Abs(Definition->OpenAngleDegrees)<=170.f;
        Panel->SetStaticMesh(bValid?Definition->Mesh:nullptr);
        Panel->SetVisibility(bValid);Panel->SetHiddenInGame(!bValid);
        Panel->SetCollisionEnabled(bValid?ECollisionEnabled::QueryAndPhysics:ECollisionEnabled::NoCollision);
        if(bValid)
        {
            PanelIds.Add(Definition->PanelId);Panel->PanelId=Definition->PanelId;
            Panel->SetRelativeLocation(Definition->PivotCm);Panel->LocalHingeAxis=Definition->HingeAxis.GetSafeNormal();
            Panel->OpenAngleDegrees=Definition->OpenAngleDegrees;
        }
    }
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
        FBox ClosedArtBox=RoadBodyMesh->GetBounds().GetBox();
        if(DriverDoorMesh)ClosedArtBox+=DriverDoorMesh->GetBounds().GetBox().ShiftBy(DriverDoorPivotCm);
        for(const auto& Panel:AdditionalPanels)if(Panel && Panel->GetStaticMesh())
            ClosedArtBox+=Panel->GetStaticMesh()->GetBounds().GetBox().ShiftBy(Panel->GetRelativeLocation());
        const FBoxSphereBounds ArtBounds(ClosedArtBox);
        FKBoxElem Shape;
        Shape.X=FMath::Clamp(float(ArtBounds.BoxExtent.X)*1.5f,100.f,1000.f);
        Shape.Y=FMath::Clamp(float(ArtBounds.BoxExtent.Y)*1.5f,60.f,400.f);
        Shape.Z=FMath::Clamp(float(ArtBounds.BoxExtent.Z),20.f,60.f);
        // Keep the underside above the contact patch; wheels carry the vehicle.
        const FTransform RootBind=ReferenceBoneTransform(RootBone);
        // Art bounds are component-space; a Physics Asset shape is bone-space.
        // Cancel the actual root bind rotation instead of assuming identity.
        Shape.Center=RootBind.InverseTransformPosition(FVector(ArtBounds.Origin.X,ArtBounds.Origin.Y,WheelRadiusCm*.5f+Shape.Z*.5f));
        Shape.Rotation=RootBind.InverseTransformRotation(FQuat::Identity).Rotator();
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
    UpdateRoadLights();
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
    for(int32 Index=0;Index<RoadWheels.Num();++Index)
    {
        const auto& Visual=RoadWheels[Index];
        if(!Visual || !Visual->GetStaticMesh())return false;
        const FVector Axle=Visual->GetComponentQuat().RotateVector(TireAxle(Visual->GetStaticMesh()));
        if(FMath::Abs(FVector::DotProduct(Axle,Up))>.1f)return false;
        auto* Wheel=ChaosMovement->Wheels.IsValidIndex(Index)?ChaosMovement->Wheels[Index].Get():nullptr;
        const FQuat Steer=FRotator(0,Wheel?Wheel->GetSteerAngle():0.f,0).Quaternion();
        const FVector Expected=Chassis->GetComponentQuat().RotateVector(Steer.RotateVector(FVector::RightVector));
        // Allow one frame of steering interpolation; reject a 90-degree
        // sideways mounting even when the tire itself is standing upright.
        if(FMath::Abs(FVector::DotProduct(Axle,Expected))<.95f)return false;
    }
    return true;
}

void AAnomaliaChaosRoadVehicle::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    UpdateWheelVisuals();
    UpdateRoadLights();
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
    return true; // Requested gameplay: exiting is allowed at any speed.
}
FVector AAnomaliaChaosRoadVehicle::GetDriverExitVelocity() const { return Chassis->GetPhysicsLinearVelocity(); }
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
    // A stalled or switched-off engine needs an explicit driver restart.
    // Replenishing fuel alone must never restart a parked vehicle.
    if(bDriverMissing || !HasFuel()) SetEngineState(false);
    float Demand=bPowered && bEngineRunning?(bManualGears?FMath::Max(0.f,Throttle):FMath::Abs(Throttle)):0.f;
    if(bManualGears && Throttle<0.f)Brake=FMath::Max(Brake,-Throttle);
    const float Speed=ChaosMovement->GetForwardSpeed();
    const int32 DesiredGear=bManualGears?ChaosMovement->GetTargetGear():(Throttle<-.05f?-1:1);
    if(Demand>.05f && ((DesiredGear<0 && Speed>30.f)||(DesiredGear>0 && Speed<-30.f)))
    { Demand=0.f; Brake=1.f; }
    else if(!bManualGears && Demand>.05f && FMath::Abs(Speed)<30.f &&
       ((DesiredGear<0 && ChaosMovement->GetCurrentGear()>=0)||(DesiredGear>0 && ChaosMovement->GetCurrentGear()<=0)))
        ChaosMovement->SetTargetGear(DesiredGear,true);
    ChaosMovement->SetThrottleInput(Demand);
    ChaosMovement->SetSteeringInput(Steering);
    const bool bPark=bDriverMissing && Chassis->GetPhysicsLinearVelocity().Size()<100.f;
    ChaosMovement->SetBrakeInput(bPark?1.f:Brake);
    ChaosMovement->SetHandbrakeInput(bPark || bHandbrakeHeld);
}

void AAnomaliaChaosRoadVehicle::SetEngineState(bool bRunning)
{
    if(!HasAuthority() || bEngineRunning==bRunning)return;
    bEngineRunning=bRunning; OnRep_EngineRunning(); ForceNetUpdate();
}
bool AAnomaliaChaosRoadVehicle::SetEngineRunningOnServer(AController* Driver,bool bRunning)
{
    if(!HasAuthority() || !IsValid(Driver) || Driver!=GetController() || Driver->GetPawn()!=this ||
       !Driver->IsPlayerController() || (bRunning && (!IsDriveReady() || !HasFuel())))return false;
    SetEngineState(bRunning);return bEngineRunning==bRunning;
}
void AAnomaliaChaosRoadVehicle::OnRep_EngineRunning(){OnEngineRunningChanged(bEngineRunning);}
void AAnomaliaChaosRoadVehicle::InputIgnition()
{
    if(!IsLocallyControlled())return;
    if(HasAuthority())ServerToggleIgnition_Implementation();else ServerToggleIgnition();
}
void AAnomaliaChaosRoadVehicle::ServerToggleIgnition_Implementation()
{
    SetEngineRunningOnServer(GetController(),!bEngineRunning);
}
void AAnomaliaChaosRoadVehicle::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);
    PlayerInputComponent->BindAction(TEXT("VehicleIgnition"),IE_Pressed,this,&AAnomaliaChaosRoadVehicle::InputIgnition);
    PlayerInputComponent->BindAction(TEXT("VehicleGearUp"),IE_Pressed,this,&AAnomaliaChaosRoadVehicle::InputGearUp);
    PlayerInputComponent->BindAction(TEXT("VehicleGearDown"),IE_Pressed,this,&AAnomaliaChaosRoadVehicle::InputGearDown);
    PlayerInputComponent->BindAction(TEXT("VehicleGearMode"),IE_Pressed,this,&AAnomaliaChaosRoadVehicle::InputGearMode);
    PlayerInputComponent->BindAction(TEXT("VehicleHandbrake"),IE_Pressed,this,&AAnomaliaChaosRoadVehicle::InputHandbrakeOn);
    PlayerInputComponent->BindAction(TEXT("VehicleHandbrake"),IE_Released,this,&AAnomaliaChaosRoadVehicle::InputHandbrakeOff);
    PlayerInputComponent->BindAction(TEXT("VehicleHeadlights"),IE_Pressed,this,&AAnomaliaChaosRoadVehicle::InputHeadlights);
    PlayerInputComponent->BindAction(TEXT("VehicleIndicatorLeft"),IE_Pressed,this,&AAnomaliaChaosRoadVehicle::InputIndicatorLeft);
    PlayerInputComponent->BindAction(TEXT("VehicleIndicatorRight"),IE_Pressed,this,&AAnomaliaChaosRoadVehicle::InputIndicatorRight);
    PlayerInputComponent->BindAction(TEXT("VehicleHazards"),IE_Pressed,this,&AAnomaliaChaosRoadVehicle::InputHazardLights);
    PlayerInputComponent->BindAction(TEXT("VehicleDoor"),IE_Pressed,this,&AAnomaliaChaosRoadVehicle::InputDriverDoor);
}
void AAnomaliaChaosRoadVehicle::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaChaosRoadVehicle,bEngineRunning);
    DOREPLIFETIME(AAnomaliaChaosRoadVehicle,bManualGears);
    DOREPLIFETIME(AAnomaliaChaosRoadVehicle,bHandbrakeHeld);
    DOREPLIFETIME(AAnomaliaChaosRoadVehicle,bHeadlightsOn);
    DOREPLIFETIME(AAnomaliaChaosRoadVehicle,IndicatorMode);
}

bool AAnomaliaChaosRoadVehicle::ExecuteRoadActionOnServer(AController* Driver,EAnomaliaRoadAction Action)
{
    if(!HasAuthority() || !IsValid(Driver) || Driver!=GetController() || Driver->GetPawn()!=this || !Driver->IsPlayerController())return false;
    switch(Action)
    {
    case EAnomaliaRoadAction::GearUp:
    case EAnomaliaRoadAction::GearDown:
    {
        if(!IsDriveReady())return false;
        const int32 Gear=ChaosMovement->GetTargetGear()+(Action==EAnomaliaRoadAction::GearUp?1:-1);
        if(Gear< -1 || Gear>ChaosMovement->TransmissionSetup.ForwardGearRatios.Num())return false;
        const float Speed=ChaosMovement->GetForwardSpeed();
        if((Gear<0 && Speed>100.f)||(Gear>0 && Speed< -100.f))return false;
        bManualGears=true;ChaosMovement->SetUseAutomaticGears(false);ChaosMovement->SetTargetGear(Gear,false);break;
    }
    case EAnomaliaRoadAction::ToggleGearMode:
        bManualGears=!bManualGears;ChaosMovement->SetUseAutomaticGears(!bManualGears);break;
    case EAnomaliaRoadAction::HandbrakeOn:bHandbrakeHeld=true;break;
    case EAnomaliaRoadAction::HandbrakeOff:bHandbrakeHeld=false;break;
    case EAnomaliaRoadAction::Headlights:bHeadlightsOn=!bHeadlightsOn;break;
    case EAnomaliaRoadAction::IndicatorLeft:IndicatorMode=IndicatorMode==1?0:1;break;
    case EAnomaliaRoadAction::IndicatorRight:IndicatorMode=IndicatorMode==2?0:2;break;
    case EAnomaliaRoadAction::HazardLights:IndicatorMode=IndicatorMode==3?0:3;break;
    case EAnomaliaRoadAction::DriverDoor:return DriverDoor->TryToggleFromDriver(Driver);
    default:return false;
    }
    OnRep_RoadControls();ForceNetUpdate();return true;
}
void AAnomaliaChaosRoadVehicle::SendRoadAction(EAnomaliaRoadAction Action)
{
    if(!IsLocallyControlled())return;
    if(HasAuthority())ExecuteRoadActionOnServer(GetController(),Action);else ServerRoadAction(Action);
}
void AAnomaliaChaosRoadVehicle::ServerRoadAction_Implementation(EAnomaliaRoadAction Action){ExecuteRoadActionOnServer(GetController(),Action);}
void AAnomaliaChaosRoadVehicle::InputGearUp(){SendRoadAction(EAnomaliaRoadAction::GearUp);}
void AAnomaliaChaosRoadVehicle::InputGearDown(){SendRoadAction(EAnomaliaRoadAction::GearDown);}
void AAnomaliaChaosRoadVehicle::InputGearMode(){SendRoadAction(EAnomaliaRoadAction::ToggleGearMode);}
void AAnomaliaChaosRoadVehicle::InputHandbrakeOn(){SendRoadAction(EAnomaliaRoadAction::HandbrakeOn);}
void AAnomaliaChaosRoadVehicle::InputHandbrakeOff(){SendRoadAction(EAnomaliaRoadAction::HandbrakeOff);}
void AAnomaliaChaosRoadVehicle::InputHeadlights(){SendRoadAction(EAnomaliaRoadAction::Headlights);}
void AAnomaliaChaosRoadVehicle::InputIndicatorLeft(){SendRoadAction(EAnomaliaRoadAction::IndicatorLeft);}
void AAnomaliaChaosRoadVehicle::InputIndicatorRight(){SendRoadAction(EAnomaliaRoadAction::IndicatorRight);}
void AAnomaliaChaosRoadVehicle::InputHazardLights(){SendRoadAction(EAnomaliaRoadAction::HazardLights);}
void AAnomaliaChaosRoadVehicle::InputDriverDoor(){SendRoadAction(EAnomaliaRoadAction::DriverDoor);}
void AAnomaliaChaosRoadVehicle::OnRep_RoadControls(){UpdateRoadLights();}
void AAnomaliaChaosRoadVehicle::UpdateRoadLights()
{
    for(const auto& Light:Headlights)if(Light)Light->SetVisibility(bHeadlightsOn);
    const auto* State=GetWorld()?GetWorld()->GetGameState():nullptr;
    const double Time=State?State->GetServerWorldTimeSeconds():(GetWorld()?GetWorld()->GetTimeSeconds():0);
    const bool bFlash=FMath::Fmod(Time,.8)<.4;
    for(int32 Index=0;Index<IndicatorLights.Num();++Index)
        if(IndicatorLights[Index])IndicatorLights[Index]->SetVisibility(bFlash && (IndicatorMode==3 || IndicatorMode==(Index%2==0?1:2)));
}
