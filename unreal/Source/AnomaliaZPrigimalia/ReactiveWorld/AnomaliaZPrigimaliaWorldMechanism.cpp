#include "AnomaliaZPrigimaliaWorldMechanism.h"
#include "AnomaliaZPrigimaliaWorldStateSubsystem.h"
#include "../AnomaliaZPrigimaliaSurvivor.h"
#include "../AnomaliaZPrigimaliaDoorActor.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/BoxComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "Engine/StaticMesh.h"
#include "Net/UnrealNetwork.h"

AAnomaliaZPrigimaliaWorldMechanism::AAnomaliaZPrigimaliaWorldMechanism()
{
    bReplicates=true;
    PrimaryActorTick.bCanEverTick=true;PrimaryActorTick.TickInterval=1.f;
    RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    Presentation=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Presentation"));
    Presentation->SetupAttachment(RootComponent);Presentation->SetMobility(EComponentMobility::Movable);
    Presentation->SetCanEverAffectNavigation(true);
    InteractionBounds=CreateDefaultSubobject<UBoxComponent>(TEXT("Interaction"));
    InteractionBounds->SetupAttachment(RootComponent);InteractionBounds->SetBoxExtent(FVector(60,60,100));
    InteractionBounds->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    InteractionBounds->SetCollisionResponseToAllChannels(ECR_Ignore);
    InteractionBounds->SetCollisionResponseToChannel(ECC_Visibility,ECR_Block);
    PoweredLight=CreateDefaultSubobject<UPointLightComponent>(TEXT("PoweredLight"));
    PoweredLight->SetupAttachment(RootComponent);PoweredLight->SetVisibility(false);
}
void AAnomaliaZPrigimaliaWorldMechanism::BeginPlay()
{
    Super::BeginPlay();
    if(HasAuthority())
        if(auto* Store=GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaWorldStateSubsystem>()) SetActorTickEnabled(!Store->Register(this));
    if(!HasAuthority()) SetActorTickEnabled(false);
    OnRep_State();
}
void AAnomaliaZPrigimaliaWorldMechanism::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if(HasAuthority())
        if(auto* Store=GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaWorldStateSubsystem>())
            if(Store->IsReady() && Store->Register(this)) SetActorTickEnabled(false);
}
void AAnomaliaZPrigimaliaWorldMechanism::EndPlay(const EEndPlayReason::Type Reason)
{
    if(HasAuthority())
        if(auto* Store=GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaWorldStateSubsystem>()) Store->Unregister(this);
    Super::EndPlay(Reason);
}
bool AAnomaliaZPrigimaliaWorldMechanism::CanInteract(const AAnomaliaZPrigimaliaSurvivor* User) const
{
    if(!HasAuthority() || !IsValid(User) || User->GetWorld()!=GetWorld() || !User->HasAuthority() ||
       !User->GetController() || User->GetController()->GetPawn()!=User || User->Health<=0 || User->bSleeping ||
       FVector::DistSquared(User->GetActorLocation(),GetActorLocation())>FMath::Square(275.f)) return false;
    FVector Eye;FRotator View;User->GetActorEyesViewPoint(Eye,View);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaZPrigimaliaMechanismLOS),true,User);Query.AddIgnoredActor(this);
    FHitResult Hit;
    return !GetWorld()->LineTraceSingleByChannel(Hit,Eye,GetActorLocation(),ECC_Visibility,Query);
}
bool AAnomaliaZPrigimaliaWorldMechanism::TryInteract(AAnomaliaZPrigimaliaSurvivor* User)
{
    auto* Store=GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaWorldStateSubsystem>();FString Error;
    return Store && CanInteract(User) && Store->Interact(this,User,Error);
}
void AAnomaliaZPrigimaliaWorldMechanism::ApplyServerState(const FAnomaliaZPrigimaliaMechanismState& NewState,bool Power,bool Overload)
{
    if(!HasAuthority()) return;
    State=NewState;bPowered=Power;bOverloaded=Overload;
    if(IsValid(ControlledDoor) && Definition)
        ControlledDoor->SetLockedOnServer(!State.bUnlocked || (Definition->bRequiresPower && !Power));
    OnRep_State();ForceNetUpdate();
}
void AAnomaliaZPrigimaliaWorldMechanism::OnRep_State()
{
    if(!Definition) return;
    PoweredLight->SetVisibility(bPowered && Definition->Kind==EAnomaliaZPrigimaliaWorldMechanism::Consumer);
    if(Definition->Kind==EAnomaliaZPrigimaliaWorldMechanism::Repair)
    {
        TSoftObjectPtr<UStaticMesh> Mesh;
        if(State.Repair==EAnomaliaZPrigimaliaRepairState::Repaired) Mesh=Definition->RepairedMesh;
        else if(Definition->RepairStages.Num())
        {
            double Total=0,Done=0;
            for(const auto& Need:Definition->Materials) {Total+=Need.Value;Done+=State.GetDeposited(Need.Key);}
            const int32 Index=FMath::Clamp(FMath::FloorToInt(Total>0?Done/Total*Definition->RepairStages.Num():0),0,Definition->RepairStages.Num()-1);
            Mesh=Definition->RepairStages[Index];
        }
        Presentation->SetStaticMesh(Mesh.LoadSynchronous());
        // Only collision from the licensed mesh is used, including its real gaps/spans.
        Presentation->SetCollisionProfileName(TEXT("BlockAll"));
        Presentation->SetCollisionEnabled(State.Repair==EAnomaliaZPrigimaliaRepairState::Disabled?ECollisionEnabled::NoCollision:ECollisionEnabled::QueryAndPhysics);
    }
    OnWorldStateChanged();
}
void AAnomaliaZPrigimaliaWorldMechanism::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaZPrigimaliaWorldMechanism,State);DOREPLIFETIME(AAnomaliaZPrigimaliaWorldMechanism,bPowered);
    DOREPLIFETIME(AAnomaliaZPrigimaliaWorldMechanism,bOverloaded);DOREPLIFETIME(AAnomaliaZPrigimaliaWorldMechanism,ActiveWorldEvent);
    DOREPLIFETIME(AAnomaliaZPrigimaliaWorldMechanism,WorldEventEndsUtc);
}
