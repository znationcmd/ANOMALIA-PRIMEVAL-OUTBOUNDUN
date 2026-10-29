#include "AnomaliaZPrigimaliaVehiclePanelComponent.h"
#include "../AnomaliaZPrigimaliaSurvivor.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "GameFramework/Pawn.h"
#include "CollisionQueryParams.h"
#include "Net/UnrealNetwork.h"

UAnomaliaZPrigimaliaVehiclePanelComponent::UAnomaliaZPrigimaliaVehiclePanelComponent()
{
    PrimaryComponentTick.bCanEverTick=true;SetIsReplicatedByDefault(true);
    SetMobility(EComponentMobility::Movable);
    BodyInstance.bAutoWeld=false; // Moving panel collision must not become chassis mass/collision.
    SetCollisionEnabled(ECollisionEnabled::NoCollision);SetCollisionObjectType(ECC_GameTraceChannel1);
    SetCollisionResponseToAllChannels(ECR_Ignore);
    SetCollisionResponseToChannel(ECC_Pawn,ECR_Block);SetCollisionResponseToChannel(ECC_Visibility,ECR_Block);
    SetGenerateOverlapEvents(false);SetCanEverAffectNavigation(false);
}
bool UAnomaliaZPrigimaliaVehiclePanelComponent::TryToggle(AAnomaliaZPrigimaliaSurvivor* User)
{
    if(!GetOwner() || !GetOwner()->HasAuthority() || !GetStaticMesh() || bLocked || !IsValid(User) ||
       User->Health<=0.f || !User->GetController() || User->GetController()->GetPawn()!=User ||
       !User->GetController()->IsPlayerController() ||
       FVector::DistSquared(User->GetActorLocation(),Bounds.Origin)>FMath::Square(250.f))return false;
    FVector Eye;FRotator View;User->GetActorEyesViewPoint(Eye,View);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaZPrigimaliaPanelInteraction),true);Query.AddIgnoredActor(User);FHitResult Hit;
    if(!GetWorld()->LineTraceSingleByChannel(Hit,Eye,Eye+User->GetControlRotation().Vector()*300.f,ECC_Visibility,Query) ||
       Hit.GetComponent()!=this)return false;
    bOpen=!bOpen;bObstructed=false;GetOwner()->ForceNetUpdate();return true;
}
bool UAnomaliaZPrigimaliaVehiclePanelComponent::IsPoseBlocked(float Angle) const
{
    if(!GetStaticMesh() || !GetAttachParent())return true;
    const FTransform Pose(FQuat(LocalHingeAxis.GetSafeNormal(SMALL_NUMBER,FVector::UpVector),FMath::DegreesToRadians(Angle)),GetRelativeLocation(),GetRelativeScale3D());
    const FTransform WorldPose=Pose*GetAttachParent()->GetComponentTransform();
    const auto Local=GetStaticMesh()->GetBounds();
    FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaZPrigimaliaPanelObstruction),false);Query.AddIgnoredActor(GetOwner());
    return GetWorld()->OverlapBlockingTestByChannel(WorldPose.TransformPosition(Local.Origin),WorldPose.GetRotation(),
        ECC_Pawn,FCollisionShape::MakeBox(Local.BoxExtent*WorldPose.GetScale3D().GetAbs()),Query);
}
bool UAnomaliaZPrigimaliaVehiclePanelComponent::TryToggleFromDriver(AController* Driver)
{
    const auto* Vehicle=Cast<APawn>(GetOwner());
    if(!Vehicle || !Vehicle->HasAuthority() || !GetStaticMesh() || bLocked || !IsValid(Driver) ||
       !Driver->IsPlayerController() || Driver->GetPawn()!=Vehicle || Vehicle->GetController()!=Driver)return false;
    bOpen=!bOpen;bObstructed=false;GetOwner()->ForceNetUpdate();return true;
}
void UAnomaliaZPrigimaliaVehiclePanelComponent::TickComponent(float Delta,ELevelTick Type,FActorComponentTickFunction* Function)
{
    Super::TickComponent(Delta,Type,Function);if(!GetStaticMesh() || !GetOwner())return;
    if(GetOwner()->HasAuthority())
    {
        const float Next=FMath::FInterpConstantTo(AngleDegrees,bOpen?FMath::Clamp(OpenAngleDegrees,-170.f,170.f):0.f,
            Delta,FMath::Clamp(DegreesPerSecond,1.f,180.f));
        const int32 Steps=FMath::Max(1,FMath::CeilToInt(FMath::Abs(Next-AngleDegrees)/2.f));
        const float Start=AngleDegrees;bObstructed=false;
        for(int32 Step=1;Step<=Steps;++Step)
        {
            const float Pose=FMath::Lerp(Start,Next,float(Step)/Steps);
            if(FMath::IsNearlyEqual(Pose,AngleDegrees))continue;
            if(IsPoseBlocked(Pose)){bObstructed=true;break;}
            AngleDegrees=Pose;
        }
        VisualAngle=AngleDegrees;
    }
    else VisualAngle=FMath::FInterpConstantTo(VisualAngle,AngleDegrees,Delta,FMath::Max(1.f,DegreesPerSecond)*1.5f);
    SetRelativeRotation(FQuat(LocalHingeAxis.GetSafeNormal(SMALL_NUMBER,FVector::UpVector),FMath::DegreesToRadians(VisualAngle)));
}
void UAnomaliaZPrigimaliaVehiclePanelComponent::OnRep_Angle()
{
    if(!bReceivedAngle){VisualAngle=AngleDegrees;SetRelativeRotation(FQuat(LocalHingeAxis.GetSafeNormal(SMALL_NUMBER,FVector::UpVector),FMath::DegreesToRadians(VisualAngle)));bReceivedAngle=true;}
}
void UAnomaliaZPrigimaliaVehiclePanelComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UAnomaliaZPrigimaliaVehiclePanelComponent,bOpen);DOREPLIFETIME(UAnomaliaZPrigimaliaVehiclePanelComponent,bLocked);
    DOREPLIFETIME(UAnomaliaZPrigimaliaVehiclePanelComponent,bObstructed);DOREPLIFETIME(UAnomaliaZPrigimaliaVehiclePanelComponent,AngleDegrees);
}
