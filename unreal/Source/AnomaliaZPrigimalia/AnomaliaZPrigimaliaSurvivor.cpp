#include "AnomaliaZPrigimaliaSurvivor.h"
#include "Vehicles/AnomaliaZPrigimaliaChaosRoadVehicle.h"
#include "ReactiveWorld/AnomaliaZPrigimaliaWorldMechanism.h"
#include "AnomaliaZPrigimaliaVehiclePawn.h"
#include "AnomaliaZPrigimaliaDoorActor.h"
#include "Vehicles/AnomaliaZPrigimaliaVehiclePanelComponent.h"
#include "AnomaliaZPrigimaliaGameMode.h"
#include "AnomaliaZPrigimaliaInventoryComponent.h"
#include "AnomaliaZPrigimaliaLootSubsystem.h"
#include "AnomaliaZPrigimaliaLootPickup.h"
#include "AnomaliaZPrigimaliaInventoryWidget.h"
#include "AnomaliaZPrigimaliaStatusWidget.h"
#include "AnomaliaZPrigimaliaSessionWidget.h"
#include "AnomaliaZPrigimaliaVitalsComponent.h"
#include "AnomaliaZPrigimaliaItemEffectsComponent.h"
#include "AnomaliaZPrigimaliaHomesteadStation.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PlayerController.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Camera/CameraComponent.h"
#include "Components/InputComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Net/UnrealNetwork.h"

AAnomaliaZPrigimaliaSurvivor::AAnomaliaZPrigimaliaSurvivor()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = true;
    SetReplicateMovement(true);
    GetCharacterMovement()->MaxWalkSpeed = 450.f;
    GetCharacterMovement()->NavAgentProps.bCanCrouch = true;
    GetCharacterMovement()->SetCrouchedHalfHeight(60.f);
    InventoryComponent = CreateDefaultSubobject<UAnomaliaZPrigimaliaInventoryComponent>(TEXT("InventoryComponent"));
    VitalsComponent = CreateDefaultSubobject<UAnomaliaZPrigimaliaVitalsComponent>(TEXT("VitalsComponent"));
    ItemEffectsComponent = CreateDefaultSubobject<UAnomaliaZPrigimaliaItemEffectsComponent>(TEXT("ItemEffectsComponent"));
    // Keep the original character mesh as the animation leader; clothes are optional.
    JacketMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("JacketMesh"));
    PantsMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("PantsMesh"));
    BootsMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("BootsMesh"));
    GlovesMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("GlovesMesh"));
    HeadgearMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("HeadgearMesh"));
    BackpackMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("BackpackMesh"));
    VestMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("VestMesh"));
    for (USkeletalMeshComponent* Part : {JacketMesh.Get(), PantsMesh.Get(), BootsMesh.Get(), GlovesMesh.Get(), HeadgearMesh.Get(), BackpackMesh.Get(), VestMesh.Get()})
    {
        Part->SetupAttachment(GetMesh());
        Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Part->SetLeaderPoseComponent(GetMesh());
    }
    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    CameraBoom->SetupAttachment(GetRootComponent());
    CameraBoom->TargetArmLength = 350.f;
    CameraBoom->bUsePawnControlRotation = true;
    FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
    FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
    FollowCamera->bUsePawnControlRotation = false;
    bUseControllerRotationYaw = false;
    GetCharacterMovement()->bOrientRotationToMovement = true;
}

bool AAnomaliaZPrigimaliaSurvivor::SetClothingMesh(FName Slot, USkeletalMesh* MeshAsset)
{
    USkeletalMeshComponent* Target = nullptr;
    if (Slot == TEXT("Jacket")) Target = JacketMesh;
    else if (Slot == TEXT("Pants")) Target = PantsMesh;
    else if (Slot == TEXT("Boots")) Target = BootsMesh;
    else if (Slot == TEXT("Gloves")) Target = GlovesMesh;
    else if (Slot == TEXT("Headgear")) Target = HeadgearMesh;
    else if (Slot == TEXT("Backpack")) Target = BackpackMesh;
    else if (Slot == TEXT("Vest")) Target = VestMesh;
    if (!Target) return false;
    // Never silently apply a mesh with a different bone hierarchy.
    if (MeshAsset && (!GetMesh() || !GetMesh()->GetSkeletalMeshAsset() ||
        MeshAsset->GetSkeleton() != GetMesh()->GetSkeletalMeshAsset()->GetSkeleton())) return false;
    if(!MeshAsset&&HasAuthority()&&GetWorld()&&GetWorld()->IsGameWorld()&&InventoryComponent&&!InventoryComponent->CanRemoveWornStorage(Slot))
    {
        InventoryComponent->UseMessage=TEXT("Videz le rangement du vêtement avant de le retirer.");
        InventoryComponent->OnInventoryUpdated.Broadcast();return false;
    }
    Target->SetSkeletalMeshAsset(MeshAsset);
    if(HasAuthority()&&InventoryComponent)InventoryComponent->SynchronizeWornStorage();
    return true;
}

