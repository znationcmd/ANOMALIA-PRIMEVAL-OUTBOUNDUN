#include "AnomaliaTransportMovement.h"
#include "AnomaliaTransportEnvironment.h"
#include "Components/SplineComponent.h"
#include "EngineUtils.h"
#include "Net/UnrealNetwork.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"

using namespace AnomaliaTransport;
UAnomaliaTransportMovement::UAnomaliaTransportMovement()
{
    SetIsReplicatedByDefault(true);
    PrimaryComponentTick.bCanEverTick=false; // Invoked once by the authoritative vehicle pawn.
    bAutoRegisterUpdatedComponent=false;
}
void UAnomaliaTransportMovement::Configure(const FAnomaliaVehicleDefinition& D,float Multiplier)
{
    bTransport=D.Domain!=EAnomaliaVehicleDomain::Ground;
    Kind=Mode::Surface;
    if(D.Domain==EAnomaliaVehicleDomain::Air)
        Kind=(D.Id==TEXT("attack_helicopter")||D.Id==TEXT("transport_helicopter"))?Mode::Helicopter:Mode::Plane;
    else if(D.Domain==EAnomaliaVehicleDomain::Underwater) Kind=Mode::Submarine;
    else if(D.Domain==EAnomaliaVehicleDomain::Rail) Kind=Mode::Rail;
    Parameters.MaxSpeed=FMath::Clamp(D.MaxSpeedKmh*Multiplier*100000.0/3600.0,100.0,60000.0);
    Parameters.Acceleration=Kind==Mode::Plane?2500:Kind==Mode::Helicopter?1100:Kind==Mode::Rail?180:350;
    Parameters.Drag=Kind==Mode::Plane?0.045:0.18;
    // A carrier accelerates and turns much more slowly than a jetski.
    if(D.Id==TEXT("carrier")||D.Id==TEXT("warship")) Parameters.Acceleration=45;
    if(Kind==Mode::Surface) Parameters.Drag=Parameters.Acceleration/Parameters.MaxSpeed;
    Velocity=FVector::ZeroVector;
    RailSpeedCm=0;
}
bool UAnomaliaTransportMovement::AssignTrack(AAnomaliaRailTrack* Route,float DistanceCm)
{
    if(!GetOwner()||!GetOwner()->HasAuthority()||Kind!=Mode::Rail||!IsValid(Route)||!UpdatedComponent||
        !FMath::IsFinite(DistanceCm)||DistanceCm<0||DistanceCm>Route->Track->GetSplineLength()||!Velocity.IsNearlyZero()) return false;
    const FVector Target=Route->Track->GetLocationAtDistanceAlongSpline(DistanceCm,ESplineCoordinateSpace::World);
    if(FVector::DistSquared(Target,UpdatedComponent->GetComponentLocation())>FMath::Square(500.f)) return false;
    // Joining a rail is proximity-gated; do not teleport vehicles through the world.
    FHitResult Hit;
    SafeMoveUpdatedComponent(Target-UpdatedComponent->GetComponentLocation(),
        Route->Track->GetQuaternionAtDistanceAlongSpline(DistanceCm,ESplineCoordinateSpace::World),true,Hit);
    if(Hit.bBlockingHit||!UpdatedComponent->GetComponentLocation().Equals(Target,1.f)) return false;
    Rail=Route; RailDistanceCm=DistanceCm; RailSpeedCm=0; return true;
}
bool UAnomaliaTransportMovement::SampleWater(double& Surface,double& Bottom)
{
    const FVector Position=UpdatedComponent->GetComponentLocation();
    if(Water.IsValid()&&Water->Sample(Position,Surface,Bottom)) return true;
    Water.Reset();
    const double Now=GetWorld()->GetTimeSeconds();
    if(Now<WaterSearchAt) return false;
    WaterSearchAt=Now+0.5;
    for(TActorIterator<AAnomaliaNavigableWater> It(GetWorld());It;++It)
        if(It->Sample(Position,Surface,Bottom)) { Water=*It; return true; }
    return false;
}
void UAnomaliaTransportMovement::Simulate(float DeltaSeconds,Controls Input,bool bPowered)
{
    if(!bTransport||!UpdatedComponent||!GetOwner()||!GetOwner()->HasAuthority()||
        !FMath::IsFinite(DeltaSeconds)||DeltaSeconds<=0) return;
    Input.Sanitize();
    Parameters.StallSpeed=FMath::Clamp(static_cast<double>(StallSpeedCm),100.0,20000.0);
    if(FMath::IsFinite(ThrustAcceleration)&&ThrustAcceleration>0) Parameters.Acceleration=FMath::Min(10000.f,ThrustAcceleration);
    // Bound hitch work and use 60 Hz substeps to keep steering, drag and water springs stable.
    double Remaining=FMath::Min(static_cast<double>(DeltaSeconds),0.25);
    while(Remaining>0.000001)
    {
        const double Dt=FMath::Min(Remaining,1.0/60.0);
        if(Kind==Mode::Rail) StepRail(Dt,Input,bPowered); else Step(Dt,Input,bPowered);
        Remaining-=Dt;
    }
    UpdateComponentVelocity();
}
void UAnomaliaTransportMovement::Step(double Dt,Controls Input,bool bPowered)
{
    FRotator Rotation=UpdatedComponent->GetComponentRotation();
    const bool Air=Kind==Mode::Plane||Kind==Mode::Helicopter;
    double Surface=0,Bottom=0;
    const bool InWater=!Air&&SampleWater(Surface,Bottom);
    const double Speed=Velocity.Size();
    const double Authority=Kind==Mode::Plane?FMath::Clamp(FVector::DotProduct(Velocity,Rotation.Vector())/Parameters.StallSpeed,0.0,1.0):
        Kind==Mode::Helicopter?(bPowered?1.0:0.0):InWater?FMath::Clamp(Speed/300.0,0.0,1.0):0.0;
    const double Turn=Kind==Mode::Helicopter?60:Kind==Mode::Plane?18:Parameters.Acceleration<=45?3:24;
    Rotation.Yaw+=Input.Yaw*Turn*Authority*Dt;
    if(Air)
    {
        Rotation.Pitch=FMath::Clamp(Rotation.Pitch+Input.Pitch*35*Authority*Dt,-80.0,80.0);
        Rotation.Roll=FRotator::NormalizeAxis(Rotation.Roll+Input.Roll*55*Authority*Dt);
        // Banking turns fixed-wing aircraft even without rudder input.
        if(Kind==Mode::Plane) Rotation.Yaw+=FMath::Sin(FMath::DegreesToRadians(Rotation.Roll))*25*Authority*Dt;
    }
    else if(Kind==Mode::Submarine)
        Rotation.Pitch=FMath::Lerp(Rotation.Pitch,Input.Vertical*15.0,FMath::Clamp(Dt*1.5,0.0,1.0));
    else { Rotation.Pitch=0; Rotation.Roll=0; }
    const FVector F=Rotation.Vector(), U=Rotation.RotateVector(FVector::UpVector);
    const Vector A=Acceleration(Kind,{Velocity.X,Velocity.Y,Velocity.Z},{F.X,F.Y,F.Z},{U.X,U.Y,U.Z},
        Input,Parameters,bPowered,InWater,Surface+WaterlineOffsetCm-UpdatedComponent->GetComponentLocation().Z);
    const Vector Next=Integrate({Velocity.X,Velocity.Y,Velocity.Z},A,Dt,Parameters.MaxSpeed);
    Velocity=FVector(Next.X,Next.Y,Next.Z);
    FVector Delta=Velocity*Dt;
    if(InWater&&Kind==Mode::Submarine)
    {
        const double Target=FMath::Clamp(UpdatedComponent->GetComponentLocation().Z+Delta.Z,Bottom+100,Surface-50);
        Delta.Z=Target-UpdatedComponent->GetComponentLocation().Z;
        if(!FMath::IsNearlyEqual(Delta.Z,Velocity.Z*Dt,0.001)) Velocity.Z=0;
    }
    FHitResult Hit;
    SafeMoveUpdatedComponent(Delta,Rotation.Quaternion(),true,Hit);
    if(Hit.IsValidBlockingHit())
    {
        HandleImpact(Hit,Dt,Delta);
        Velocity=FVector::VectorPlaneProject(Velocity,Hit.Normal);
        SlideAlongSurface(Delta,1-Hit.Time,Hit.Normal,Hit,true);
    }
}
void UAnomaliaTransportMovement::StepRail(double Dt,Controls Input,bool bPowered)
{
    if(!Rail.IsValid()) { Velocity=FVector::ZeroVector; RailSpeedCm=0; return; }
    USplineComponent* Spline=Rail->Track;
    if(Spline->GetSplineLength()<=0) { Velocity=FVector::ZeroVector; RailSpeedCm=0; return; }
    const double Previous=RailDistanceCm;
    RailSpeedCm=AnomaliaTransport::RailSpeed(RailSpeedCm,Input,Parameters,bPowered,Dt);
    bool AtEnd=false;
    const double Next=AnomaliaTransport::RailDistance(Previous,RailSpeedCm*Dt,Spline->GetSplineLength(),Spline->IsClosedLoop(),AtEnd);
    const FTransform Target=Spline->GetTransformAtDistanceAlongSpline(Next,ESplineCoordinateSpace::World,false);
    const FVector Start=UpdatedComponent->GetComponentLocation();
    FHitResult Hit;
    SafeMoveUpdatedComponent(Target.GetLocation()-Start,Target.GetRotation(),true,Hit);
    if(Hit.bBlockingHit)
    {
        // Stop at an obstruction, never slide a locomotive off its rail or teleport through it.
        bool UnusedEnd=false;
        RailDistanceCm=AnomaliaTransport::RailDistance(Previous,RailSpeedCm*Dt*Hit.Time,Spline->GetSplineLength(),Spline->IsClosedLoop(),UnusedEnd);
        RailSpeedCm=0; Velocity=FVector::ZeroVector;
    }
    else
    {
        RailDistanceCm=Next;
        Velocity=(UpdatedComponent->GetComponentLocation()-Start)/Dt;
        if(AtEnd) { RailSpeedCm=0; Velocity=FVector::ZeroVector; }
    }
}

void UAnomaliaTransportMovement::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UAnomaliaTransportMovement,RailDistanceCm);
    DOREPLIFETIME(UAnomaliaTransportMovement,RailSpeedCm);
}
