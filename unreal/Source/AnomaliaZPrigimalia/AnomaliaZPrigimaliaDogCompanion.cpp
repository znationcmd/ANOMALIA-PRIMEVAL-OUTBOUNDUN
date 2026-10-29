#include "AnomaliaZPrigimaliaDogCompanion.h"
#include "AnomaliaZPrigimaliaSurvivor.h"
#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "Net/UnrealNetwork.h"

AAnomaliaZPrigimaliaDogCompanion::AAnomaliaZPrigimaliaDogCompanion()
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
bool AAnomaliaZPrigimaliaDogCompanion::LoadBreed()
{
    auto* Body=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/German_Shepherd_3D_Model/Models/SK_GermanShepherd_01.SK_GermanShepherd_01"));
    Idle=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/German_Shepherd_3D_Model/Animations/A_type1_Idle_Playing_v01.A_type1_Idle_Playing_v01"));
    Walk=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/German_Shepherd_3D_Model/Animations/A_type1_Walk_Loop_v01.A_type1_Walk_Loop_v01"));
    Run=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/German_Shepherd_3D_Model/Animations/A_type1_Run_Loop_v01.A_type1_Run_Loop_v01"));
    if(!Body||!Idle||!Walk||!Run||Idle->GetSkeleton()!=Body->GetSkeleton()||Walk->GetSkeleton()!=Body->GetSkeleton()||Run->GetSkeleton()!=Body->GetSkeleton())
    {Status=TEXT("Modèle ou animations du chien indisponibles");return false;}
    GetMesh()->SetSkeletalMesh(Body);RefreshAnimation();return true;
}
void AAnomaliaZPrigimaliaDogCompanion::BeginPlay(){Super::BeginPlay();LoadBreed();}
bool AAnomaliaZPrigimaliaDogCompanion::AssignSurvivor(AAnomaliaZPrigimaliaSurvivor* Survivor)
{
    if(!HasAuthority()||!IsValid(Survivor)||Survivor->GetWorld()!=GetWorld()||(SurvivorOwner&&SurvivorOwner!=Survivor))return false;
    SurvivorOwner=Survivor;SetOwner(Survivor);OwnerTrail.Reset();bHasOwnerSample=false;
    Command=EAnomaliaZPrigimaliaDogCommand::Stay;ForceNetUpdate();return true;
}
bool AAnomaliaZPrigimaliaDogCompanion::IsCommandAvailable(EAnomaliaZPrigimaliaDogCommand Value) const
{return Value==EAnomaliaZPrigimaliaDogCommand::Follow||Value==EAnomaliaZPrigimaliaDogCommand::Stay;}
bool AAnomaliaZPrigimaliaDogCompanion::IssueCommand(EAnomaliaZPrigimaliaDogCommand Value)
{
    if(!HasAuthority()||!IsValid(SurvivorOwner)||!SurvivorOwner->GetController()||SurvivorOwner->GetController()->GetPawn()!=SurvivorOwner||
       GetOwner()!=SurvivorOwner||SurvivorOwner->Health<=0||GetDistanceTo(SurvivorOwner)>1500||!GetWorld())return false;
    if(!IsCommandAvailable(Value)){Status=TEXT("Animation de cet ordre non disponible");return false;}
    const double Now=GetWorld()->GetRealTimeSeconds();if(Now<NextCommandTime)return false;NextCommandTime=Now+.2;
    Command=Value;OwnerTrail.Reset();bHasOwnerSample=false;
    if(Value==EAnomaliaZPrigimaliaDogCommand::Stay)GetCharacterMovement()->StopMovementImmediately();
    Status=Value==EAnomaliaZPrigimaliaDogCommand::Stay?TEXT("Pas bouger"):TEXT("Suivre");ForceNetUpdate();return true;
}
bool AAnomaliaZPrigimaliaDogCompanion::RequestCommand(EAnomaliaZPrigimaliaDogCommand Value)
{
    if(HasAuthority())return IssueCommand(Value);
    if(!HasLocalNetOwner()||!IsCommandAvailable(Value))return false;
    ServerRequestCommand(Value);return true;
}
void AAnomaliaZPrigimaliaDogCompanion::ServerRequestCommand_Implementation(EAnomaliaZPrigimaliaDogCommand Value){IssueCommand(Value);}
void AAnomaliaZPrigimaliaDogCompanion::RefreshAnimation()
{
    if(!GetMesh()->GetSkeletalMeshAsset()||!Idle||!Walk||!Run)return;
    const float Speed=GetVelocity().Size2D();UAnimSequence* Wanted=Speed>300.f?Run.Get():Speed>10.f?Walk.Get():Idle.Get();
    if(Wanted!=CurrentAnimation){CurrentAnimation=Wanted;GetMesh()->PlayAnimation(Wanted,true);}
}
void AAnomaliaZPrigimaliaDogCompanion::Tick(float Delta)
{
    Super::Tick(Delta);RefreshAnimation();if(!HasAuthority())return;
    if(GetCharacterMovement()->IsMovingOnGround()){LastSafeLocation=GetActorLocation();bHasSafeLocation=true;}
    if(!SurvivorOwner&&bAutoAssignNearestSurvivor&&GetWorld())
    {
        AAnomaliaZPrigimaliaSurvivor* Nearest=nullptr;float Distance=2000;
        for(TActorIterator<AAnomaliaZPrigimaliaSurvivor> It(GetWorld());It;++It)
            if(It->GetController()&&It->GetController()->IsPlayerController()&&It->Health>0&&GetDistanceTo(*It)<Distance)
            {Nearest=*It;Distance=GetDistanceTo(*It);}
        if(Nearest)AssignSurvivor(Nearest);
    }
    if(Command!=EAnomaliaZPrigimaliaDogCommand::Follow||!IsValid(SurvivorOwner)||SurvivorOwner->Health<=0)
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
float AAnomaliaZPrigimaliaDogCompanion::TakeDamage(float Damage,const FDamageEvent& Event,AController* EventInstigator,AActor* Causer)
{
    if(!HasAuthority()||!FMath::IsFinite(Damage)||Damage<=0)return 0;
    const float Applied=FMath::Min(Damage,Health-1.f);Health=FMath::Clamp(Health-Damage,1.f,100.f);
    bInjured=Health<=25.f;ForceNetUpdate();return FMath::Max(0.f,Applied);
}
bool AAnomaliaZPrigimaliaDogCompanion::TreatInjury(float Amount)
{
    if(!HasAuthority()||!FMath::IsFinite(Amount)||Amount<=0||Amount>100)return false;
    Health=FMath::Clamp(Health+Amount,1.f,100.f);bInjured=Health<=25.f;ForceNetUpdate();return true;
}
void AAnomaliaZPrigimaliaDogCompanion::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(AAnomaliaZPrigimaliaDogCompanion,SurvivorOwner);
    DOREPLIFETIME(AAnomaliaZPrigimaliaDogCompanion,Command);DOREPLIFETIME(AAnomaliaZPrigimaliaDogCompanion,Health);DOREPLIFETIME(AAnomaliaZPrigimaliaDogCompanion,bInjured);
}


void AAnomaliaZPrigimaliaDogCompanion::FellOutOfWorld(const UDamageType& DamageType)
{
    // Falling injures the companion instead of using the engine's default actor destruction.
    if(!HasAuthority())return;
    Health=1.f;bInjured=true;Command=EAnomaliaZPrigimaliaDogCommand::Stay;OwnerTrail.Reset();
    GetCharacterMovement()->StopMovementImmediately();
    if(bHasSafeLocation)TeleportTo(LastSafeLocation,GetActorRotation(),false,false);
    else if(IsValid(SurvivorOwner))TeleportTo(SurvivorOwner->GetActorLocation()+FVector(120,120,80),GetActorRotation(),false,false);
    ForceNetUpdate();
}