float AAnomaliaZPrigimaliaSurvivor::TakeDamage(float Amount,const FDamageEvent& Event,AController* InstigatorController,AActor* Causer)
{
    if(!HasAuthority() || !CanBeDamaged() || !FMath::IsFinite(Amount) || Amount<=0 || Health<=0) return 0;
    const float Applied=FMath::Min(Health,Amount);
    Super::TakeDamage(Applied,Event,InstigatorController,Causer);
    Health=FMath::Max(0.f,Health-Applied);
    if(ItemEffectsComponent) ItemEffectsComponent->AddInjury(Applied);
    if(InventoryComponent)
    {
        InventoryComponent->ApplyWornWear(Applied*.1f);
        const auto Items=InventoryComponent->Stacks;
        for(const auto& Item:Items)if(Item.ContainerId==TEXT("hands")&&InventoryComponent->SupportsItemWear(Item.ItemId))InventoryComponent->ApplyItemWear(Item.StackId,Applied*.05f);
    }
    OnSurvivalChanged();return Applied;
}

void AAnomaliaZPrigimaliaSurvivor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    // The owning HUD also reads replicated values on clients; dedicated servers create no UI.
    if (!StatusWidget && IsLocallyControlled() && GetNetMode()!=NM_DedicatedServer)
    {
        if (auto* PC=Cast<APlayerController>(Controller))
        {
            StatusWidget=CreateWidget<UAnomaliaZPrigimaliaStatusWidget>(PC,UAnomaliaZPrigimaliaStatusWidget::StaticClass());
            if (StatusWidget) { StatusWidget->InitializeForSurvivor(this); StatusWidget->AddToViewport(20); }
        }
    }
    if (!HasAuthority()) return;
    const float PreviousHunger = Hunger;
    const float PreviousThirst = Thirst;
    const float PreviousHealth = Health;
    // Read only this world's authoritative GameMode. Clients cannot change server survival rates.
    const AAnomaliaZPrigimaliaGameMode* Rules = GetWorld() ? Cast<AAnomaliaZPrigimaliaGameMode>(GetWorld()->GetAuthGameMode()) : nullptr;
    const float HungerRate = Rules ? Rules->ActiveServerSettings.HungerDrainPerSecond : 0.015f;
    const float ThirstRate = Rules ? Rules->ActiveServerSettings.ThirstDrainPerSecond : 0.025f;
    const float DamageRate = Rules ? Rules->ActiveServerSettings.StarvationDamagePerSecond : 0.25f;
    Hunger = FMath::Max(0.f, Hunger - DeltaSeconds * HungerRate);
    Thirst = FMath::Max(0.f, Thirst - DeltaSeconds * ThirstRate);
    if (Hunger <= 0.f || Thirst <= 0.f) Health = FMath::Max(0.f, Health - DeltaSeconds * DamageRate);
    if (PreviousHunger != Hunger || PreviousThirst != Thirst || PreviousHealth != Health) OnSurvivalChanged();

    // Sleep is server-owned; a bed must still exist in this world and remain nearby.
    if (bSleeping &&
        (!ActiveBed.IsValid() || !ActiveBed->IsRestPlace() || Health <= 0.f ||
         FVector::DistSquared(GetActorLocation(), ActiveBed->GetActorLocation()) > FMath::Square(350.f)))
    {
        bSleeping = false;
        SleepRemainingSeconds = 0.f;
        ActiveBed.Reset();
        if (GetCharacterMovement()) GetCharacterMovement()->SetMovementMode(MOVE_Walking);
        OnRestChanged();
    }
    const float PreviousFatigue = Fatigue;
    const float RestStep = FMath::Min(DeltaSeconds, 0.25f);
    Fatigue = bSleeping
        ? FMath::Max(0.f, Fatigue - RestStep * (100.f/30.f))
        : FMath::Min(100.f, Fatigue + RestStep * 0.009f);
    if (bSleeping)
    {
        SleepRemainingSeconds=FMath::Max(0.f,SleepRemainingSeconds-RestStep);
        if (SleepRemainingSeconds<=KINDA_SMALL_NUMBER)
        {
            bSleeping=false; Fatigue=0.f; ActiveBed.Reset();
            if (GetCharacterMovement()) GetCharacterMovement()->SetMovementMode(MOVE_Walking);
            if (VitalsComponent) VitalsComponent->RestoreVitals(100.f,VitalsComponent->BodyTemperatureC);
            OnRestChanged();
        }
    }
    if (!FMath::IsNearlyEqual(Fatigue, PreviousFatigue, 0.01f)) OnRestChanged();
}

