#include "AnomaliaSurvivor.h"
#include "AnomaliaVehiclePawn.h"
#include "AnomaliaGameMode.h"
#include "AnomaliaInventoryComponent.h"
#include "AnomaliaInventoryWidget.h"
#include "AnomaliaVitalsComponent.h"
#include "AnomaliaHomesteadStation.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PlayerController.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Camera/CameraComponent.h"
#include "Components/InputComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Net/UnrealNetwork.h"

AAnomaliaSurvivor::AAnomaliaSurvivor()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = true;
    SetReplicateMovement(true);
    GetCharacterMovement()->MaxWalkSpeed = 450.f;
    InventoryComponent = CreateDefaultSubobject<UAnomaliaInventoryComponent>(TEXT("InventoryComponent"));
    VitalsComponent = CreateDefaultSubobject<UAnomaliaVitalsComponent>(TEXT("VitalsComponent"));
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

void AAnomaliaSurvivor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!HasAuthority()) return;
    const float PreviousHunger = Hunger;
    const float PreviousThirst = Thirst;
    const float PreviousHealth = Health;
    // Read only this world's authoritative GameMode. Clients cannot change server survival rates.
    const AAnomaliaGameMode* Rules = GetWorld() ? Cast<AAnomaliaGameMode>(GetWorld()->GetAuthGameMode()) : nullptr;
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
        ActiveBed.Reset();
        if (GetCharacterMovement()) GetCharacterMovement()->SetMovementMode(MOVE_Walking);
        OnRestChanged();
    }
    const float PreviousFatigue = Fatigue;
    const float RestStep = FMath::Min(DeltaSeconds, 0.25f);
    Fatigue = bSleeping
        ? FMath::Max(0.f, Fatigue - RestStep * 0.7f)
        : FMath::Min(100.f, Fatigue + RestStep * 0.009f);
    if (!FMath::IsNearlyEqual(Fatigue, PreviousFatigue, 0.01f)) OnRestChanged();
}

void AAnomaliaSurvivor::RestoreSurvival(float Food, float Water, float HP)
{
    if (!HasAuthority()) return;
    Hunger = FMath::Clamp(Food, 0.f, 100.f);
    Thirst = FMath::Clamp(Water, 0.f, 100.f);
    Health = FMath::Clamp(HP, 0.f, 100.f);
    OnSurvivalChanged();
}

void AAnomaliaSurvivor::OnRep_Survival() { OnSurvivalChanged(); }

void AAnomaliaSurvivor::RestoreFatigue(float SavedFatigue)
{
    if (!HasAuthority() || !FMath::IsFinite(SavedFatigue)) return;
    Fatigue = FMath::Clamp(SavedFatigue, 0.f, 100.f);
    OnRestChanged();
}

void AAnomaliaSurvivor::OnRep_Rest()
{
    // Real movement-mode changes also replicate from the server to simulated proxies.
    OnRestChanged();
}

void AAnomaliaSurvivor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaSurvivor, Hunger);
    DOREPLIFETIME(AAnomaliaSurvivor, Thirst);
    DOREPLIFETIME(AAnomaliaSurvivor, Health);
    DOREPLIFETIME(AAnomaliaSurvivor, Fatigue);
    DOREPLIFETIME(AAnomaliaSurvivor, bSleeping);
}

void AAnomaliaSurvivor::SetupPlayerInputComponent(UInputComponent* Input)
{
    Super::SetupPlayerInputComponent(Input);
    Input->BindAxis(TEXT("MoveForward"), this, &AAnomaliaSurvivor::MoveForward);
    Input->BindAxis(TEXT("MoveRight"), this, &AAnomaliaSurvivor::MoveRight);
    Input->BindAxis(TEXT("Turn"), this, &AAnomaliaSurvivor::Turn);
    Input->BindAxis(TEXT("LookUp"), this, &AAnomaliaSurvivor::LookUp);
    Input->BindAction(TEXT("Jump"), IE_Pressed, this, &ACharacter::Jump);
    Input->BindAction(TEXT("Jump"), IE_Released, this, &ACharacter::StopJumping);
    Input->BindAction(TEXT("Interact"), IE_Pressed, this, &AAnomaliaSurvivor::InputInteract);
    Input->BindAction(TEXT("Inventory"), IE_Pressed, this, &AAnomaliaSurvivor::InputInventory);
    Input->BindAction(TEXT("Sprint"), IE_Pressed, this, &AAnomaliaSurvivor::StartSprint);
    Input->BindAction(TEXT("Sprint"), IE_Released, this, &AAnomaliaSurvivor::StopSprint);
    Input->BindAction(TEXT("Rest"), IE_Pressed, this, &AAnomaliaSurvivor::InputRest);
}

