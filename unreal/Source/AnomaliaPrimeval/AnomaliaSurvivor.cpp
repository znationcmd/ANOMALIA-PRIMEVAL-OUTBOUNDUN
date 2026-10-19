#include "AnomaliaSurvivor.h"
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
    Hunger = FMath::Max(0.f, Hunger - DeltaSeconds * 0.015f);
    Thirst = FMath::Max(0.f, Thirst - DeltaSeconds * 0.025f);
    if (Hunger <= 0.f || Thirst <= 0.f) Health = FMath::Max(0.f, Health - DeltaSeconds * 0.25f);
    if (PreviousHunger != Hunger || PreviousThirst != Thirst) OnSurvivalChanged();
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

void AAnomaliaSurvivor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaSurvivor, Hunger);
    DOREPLIFETIME(AAnomaliaSurvivor, Thirst);
    DOREPLIFETIME(AAnomaliaSurvivor, Health);
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