void AAnomaliaZPrigimaliaSurvivor::EndPlay(const EEndPlayReason::Type Reason)
{
    if (StatusWidget) { StatusWidget->RemoveFromParent(); StatusWidget=nullptr; }
    if (InventoryWidget) { InventoryWidget->RemoveFromParent(); InventoryWidget=nullptr; }
    Super::EndPlay(Reason);
}

void AAnomaliaZPrigimaliaSurvivor::RestoreSurvival(float Food, float Water, float HP)
{
    if (!HasAuthority()) return;
    Hunger = FMath::Clamp(Food, 0.f, 100.f);
    Thirst = FMath::Clamp(Water, 0.f, 100.f);
    Health = FMath::Clamp(HP, 0.f, 100.f);
    OnSurvivalChanged();
}

void AAnomaliaZPrigimaliaSurvivor::OnRep_Survival() { OnSurvivalChanged(); }

void AAnomaliaZPrigimaliaSurvivor::RestoreFatigue(float SavedFatigue)
{
    if (!HasAuthority() || !FMath::IsFinite(SavedFatigue)) return;
    Fatigue = FMath::Clamp(SavedFatigue, 0.f, 100.f);
    OnRestChanged();
}

void AAnomaliaZPrigimaliaSurvivor::OnRep_Rest()
{
    // Real movement-mode changes also replicate from the server to simulated proxies.
    OnRestChanged();
}

void AAnomaliaZPrigimaliaSurvivor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaZPrigimaliaSurvivor, Hunger);
    DOREPLIFETIME(AAnomaliaZPrigimaliaSurvivor, Thirst);
    DOREPLIFETIME(AAnomaliaZPrigimaliaSurvivor, Health);
    DOREPLIFETIME(AAnomaliaZPrigimaliaSurvivor, Fatigue);
    DOREPLIFETIME(AAnomaliaZPrigimaliaSurvivor, bSleeping);
    DOREPLIFETIME(AAnomaliaZPrigimaliaSurvivor, SleepRemainingSeconds);
}

void AAnomaliaZPrigimaliaSurvivor::SetupPlayerInputComponent(UInputComponent* Input)
{
    Super::SetupPlayerInputComponent(Input);
    Input->BindAxis(TEXT("MoveForward"), this, &AAnomaliaZPrigimaliaSurvivor::MoveForward);
    Input->BindAxis(TEXT("MoveRight"), this, &AAnomaliaZPrigimaliaSurvivor::MoveRight);
    Input->BindAxis(TEXT("Turn"), this, &AAnomaliaZPrigimaliaSurvivor::Turn);
    Input->BindAxis(TEXT("LookUp"), this, &AAnomaliaZPrigimaliaSurvivor::LookUp);
    Input->BindAxis(TEXT("TurnRate"), this, &AAnomaliaZPrigimaliaSurvivor::TurnRate);
    Input->BindAxis(TEXT("LookUpRate"), this, &AAnomaliaZPrigimaliaSurvivor::LookUpRate);
    Input->BindAction(TEXT("Jump"), IE_Pressed, this, &ACharacter::Jump);
    Input->BindAction(TEXT("Jump"), IE_Released, this, &ACharacter::StopJumping);
    Input->BindAction(TEXT("Interact"), IE_Pressed, this, &AAnomaliaZPrigimaliaSurvivor::InputInteract);
    Input->BindAction(TEXT("Pause"), IE_Pressed, this, &AAnomaliaZPrigimaliaSurvivor::InputPause);
    Input->BindAction(TEXT("VehicleCamera"), IE_Pressed, this, &AAnomaliaZPrigimaliaSurvivor::InputCamera);
    Input->BindAction(TEXT("Inventory"), IE_Pressed, this, &AAnomaliaZPrigimaliaSurvivor::InputInventory);
    Input->BindAction(TEXT("Sprint"), IE_Pressed, this, &AAnomaliaZPrigimaliaSurvivor::StartSprint);
    Input->BindAction(TEXT("Sprint"), IE_Released, this, &AAnomaliaZPrigimaliaSurvivor::StopSprint);
    Input->BindAction(TEXT("Rest"), IE_Pressed, this, &AAnomaliaZPrigimaliaSurvivor::InputRest);
    Input->BindAction(TEXT("TacticalCrouch"), IE_Pressed, this, &AAnomaliaZPrigimaliaSurvivor::ToggleTacticalCrouch);
    Input->BindAction(TEXT("PaceMode"), IE_Pressed, this, &AAnomaliaZPrigimaliaSurvivor::BeginPaceAdjustment);
    Input->BindAction(TEXT("PaceMode"), IE_Released, this, &AAnomaliaZPrigimaliaSurvivor::EndPaceAdjustment);
    Input->BindAction(TEXT("PaceUp"), IE_Pressed, this, &AAnomaliaZPrigimaliaSurvivor::IncreasePace);
    Input->BindAction(TEXT("PaceDown"), IE_Pressed, this, &AAnomaliaZPrigimaliaSurvivor::DecreasePace);
}