void AAnomaliaSurvivor::StartSprint()
{
    if (VitalsComponent) VitalsComponent->RequestSprint(true);
}

void AAnomaliaSurvivor::StopSprint()
{
    if (VitalsComponent) VitalsComponent->RequestSprint(false);
}

void AAnomaliaSurvivor::InputRest()
{
    if (!IsLocallyControlled()) return;
    if (HasAuthority()) ServerRequestRest_Implementation();
    else ServerRequestRest();
}

void AAnomaliaSurvivor::ServerRequestRest_Implementation()
{
    if (!HasAuthority() || !GetController() || !GetWorld()) return;
    if (bSleeping)
    {
        bSleeping = false;
        ActiveBed.Reset();
        if (GetCharacterMovement()) GetCharacterMovement()->SetMovementMode(MOVE_Walking);
        OnRestChanged();
        return;
    }
    if (Health <= 0.f || GetVelocity().SizeSquared2D() > FMath::Square(60.f)) return;

    AAnomaliaHomesteadStation* NearestBed = nullptr;
    float NearestDistanceSquared = FMath::Square(250.f);
    for (TActorIterator<AAnomaliaHomesteadStation> It(GetWorld()); It; ++It)
    {
        AAnomaliaHomesteadStation* Station = *It;
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
    GetCharacterMovement()->StopMovementImmediately();
    GetCharacterMovement()->DisableMovement();
    OnRestChanged();
}

void AAnomaliaSurvivor::InputInventory()
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
    InventoryWidget = CreateWidget<UAnomaliaInventoryWidget>(PC, UAnomaliaInventoryWidget::StaticClass());
    if (!InventoryWidget) return;
    InventoryWidget->InitializeForInventory(InventoryComponent);
    InventoryWidget->AddToViewport(80);
    FInputModeGameAndUI InputMode;
    InputMode.SetWidgetToFocus(InventoryWidget->TakeWidget());
    InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    PC->SetInputMode(InputMode);
    PC->bShowMouseCursor = true;
    PC->SetIgnoreMoveInput(true);
    PC->SetIgnoreLookInput(true);
}

void AAnomaliaSurvivor::MoveForward(float Value)
{
    if (Controller && !FMath::IsNearlyZero(Value))
    {
        const FRotator Yaw(0.f, Controller->GetControlRotation().Yaw, 0.f);
        AddMovementInput(FRotationMatrix(Yaw).GetUnitAxis(EAxis::X), Value);
    }
}
void AAnomaliaSurvivor::MoveRight(float Value)
{
    if (Controller && !FMath::IsNearlyZero(Value))
    {
        const FRotator Yaw(0.f, Controller->GetControlRotation().Yaw, 0.f);
        AddMovementInput(FRotationMatrix(Yaw).GetUnitAxis(EAxis::Y), Value);
    }
}
void AAnomaliaSurvivor::Turn(float Value) { AddControllerYawInput(Value); }
void AAnomaliaSurvivor::LookUp(float Value) { AddControllerPitchInput(Value); }

void AAnomaliaSurvivor::InputInteract()
{
    if (!IsLocallyControlled()) return;
    if (HasAuthority()) ServerTryEnterVehicle_Implementation();
    else ServerTryEnterVehicle();
}

void AAnomaliaSurvivor::ServerTryEnterVehicle_Implementation()
{
    if (!HasAuthority() || !GetController() || Health <= 0.f || !GetWorld() || bSleeping) return;
    // A client only requests INTERACT; the server chooses the nearest harvest station.
    AAnomaliaHomesteadStation* NearestFarm = nullptr;
    float FarmDistanceSquared = FMath::Square(275.f);
    for (TActorIterator<AAnomaliaHomesteadStation> It(GetWorld()); It; ++It)
    {
        AAnomaliaHomesteadStation* Station = *It;
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
    AAnomaliaVehiclePawn* Nearest = nullptr;
    float NearestDistanceSquared = FMath::Square(450.f);
    for (TActorIterator<AAnomaliaVehiclePawn> It(GetWorld()); It; ++It)
    {
        AAnomaliaVehiclePawn* Candidate = *It;
        if (!IsValid(Candidate) || Candidate->HasDriver()) continue;
        const float DistanceSquared = FVector::DistSquared(GetActorLocation(), Candidate->GetActorLocation());
        if (DistanceSquared < NearestDistanceSquared)
        {
            Nearest = Candidate;
            NearestDistanceSquared = DistanceSquared;
        }
    }
    if (Nearest) Nearest->EnterVehicle(GetController(), this);
}
