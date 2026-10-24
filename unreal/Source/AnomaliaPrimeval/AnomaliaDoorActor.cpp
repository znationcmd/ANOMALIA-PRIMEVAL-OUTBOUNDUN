#include "AnomaliaDoorActor.h"
#include "AnomaliaSurvivor.h"
#include "Components/SceneComponent.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "Net/UnrealNetwork.h"

AAnomaliaDoorActor::AAnomaliaDoorActor()
{
    bReplicates=true;
    PrimaryActorTick.bCanEverTick=true;
    PrimaryActorTick.bStartWithTickEnabled=false;
    Hinge=CreateDefaultSubobject<USceneComponent>(TEXT("Hinge"));RootComponent=Hinge;
    Hinge->SetMobility(EComponentMobility::Movable);
    LeafCollision=CreateDefaultSubobject<UBoxComponent>(TEXT("LeafCollision"));
    LeafCollision->SetupAttachment(Hinge);LeafCollision->SetMobility(EComponentMobility::Movable);
    LeafCollision->SetCollisionProfileName(TEXT("BlockAllDynamic"));
    LeafCollision->SetBoxExtent(FVector(WidthCm/2,ThicknessCm/2,HeightCm/2));
    LeafCollision->SetRelativeLocation(FVector(WidthCm/2,0,HeightCm/2));
    LeafMesh=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("LeafMesh"));
    LeafMesh->SetupAttachment(LeafCollision);LeafMesh->SetMobility(EComponentMobility::Movable);
    LeafMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void AAnomaliaDoorActor::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    WidthCm=FMath::Clamp(WidthCm,40.f,400.f);HeightCm=FMath::Clamp(HeightCm,100.f,500.f);
    ThicknessCm=FMath::Clamp(ThicknessCm,2.f,30.f);
    OpenAngleDegrees=FMath::Clamp(OpenAngleDegrees,-170.f,170.f);
    DegreesPerSecond=FMath::Clamp(DegreesPerSecond,10.f,180.f);
    LeafCollision->SetBoxExtent(FVector(WidthCm/2,ThicknessCm/2,HeightCm/2));
    LeafCollision->SetRelativeLocation(FVector(WidthCm/2,0,HeightCm/2));OnRep_Door();
}

void AAnomaliaDoorActor::OnRep_Door()
{
    // Replicated leaf angle also restores the correct pose for late join/streaming.
    LeafCollision->SetRelativeRotation(FRotator(0,DoorAngleDegrees,0));
    // Rotation must occur about the hinge, rather than about the centre of the leaf.
    LeafCollision->SetRelativeLocation(FRotator(0,DoorAngleDegrees,0).RotateVector(FVector(WidthCm/2,0,HeightCm/2)));
}

bool AAnomaliaDoorActor::SetLockedOnServer(bool bNewLocked)
{
    if(!HasAuthority())return false;
    bLocked=bNewLocked;ForceNetUpdate();return true;
}

bool AAnomaliaDoorActor::TryToggle(AAnomaliaSurvivor* User)
{
    if(!HasAuthority() || !IsValid(User) || User->GetWorld()!=GetWorld() ||
       !User->GetController() || User->Health<=0 || User->bSleeping || bLocked)return false;
    const FVector Handle=LeafCollision->GetComponentTransform().TransformPosition(FVector(WidthCm*.35,0,0));
    if(FVector::DistSquared(User->GetActorLocation(),Handle)>FMath::Square(250.f))return false;
    FVector Eye;FRotator View;User->GetActorEyesViewPoint(Eye,View);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaDoorInteract),true);
    Query.AddIgnoredActor(User);Query.AddIgnoredActor(this);
    FHitResult Hit;
    if(GetWorld()->LineTraceSingleByChannel(Hit,Eye,Handle,ECC_Visibility,Query))return false;
    bTargetOpen=!bTargetOpen;bObstructed=false;SetActorTickEnabled(true);ForceNetUpdate();return true;
}

bool AAnomaliaDoorActor::IsPoseBlocked(float Angle) const
{
    const FTransform Parent=Hinge->GetComponentTransform();
    const FQuat Turn=FRotator(0,Angle,0).Quaternion();
    const FVector Centre=Parent.TransformPosition(Turn.RotateVector(FVector(WidthCm/2,0,HeightCm/2)));
    const FVector Extent=FVector(WidthCm/2,ThicknessCm/2,HeightCm/2)*Parent.GetScale3D().GetAbs();
    FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaDoorClearance),false);
    Query.AddIgnoredActor(this);
    return GetWorld()->OverlapBlockingTestByChannel(Centre,Parent.GetRotation()*Turn,ECC_Pawn,
        FCollisionShape::MakeBox(Extent),Query);
}

void AAnomaliaDoorActor::Tick(float Dt)
{
    Super::Tick(Dt);
    if(!HasAuthority() || !FMath::IsFinite(Dt) || Dt<=0)return;
    const float Target=bTargetOpen?OpenAngleDegrees:0.f;
    const float Next=FMath::FInterpConstantTo(DoorAngleDegrees,Target,FMath::Min(Dt,.1f),DegreesPerSecond);
    const int32 Steps=FMath::Max(1,FMath::CeilToInt(FMath::Abs(Next-DoorAngleDegrees)/2.f));
    for(int32 Index=1;Index<=Steps;++Index)
        if(IsPoseBlocked(FMath::Lerp(DoorAngleDegrees,Next,float(Index)/Steps)))
        {bObstructed=true;SetActorTickEnabled(false);ForceNetUpdate();return;}
    DoorAngleDegrees=Next;OnRep_Door();ForceNetUpdate();
    if(FMath::IsNearlyEqual(DoorAngleDegrees,Target,.01f))SetActorTickEnabled(false);
}

void AAnomaliaDoorActor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaDoorActor,bLocked);DOREPLIFETIME(AAnomaliaDoorActor,bTargetOpen);
    DOREPLIFETIME(AAnomaliaDoorActor,DoorAngleDegrees);DOREPLIFETIME(AAnomaliaDoorActor,bObstructed);
}