void AAnomaliaZPrigimaliaSurvivor::BeginPaceAdjustment() { bAdjustPaceWithWheel = IsLocallyControlled(); }
void AAnomaliaZPrigimaliaSurvivor::EndPaceAdjustment() { bAdjustPaceWithWheel = false; }
void AAnomaliaZPrigimaliaSurvivor::IncreasePace()
{
    if (IsLocallyControlled() && bAdjustPaceWithWheel && VitalsComponent)
        VitalsComponent->RequestPaceStep(FMath::Min<uint8>(6, VitalsComponent->PaceStep + 1));
}
void AAnomaliaZPrigimaliaSurvivor::DecreasePace()
{
    if (IsLocallyControlled() && bAdjustPaceWithWheel && VitalsComponent)
        VitalsComponent->RequestPaceStep(VitalsComponent->PaceStep > 0 ? VitalsComponent->PaceStep - 1 : 0);
}
void AAnomaliaZPrigimaliaSurvivor::ToggleTacticalCrouch()
{
    if (!IsLocallyControlled() || Health <= 0.f || bSleeping) return;
    // Native ACharacter crouch predicts and replicates capsule height via CharacterMovement.
    if (bIsCrouched) UnCrouch(); else Crouch();
}

void AAnomaliaZPrigimaliaSurvivor::StartSprint()
{
    if (VitalsComponent) VitalsComponent->RequestSprint(true);
}

void AAnomaliaZPrigimaliaSurvivor::StopSprint()
{
    if (VitalsComponent) VitalsComponent->RequestSprint(false);
}

void AAnomaliaZPrigimaliaSurvivor::InputRest()
{
    if (!IsLocallyControlled()) return;
    if (HasAuthority()) ServerRequestRest_Implementation();
    else ServerRequestRest();
}

void AAnomaliaZPrigimaliaSurvivor::ServerRequestRest_Implementation()
{
    if (!HasAuthority() || !GetController() || !GetWorld()) return;
    if (bSleeping)
    {
        bSleeping = false;
        SleepRemainingSeconds = 0.f;
        ActiveBed.Reset();
        if (GetCharacterMovement()) GetCharacterMovement()->SetMovementMode(MOVE_Walking);
        OnRestChanged();
        return;
    }
    if (Health <= 0.f || GetVelocity().SizeSquared2D() > FMath::Square(60.f)) return;

    AAnomaliaZPrigimaliaHomesteadStation* NearestBed = nullptr;
    float NearestDistanceSquared = FMath::Square(250.f);
    for (TActorIterator<AAnomaliaZPrigimaliaHomesteadStation> It(GetWorld()); It; ++It)
    {
        AAnomaliaZPrigimaliaHomesteadStation* Station = *It;
        if (!IsValid(Station) || !Station->IsRestPlace()) continue;
        const float DistanceSquared = FVector::DistSquared(GetActorLocation(), Station->GetActorLocation());
        if (DistanceSquared < NearestDistanceSquared)
        {
            NearestBed = Station;
            NearestDistanceSquared = DistanceSquared;
        }
    }
    if (!NearestBed || !GetCharacterMovement()) return;
    ActiveBed = NearestBed;
    bSleeping = true;
    SleepRemainingSeconds = 30.f;
    GetCharacterMovement()->StopMovementImmediately();
    GetCharacterMovement()->DisableMovement();
    OnRestChanged();
}

