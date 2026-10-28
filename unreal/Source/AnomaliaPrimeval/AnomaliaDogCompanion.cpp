#include "AnomaliaDogCompanion.h"
#include "AnomaliaSurvivor.h"
#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "Net/UnrealNetwork.h"

AAnomaliaDogCompanion::AAnomaliaDogCompanion()
{
    PrimaryActorTick.bCanEverTick=true;
    bReplicates=true;SetReplicateMovement(true);
    GetCapsuleComponent()->InitCapsuleSize(24.f,45.f);
    GetMesh()->SetRelativeLocation(FVector(0,0,-45));
    GetMesh()->SetRelativeRotation(FRotator(0,-90,0));
    GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    auto* Move=GetCharacterMovement();Move->bRunPhysicsWithNoController=true;
    Move->bOrientRotationToMovement=true;Move->RotationRate=FRotator(0,480,0);
    Move->MaxWalkSpeed=650;Move->MaxStepHeight=25;
    bUseControllerRotationYaw=false;
}
bool AAnomaliaDogCompanion::LoadBreed()
{
    auto* Body=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/German_Shepherd_3D_Model/Models/SK_GermanShepherd_01.SK_GermanShepherd_01"));
    Idle=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/German_Shepherd_3D_Model/Animations/A_type1_Idle_Playing_v01.A_type1_Idle_Playing_v01"));
    Walk=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/German_Shepherd_3D_Model/Animations/A_type1_Walk_Loop_v01.A_type1_Walk_Loop_v01"));
    Run=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/German_Shepherd_3D_Model/Animations/A_type1_Run_Loop_v01.A_type1_Run_Loop_v01"));
    if(!Body||!Idle||!Walk||!Run||Idle->GetSkeleton()!=Body->GetSkeleton()||Walk->GetSkeleton()!=Body->GetSkeleton()||Run->GetSkeleton()!=Body->GetSkeleton())
    {Status=TEXT("Modèle ou animations du chien indisponibles");return false;}
    GetMesh()->SetSkeletalMesh(Body);
    // Normalize the imported dog mesh to a believable adult shepherd silhouette.
    // The collision capsule stays in centimetres; this only corrects the visual mesh scale.
    const FBoxSphereBounds BodyBounds=Body->GetBounds();
    const float ImportedHeight=BodyBounds.BoxExtent.Z*2.f;
    const float TargetHeightCm=90.f;
    const float VisualScale=ImportedHeight>1.f?FMath::Clamp(TargetHeightCm/ImportedHeight,.8f,2.5f):1.f;
    GetMesh()->SetRelativeScale3D(FVector(VisualScale));
    const float CapsuleHalfHeight=GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight();
    const float MeshBottom=BodyBounds.Origin.Z-BodyBounds.BoxExtent.Z;
    GetMesh()->SetRelativeLocation(FVector(0,0,-CapsuleHalfHeight-MeshBottom*VisualScale));
    RefreshAnimation();return true;
}
void AAnomaliaDogCompanion::BeginPlay(){Super::BeginPlay();LoadBreed();}
bool AAnomaliaDogCompanion::AssignSurvivor(AAnomaliaSurvivor* Survivor)
{
    if(!HasAuthority()||!IsValid(Survivor)||Survivor->GetWorld()!=GetWorld()||(SurvivorOwner&&SurvivorOwner!=Survivor))return false;
    SurvivorOwner=Survivor;SetOwner(Survivor);OwnerTrail.Reset();bHasOwnerSample=false;
    Command=EAnomaliaDogCommand::Stay;ForceNetUpdate();return true;
}
bool AAnomaliaDogCompanion::IsCommandAvailable(EAnomaliaDogCommand Value) const
{return Value==EAnomaliaDogCommand::Follow||Value==EAnomaliaDogCommand::Stay;}
bool AAnomaliaDogCompanion::IssueCommand(EAnomaliaDogCommand Value)
{
    if(!HasAuthority()||!IsValid(SurvivorOwner)||!SurvivorOwner->GetController()||SurvivorOwner->GetController()->GetPawn()!=SurvivorOwner||
       GetOwner()!=SurvivorOwner||SurvivorOwner->Health<=0||GetDistanceTo(SurvivorOwner)>1500||!GetWorld())return false;
    if(!IsCommandAvailable(Value)){Status=TEXT("Animation de cet ordre non disponible");return false;}
    const double Now=GetWorld()->GetRealTimeSeconds();if(Now<NextCommandTime)return false;NextCommandTime=Now+.2;
    Command=Value;OwnerTrail.Reset();bHasOwnerSample=false;
    if(Value==EAnomaliaDogCommand::Stay)GetCharacterMovement()->StopMovementImmediately();
    Status=Value==EAnomaliaDogCommand::Stay?TEXT("Pas bouger"):TEXT("Suivre");ForceNetUpdate();return true;
}
bool AAnomaliaDogCompanion::RequestCommand(EAnomaliaDogCommand Value)
{
    if(HasAuthority())return IssueCommand(Value);
    if(!HasLocalNetOwner()||!IsCommandAvailable(Value))return false;
    ServerRequestCommand(Value);return true;
}
void AAnomaliaDogCompanion::ServerRequestCommand_Implementation(EAnomaliaDogCommand Value){IssueCommand(Value);}
void AAnomaliaDogCompanion::RefreshAnimation()
{
    if(!GetMesh()->GetSkeletalMeshAsset()||!Idle||!Walk||!Run)return;
    const float Speed=GetVelocity().Size2D();UAnimSequence* Wanted=Speed>300.f?Run.Get():Speed>10.f?Walk.Get():Idle.Get();
    if(Wanted!=CurrentAnimation){CurrentAnimation=Wanted;GetMesh()->PlayAnimation(Wanted,true);}
}
void AAnomaliaDogCompanion::Tick(float Delta)
{
    Super::Tick(Delta);RefreshAnimation();if(!HasAuthority())return;
    if(GetCharacterMovement()->IsMovingOnGround()){LastSafeLocation=GetActorLocation();bHasSafeLocation=true;}
    if(!SurvivorOwner&&bAutoAssignNearestSurvivor&&GetWorld())
    {
        AAnomaliaSurvivor* Nearest=nullptr;float Distance=2000;
        for(TActorIterator<AAnomaliaSurvivor> It(GetWorld());It;++It)
            if(It->GetController()&&It->GetController()->IsPlayerController()&&It->Health>0&&GetDistanceTo(*It)<Distance)
            {Nearest=*It;Distance=GetDistanceTo(*It);}
        if(Nearest)AssignSurvivor(Nearest);
    }
    if(Command!=EAnomaliaDogCommand::Follow||!IsValid(SurvivorOwner)||SurvivorOwner->Health<=0)
    {GetCharacterMovement()->StopMovementImmediately();return;}
    const FVector OwnerLocation=SurvivorOwner->GetActorLocation();
    const float Distance=FVector::Dist2D(GetActorLocation(),OwnerLocation);
    if(!bHasOwnerSample||FVector::Dist2D(LastOwnerSample,OwnerLocation)>35.f)
    {
        OwnerTrail.Add(OwnerLocation);LastOwnerSample=OwnerLocation;bHasOwnerSample=true;
        if(OwnerTrail.Num()>128)OwnerTrail.RemoveAt(0);
    }
    if(Distance<140.f){OwnerTrail.Reset();GetCharacterMovement()->StopMovementImmediately();return;}
    while(OwnerTrail.Num()>1&&FVector::Dist2D(GetActorLocation(),OwnerTrail[0])<60.f)OwnerTrail.RemoveAt(0);
    const FVector Goal=OwnerTrail.Num()?OwnerTrail[0]:OwnerLocation;
    FVector Direction=Goal-GetActorLocation();Direction.Z=0;
    GetCharacterMovement()->MaxWalkSpeed=bInjured?180.f:Distance>500.f?800.f:400.f;
    AddMovementInput(Direction.GetSafeNormal(),1.f,true);
}
float AAnomaliaDogCompanion::TakeDamage(float Damage,const FDamageEvent& Event,AController* EventInstigator,AActor* Causer)
{
    if(!HasAuthority()||!FMath::IsFinite(Damage)||Damage<=0)return 0;
    const float Applied=FMath::Min(Damage,Health-1.f);Health=FMath::Clamp(Health-Damage,1.f,100.f);
    bInjured=Health<=25.f;ForceNetUpdate();return FMath::Max(0.f,Applied);
}
bool AAnomaliaDogCompanion::TreatInjury(float Amount)
{
    if(!HasAuthority()||!FMath::IsFinite(Amount)||Amount<=0||Amount>100)return false;
    Health=FMath::Clamp(Health+Amount,1.f,100.f);bInjured=Health<=25.f;ForceNetUpdate();return true;
}
void AAnomaliaDogCompanion::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(AAnomaliaDogCompanion,SurvivorOwner);
    DOREPLIFETIME(AAnomaliaDogCompanion,Command);DOREPLIFETIME(AAnomaliaDogCompanion,Health);DOREPLIFETIME(AAnomaliaDogCompanion,bInjured);
}


void AAnomaliaDogCompanion::FellOutOfWorld(const UDamageType& DamageType)
{
    // Falling injures the companion instead of using the engine's default actor destruction.
    if(!HasAuthority())return;
    Health=1.f;bInjured=true;Command=EAnomaliaDogCommand::Stay;OwnerTrail.Reset();
    GetCharacterMovement()->StopMovementImmediately();
    if(bHasSafeLocation)TeleportTo(LastSafeLocation,GetActorRotation(),false,false);
    else if(IsValid(SurvivorOwner))TeleportTo(SurvivorOwner->GetActorLocation()+FVector(120,120,80),GetActorRotation(),false,false);
    ForceNetUpdate();
}
