#include "AnomaliaFurnitureComponent.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaHomesteadStation.h"
#include "Components/InputComponent.h"
#include "GameFramework/PlayerController.h"
#include "Engine/Engine.h"
#include "CollisionQueryParams.h"
#include "Engine/World.h"

UAnomaliaFurnitureComponent::UAnomaliaFurnitureComponent()
{
    SetIsReplicatedByDefault(true);
    PrimaryComponentTick.bCanEverTick = false;
}
void UAnomaliaFurnitureComponent::RequestPlace(FName Type, FVector Location, float Yaw)
{ ServerRequest(EAnomaliaFurnitureCommand::Place, Type, FString(), Location, Yaw, false); }
void UAnomaliaFurnitureComponent::RequestMove(const FString& Id, FVector Location, float Yaw)
{ ServerRequest(EAnomaliaFurnitureCommand::Move, NAME_None, Id, Location, Yaw, false); }
void UAnomaliaFurnitureComponent::RequestRemove(const FString& Id, bool bConfirmed)
{ ServerRequest(EAnomaliaFurnitureCommand::Remove, NAME_None, Id, FVector::ZeroVector, 0, bConfirmed); }
void UAnomaliaFurnitureComponent::RequestUndo()
{ ServerRequest(EAnomaliaFurnitureCommand::Undo, NAME_None, FString(), FVector::ZeroVector, 0, false); }
void UAnomaliaFurnitureComponent::RequestRedo()
{ ServerRequest(EAnomaliaFurnitureCommand::Redo, NAME_None, FString(), FVector::ZeroVector, 0, false); }

void UAnomaliaFurnitureComponent::ServerRequest_Implementation(EAnomaliaFurnitureCommand Command,
    FName Type, const FString& Id, FVector Location, float Yaw, bool bConfirmed)
{
    AAnomaliaSurvivor* Caller = Cast<AAnomaliaSurvivor>(GetOwner());
    if (!Caller || !Caller->HasAuthority() || !Caller->GetController() || !GetWorld()) return;
    const double Now = GetWorld()->GetTimeSeconds();
    if (Now - LastRequestTime < .25) { ClientResult(false, TEXT("Too many furniture requests")); return; }
    LastRequestTime = Now;
    UAnomaliaFurnitureSubsystem* WorldFurniture = GetWorld()->GetSubsystem<UAnomaliaFurnitureSubsystem>();
    FString Error;
    const bool bSuccess = WorldFurniture && WorldFurniture->Execute(Caller, Command, Type, Id, Location, Yaw, bConfirmed, Error);
    ClientResult(bSuccess, bSuccess ? TEXT("Furniture saved") : Error);
}
void UAnomaliaFurnitureComponent::ClientResult_Implementation(bool bSuccess, const FString& Message)
{
    OnFurnitureResult(bSuccess, Message);
    if (GEngine) GEngine->AddOnScreenDebugMessage(-1, 3.f, bSuccess ? FColor::Green : FColor::Red,
        bSuccess ? TEXT("Ameublement sauvegarde.") : TEXT("Modification refusee."));
}

void UAnomaliaFurnitureComponent::BindInput(UInputComponent* Input)
{
    if (!Input) return;
    Input->BindAction(TEXT("FurniturePlaceBed"), IE_Pressed, this, &UAnomaliaFurnitureComponent::PlaceBedFromView);
    Input->BindAction(TEXT("FurnitureSelect"), IE_Pressed, this, &UAnomaliaFurnitureComponent::SelectFromView);
    Input->BindAction(TEXT("FurnitureMove"), IE_Pressed, this, &UAnomaliaFurnitureComponent::MoveSelectedToView);
    Input->BindAction(TEXT("FurnitureRotate"), IE_Pressed, this, &UAnomaliaFurnitureComponent::RotateSelected);
    Input->BindAction(TEXT("FurnitureUndo"), IE_Pressed, this, &UAnomaliaFurnitureComponent::InputUndo);
    Input->BindAction(TEXT("FurnitureRedo"), IE_Pressed, this, &UAnomaliaFurnitureComponent::InputRedo);
}

bool UAnomaliaFurnitureComponent::ViewHit(FHitResult& Hit, bool bIgnoreSelection) const
{
    const AAnomaliaSurvivor* Caller = Cast<AAnomaliaSurvivor>(GetOwner());
    APlayerController* PC = Caller ? Cast<APlayerController>(Caller->GetController()) : nullptr;
    if (!Caller || !Caller->IsLocallyControlled() || !PC || PC->IsMoveInputIgnored() || !GetWorld()) return false;
    FVector Origin; FRotator Rotation;
    PC->GetPlayerViewPoint(Origin, Rotation);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaFurnitureAim), false, Caller);
    if (bIgnoreSelection && Selected.IsValid()) Query.AddIgnoredActor(Selected.Get());
    return GetWorld()->LineTraceSingleByChannel(Hit, Origin, Origin + Rotation.Vector() * 1000.f,
        ECC_Visibility, Query);
}

void UAnomaliaFurnitureComponent::PlaceBedFromView()
{
    FHitResult Hit;
    if (ViewHit(Hit, false)) RequestPlace(TEXT("bed"), Hit.ImpactPoint + FVector(0,0,50), 0.f);
}
void UAnomaliaFurnitureComponent::SelectFromView()
{
    FHitResult Hit;
    if (!ViewHit(Hit, false)) return;
    AAnomaliaHomesteadStation* Candidate = Cast<AAnomaliaHomesteadStation>(Hit.GetActor());
    Selected = Candidate && !Candidate->PlacementId.IsEmpty() ? Candidate : nullptr;
    if (Selected.IsValid() && GEngine) GEngine->AddOnScreenDebugMessage(-1, 4.f, FColor::Cyan,
        TEXT("Meuble selectionne : T deplacer, H pivoter."));
}
void UAnomaliaFurnitureComponent::MoveSelectedToView()
{
    FHitResult Hit;
    if (Selected.IsValid() && ViewHit(Hit, true))
        RequestMove(Selected->PlacementId, Hit.ImpactPoint + FVector(0,0,50), Selected->GetActorRotation().Yaw);
}
void UAnomaliaFurnitureComponent::RotateSelected()
{
    FHitResult Hit;
    if (Selected.IsValid() && ViewHit(Hit, false))
        RequestMove(Selected->PlacementId, Selected->GetActorLocation(),
            FMath::UnwindDegrees(Selected->GetActorRotation().Yaw + 90.f));
}
void UAnomaliaFurnitureComponent::InputUndo()
{ FHitResult Hit; if (ViewHit(Hit, true)) RequestUndo(); }
void UAnomaliaFurnitureComponent::InputRedo()
{ FHitResult Hit; if (ViewHit(Hit, true)) RequestRedo(); }