void AAnomaliaZPrigimaliaSurvivor::CloseInventory()
{
    if (InventoryWidget && InventoryWidget->IsInViewport()) InputInventory();
}

void AAnomaliaZPrigimaliaSurvivor::InputInventory()
{
    if (!IsLocallyControlled() || !InventoryComponent) return;
    APlayerController* PC = Cast<APlayerController>(Controller);
    if (!PC) return;
    if (InventoryWidget && InventoryWidget->IsInViewport())
    {
        InventoryWidget->RemoveFromParent();
        InventoryWidget = nullptr;
        PC->SetInputMode(FInputModeGameOnly());
        PC->bShowMouseCursor = false;
        PC->SetIgnoreMoveInput(false);
        PC->SetIgnoreLookInput(false);
        return;
    }
    UAnomaliaZPrigimaliaInventoryWidget::CreateForPlayerInventory(PC);
}

void AAnomaliaZPrigimaliaSurvivor::MoveForward(float Value)
{
    if (Controller && !FMath::IsNearlyZero(Value))
    {
        const FRotator Yaw(0.f, Controller->GetControlRotation().Yaw, 0.f);
        AddMovementInput(FRotationMatrix(Yaw).GetUnitAxis(EAxis::X), Value);
    }
}
void AAnomaliaZPrigimaliaSurvivor::MoveRight(float Value)
{
    if (Controller && !FMath::IsNearlyZero(Value))
    {
        const FRotator Yaw(0.f, Controller->GetControlRotation().Yaw, 0.f);
        AddMovementInput(FRotationMatrix(Yaw).GetUnitAxis(EAxis::Y), Value);
    }
}
void AAnomaliaZPrigimaliaSurvivor::Turn(float Value) { AddControllerYawInput(Value); }
void AAnomaliaZPrigimaliaSurvivor::LookUp(float Value) { AddControllerPitchInput(Value); }
void AAnomaliaZPrigimaliaSurvivor::TurnRate(float Value)
{
    if (GetWorld()) AddControllerYawInput(Value*90.f*GetWorld()->GetDeltaSeconds());
}
void AAnomaliaZPrigimaliaSurvivor::LookUpRate(float Value)
{
    if (GetWorld()) AddControllerPitchInput(Value*90.f*GetWorld()->GetDeltaSeconds());
}

void AAnomaliaZPrigimaliaSurvivor::InputInteract()
{
    if (!IsLocallyControlled()) return;
    if (HasAuthority()) ServerTryEnterVehicle_Implementation();
    else ServerTryEnterVehicle();
}

void AAnomaliaZPrigimaliaSurvivor::ServerTryEnterVehicle_Implementation()
{
    if (!HasAuthority() || !GetController() || Health <= 0.f || !GetWorld() || bSleeping) return;
    // Door targeting uses the server's view ray, never a client-supplied actor ID.
    FVector Eye;FRotator View;GetActorEyesViewPoint(Eye,View);
    FCollisionQueryParams DoorQuery(SCENE_QUERY_STAT(AnomaliaZPrigimaliaDoorTarget),true);
    DoorQuery.AddIgnoredActor(this);FHitResult DoorHit;
    if(GetWorld()->LineTraceSingleByChannel(DoorHit,Eye,Eye+GetControlRotation().Vector()*300.f,ECC_Visibility,DoorQuery))
    {
        if(auto* Panel=Cast<UAnomaliaZPrigimaliaVehiclePanelComponent>(DoorHit.GetComponent())){Panel->TryToggle(this);return;}
        if(auto* Mechanism=Cast<AAnomaliaZPrigimaliaWorldMechanism>(DoorHit.GetActor())) {Mechanism->TryInteract(this);return;}
        if(auto* Door=Cast<AAnomaliaZPrigimaliaDoorActor>(DoorHit.GetActor())){Door->TryToggle(this);return;}
    }
    // The client sends no item ID, count, player identity or arbitrary world target.
    if (auto* Loot = GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaLootSubsystem>())
    {
        AAnomaliaZPrigimaliaLootPickup* NearestLoot = nullptr;
        double Best = FMath::Square(250.0);
        for (TActorIterator<AAnomaliaZPrigimaliaLootPickup> It(GetWorld()); It; ++It)
        {
            const double Distance = FVector::DistSquared(GetActorLocation(), It->GetActorLocation());
            if (IsValid(*It) && !It->IsActorBeingDestroyed() && Distance < Best)
            { Best = Distance; NearestLoot = *It; }
        }
        if (NearestLoot)
        {
            const auto* Mode = GetWorld()->GetAuthGameMode<AAnomaliaZPrigimaliaGameMode>();
            FString Error;
            if (Mode) Loot->TryCollect(NearestLoot, this, Mode->GetPersistentPlayerId(GetController()), Error);
            return;
        }
    }
    // A client only requests INTERACT; the server chooses the nearest harvest station.
    AAnomaliaZPrigimaliaHomesteadStation* NearestFarm = nullptr;
    float FarmDistanceSquared = FMath::Square(275.f);
    for (TActorIterator<AAnomaliaZPrigimaliaHomesteadStation> It(GetWorld()); It; ++It)
    {
        AAnomaliaZPrigimaliaHomesteadStation* Station = *It;
        if (!IsValid(Station) || Station->GetHarvestItemId().IsNone()) continue;
        const float DistanceSquared = FVector::DistSquared(GetActorLocation(), Station->GetActorLocation());
        if (DistanceSquared < FarmDistanceSquared)
        {
            NearestFarm = Station;
            FarmDistanceSquared = DistanceSquared;
        }
    }
    if (NearestFarm)
    {
        NearestFarm->TryHarvest(this);
        return;
    }
    AAnomaliaZPrigimaliaVehiclePawn* Nearest = nullptr;
    float NearestDistanceSquared = FMath::Square(450.f);
    for (TActorIterator<AAnomaliaZPrigimaliaVehiclePawn> It(GetWorld()); It; ++It)
    {
        AAnomaliaZPrigimaliaVehiclePawn* Candidate = *It;
        if (!IsValid(Candidate) || Candidate->HasDriver()) continue;
        if (!Candidate->CanEnterFrom(this)) continue;
        const float DistanceSquared = FVector::DistSquared(GetActorLocation(), Candidate->GetActorLocation());
        if (DistanceSquared < NearestDistanceSquared)
        {
            Nearest = Candidate;
            NearestDistanceSquared = DistanceSquared;
        }
    }
    if (Nearest) Nearest->EnterVehicle(GetController(), this);
}

void AAnomaliaZPrigimaliaSurvivor::InputPause() { UAnomaliaZPrigimaliaSessionWidget::Open(Cast<APlayerController>(Controller)); }
void AAnomaliaZPrigimaliaSurvivor::InputCamera()
{
    const bool First=CameraBoom->TargetArmLength>1.f;
    CameraBoom->TargetArmLength=First?0.f:350.f;
    CameraBoom->SocketOffset=First?FVector(0,0,65):FVector::ZeroVector;
}



bool AAnomaliaZPrigimaliaSurvivor::RequestVehicleService(AAnomaliaZPrigimaliaChaosRoadVehicle* Vehicle,EAnomaliaZPrigimaliaVehicleServiceAction Action,int32 StackId,int32 ExpectedCount)
{
    if(!IsLocallyControlled()||!Vehicle)return false;
    if(HasAuthority())ServerVehicleService_Implementation(Vehicle,Action,StackId,ExpectedCount);
    else ServerVehicleService(Vehicle,Action,StackId,ExpectedCount);return true;
}
void AAnomaliaZPrigimaliaSurvivor::ServerVehicleService_Implementation(AAnomaliaZPrigimaliaChaosRoadVehicle* Vehicle,EAnomaliaZPrigimaliaVehicleServiceAction Action,int32 StackId,int32 ExpectedCount)
{
    if(!InventoryComponent||!GetController()||GetController()->GetPawn()!=this)return;
    FString Error;const bool Accepted=IsValid(Vehicle)&&Vehicle->GetWorld()==GetWorld()&&Vehicle->SurvivalSystems->Execute(this,Action,StackId,ExpectedCount,Error);
    InventoryComponent->UseMessage=Accepted?TEXT("Échange véhicule enregistré."):Error.IsEmpty()?TEXT("Action véhicule indisponible."):Error;
    InventoryComponent->OnInventoryUpdated.Broadcast();ForceNetUpdate();
}


