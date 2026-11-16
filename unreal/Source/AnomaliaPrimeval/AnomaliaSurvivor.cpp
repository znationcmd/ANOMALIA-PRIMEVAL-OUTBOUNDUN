#include "AnomaliaSurvivor.h"
#include "AnomaliaVehiclePawn.h"
#include "AnomaliaGameMode.h"
#include "AnomaliaInventoryComponent.h"
#include "AnomaliaInventoryWidget.h"
#include "AnomaliaRefrigerator.h"
#include "AnomaliaPowerGenerator.h"
#include "AnomaliaRefrigeratorWidget.h"
#include "AnomaliaBatteryCharger.h"
#include "AnomaliaWorkLight.h"
#include "AnomaliaPowerUtilityWidget.h"
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
    Input->BindAction(TEXT("Interact"), IE_Pressed, this, &AAnomaliaSurvivor::InputInteract);
    Input->BindAction(TEXT("Inventory"), IE_Pressed, this, &AAnomaliaSurvivor::InputInventory);
}

void AAnomaliaSurvivor::InputInventory()
{
    if (!IsLocallyControlled() || !InventoryComponent) return;
    if (FridgeWidget) { CloseFridgeInterface(); return; }
    if (PowerUtilityWidget) { ClosePowerUtilityInterface(); return; }
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
    if (FridgeWidget) { CloseFridgeInterface(); return; }
    if (PowerUtilityWidget) { ClosePowerUtilityInterface(); return; }
    AActor* NearestDevice = nullptr;
    float BestDistanceSq = FMath::Square(300.f);
    if (GetWorld())
    {
        auto Compare = [&](AActor* Candidate)
        {
            if (!IsValid(Candidate)) return;
            const float Dist = FVector::DistSquared(Candidate->GetActorLocation(), GetActorLocation());
            if (Dist <= BestDistanceSq) { BestDistanceSq = Dist; NearestDevice = Candidate; }
        };
        for (TActorIterator<AAnomaliaRefrigerator> It(GetWorld()); It; ++It) Compare(*It);
        for (TActorIterator<AAnomaliaPowerGenerator> It(GetWorld()); It; ++It) Compare(*It);
        for (TActorIterator<AAnomaliaBatteryCharger> It(GetWorld()); It; ++It) Compare(*It);
        for (TActorIterator<AAnomaliaWorkLight> It(GetWorld()); It; ++It) Compare(*It);
    }
    if (NearestDevice)
    {
        if (AAnomaliaRefrigerator* Fridge = Cast<AAnomaliaRefrigerator>(NearestDevice))
            OpenFridgeInterface(Fridge);
        else OpenPowerUtilityInterface(NearestDevice);
        return;
    }
    if (HasAuthority()) ServerTryEnterVehicle_Implementation();
    else ServerTryEnterVehicle();
}

void AAnomaliaSurvivor::OpenFridgeInterface(AAnomaliaRefrigerator* Fridge)
{
    if (!IsLocallyControlled() || !IsValid(Fridge) || !Controller) return;
    APlayerController* PC = Cast<APlayerController>(Controller);
    if (!PC) return;
    if (InventoryWidget && InventoryWidget->IsInViewport()) { InventoryWidget->RemoveFromParent(); InventoryWidget = nullptr; }
    FridgeWidget = CreateWidget<UAnomaliaRefrigeratorWidget>(PC, UAnomaliaRefrigeratorWidget::StaticClass());
    if (!FridgeWidget) return;
    FridgeWidget->InitializeForFridge(this, Fridge);
    FridgeWidget->AddToViewport(90);
    FInputModeGameAndUI InputMode;
    InputMode.SetWidgetToFocus(FridgeWidget->TakeWidget());
    InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    PC->SetInputMode(InputMode);
    PC->bShowMouseCursor = true;
    PC->SetIgnoreMoveInput(true);
    PC->SetIgnoreLookInput(true);
}

void AAnomaliaSurvivor::CloseFridgeInterface()
{
    if (FridgeWidget) { FridgeWidget->RemoveFromParent(); FridgeWidget = nullptr; }
    APlayerController* PC = Cast<APlayerController>(Controller);
    if (!PC || !IsLocallyControlled()) return;
    PC->SetInputMode(FInputModeGameOnly());
    PC->bShowMouseCursor = false;
    PC->SetIgnoreMoveInput(false);
    PC->SetIgnoreLookInput(false);
}

void AAnomaliaSurvivor::RequestDepositToFridge(AAnomaliaRefrigerator* Fridge, FName ItemId, int32 Count)
{
    if (!IsLocallyControlled() || !IsValid(Fridge)) return;
    if (HasAuthority()) Fridge->DepositOnServer(this, ItemId, Count);
    else ServerDepositToFridge(Fridge, ItemId, Count);
}

void AAnomaliaSurvivor::RequestWithdrawFromFridge(AAnomaliaRefrigerator* Fridge, FName ItemId, int32 Count)
{
    if (!IsLocallyControlled() || !IsValid(Fridge)) return;
    if (HasAuthority()) Fridge->WithdrawOnServer(this, ItemId, Count);
    else ServerWithdrawFromFridge(Fridge, ItemId, Count);
}

void AAnomaliaSurvivor::ServerDepositToFridge_Implementation(AAnomaliaRefrigerator* Fridge, FName ItemId, int32 Count)
{
    if (IsValid(Fridge)) Fridge->DepositOnServer(this, ItemId, Count);
}

void AAnomaliaSurvivor::ServerWithdrawFromFridge_Implementation(AAnomaliaRefrigerator* Fridge, FName ItemId, int32 Count)
{
    if (IsValid(Fridge)) Fridge->WithdrawOnServer(this, ItemId, Count);
}

void AAnomaliaSurvivor::RequestSetFridgeOn(AAnomaliaRefrigerator* Fridge, bool bOn)
{
    if (!IsLocallyControlled() || !IsValid(Fridge)) return;
    if (HasAuthority()) ServerSetFridgeOn_Implementation(Fridge, bOn);
    else ServerSetFridgeOn(Fridge, bOn);
}

void AAnomaliaSurvivor::RequestSetGeneratorRunning(AAnomaliaPowerGenerator* Generator, bool bOn)
{
    if (!IsLocallyControlled() || !IsValid(Generator)) return;
    if (HasAuthority()) ServerSetGeneratorRunning_Implementation(Generator, bOn);
    else ServerSetGeneratorRunning(Generator, bOn);
}

void AAnomaliaSurvivor::ServerSetFridgeOn_Implementation(AAnomaliaRefrigerator* Fridge, bool bOn)
{
    if (Health <= 0.f || !IsValid(Fridge) || Fridge->GetWorld() != GetWorld() ||
        FVector::DistSquared(Fridge->GetActorLocation(), GetActorLocation()) > FMath::Square(300.f)) return;
    Fridge->SetSwitchedOnServer(bOn);
}

void AAnomaliaSurvivor::ServerSetGeneratorRunning_Implementation(AAnomaliaPowerGenerator* Generator, bool bOn)
{
    if (Health <= 0.f || !IsValid(Generator) || Generator->GetWorld() != GetWorld() ||
        FVector::DistSquared(Generator->GetActorLocation(), GetActorLocation()) > FMath::Square(300.f)) return;
    Generator->SetRunningOnServer(bOn);
}

void AAnomaliaSurvivor::OpenPowerUtilityInterface(AActor* Device)
{
    if (!IsLocallyControlled() || !IsValid(Device) || !Controller) return;
    APlayerController* PC = Cast<APlayerController>(Controller);
    if (!PC) return;
    if (InventoryWidget && InventoryWidget->IsInViewport())
    {
        InventoryWidget->RemoveFromParent();
        InventoryWidget = nullptr;
    }
    PowerUtilityWidget = CreateWidget<UAnomaliaPowerUtilityWidget>(PC, UAnomaliaPowerUtilityWidget::StaticClass());
    if (!PowerUtilityWidget) return;
    PowerUtilityWidget->InitializeForDevice(this, Device);
    PowerUtilityWidget->AddToViewport(90);
    FInputModeGameAndUI Mode;
    Mode.SetWidgetToFocus(PowerUtilityWidget->TakeWidget());
    Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    PC->SetInputMode(Mode);
    PC->bShowMouseCursor = true;
    PC->SetIgnoreMoveInput(true);
    PC->SetIgnoreLookInput(true);
}

void AAnomaliaSurvivor::ClosePowerUtilityInterface()
{
    if (PowerUtilityWidget) { PowerUtilityWidget->RemoveFromParent(); PowerUtilityWidget = nullptr; }
    if (!IsLocallyControlled()) return;
    APlayerController* PC = Cast<APlayerController>(Controller);
    if (!PC) return;
    PC->SetInputMode(FInputModeGameOnly());
    PC->bShowMouseCursor = false;
    PC->SetIgnoreMoveInput(false);
    PC->SetIgnoreLookInput(false);
}

void AAnomaliaSurvivor::RequestSetChargerOn(AAnomaliaBatteryCharger* Charger, bool bOn)
{
    if (!IsLocallyControlled() || !IsValid(Charger)) return;
    if (HasAuthority()) ServerSetChargerOn_Implementation(Charger, bOn);
    else ServerSetChargerOn(Charger, bOn);
}

void AAnomaliaSurvivor::RequestInsertBattery(AAnomaliaBatteryCharger* Charger)
{
    if (!IsLocallyControlled() || !IsValid(Charger)) return;
    if (HasAuthority()) ServerInsertBattery_Implementation(Charger);
    else ServerInsertBattery(Charger);
}

void AAnomaliaSurvivor::RequestRemoveBattery(AAnomaliaBatteryCharger* Charger)
{
    if (!IsLocallyControlled() || !IsValid(Charger)) return;
    if (HasAuthority()) ServerRemoveBattery_Implementation(Charger);
    else ServerRemoveBattery(Charger);
}

void AAnomaliaSurvivor::RequestSetWorkLightOn(AAnomaliaWorkLight* Light, bool bOn)
{
    if (!IsLocallyControlled() || !IsValid(Light)) return;
    if (HasAuthority()) ServerSetWorkLightOn_Implementation(Light, bOn);
    else ServerSetWorkLightOn(Light, bOn);
}

void AAnomaliaSurvivor::RequestRefuelGenerator(AAnomaliaPowerGenerator* Generator)
{
    if (!IsLocallyControlled() || !IsValid(Generator)) return;
    if (HasAuthority()) ServerRefuelGenerator_Implementation(Generator);
    else ServerRefuelGenerator(Generator);
}

void AAnomaliaSurvivor::RequestPickupGenerator(AAnomaliaPowerGenerator* Generator)
{
    if (!IsLocallyControlled() || !IsValid(Generator)) return;
    if (HasAuthority()) ServerPickupGenerator_Implementation(Generator);
    else ServerPickupGenerator(Generator);
}

void AAnomaliaSurvivor::RequestPlaceGenerator(AAnomaliaPowerGenerator* Generator)
{
    if (!IsLocallyControlled() || !IsValid(Generator)) return;
    if (HasAuthority()) ServerPlaceGenerator_Implementation(Generator);
    else ServerPlaceGenerator(Generator);
}

static bool CanUseElectricalDevice(const AAnomaliaSurvivor* Player, const AActor* Device)
{
    return IsValid(Player) && IsValid(Device) && Player->Health > 0.f &&
        Device->GetWorld() == Player->GetWorld() &&
        FVector::DistSquared(Device->GetActorLocation(), Player->GetActorLocation()) <= FMath::Square(300.f);
}

void AAnomaliaSurvivor::ServerSetChargerOn_Implementation(AAnomaliaBatteryCharger* Charger, bool bOn)
{
    if (CanUseElectricalDevice(this, Charger)) Charger->SetSwitchedOnServer(bOn);
}

void AAnomaliaSurvivor::ServerInsertBattery_Implementation(AAnomaliaBatteryCharger* Charger)
{
    if (CanUseElectricalDevice(this, Charger)) Charger->InsertBatteryOnServer(this);
}

void AAnomaliaSurvivor::ServerRemoveBattery_Implementation(AAnomaliaBatteryCharger* Charger)
{
    if (CanUseElectricalDevice(this, Charger)) Charger->RemoveBatteryOnServer(this);
}

void AAnomaliaSurvivor::ServerSetWorkLightOn_Implementation(AAnomaliaWorkLight* Light, bool bOn)
{
    if (CanUseElectricalDevice(this, Light)) Light->SetSwitchedOnServer(bOn);
}

void AAnomaliaSurvivor::ServerRefuelGenerator_Implementation(AAnomaliaPowerGenerator* Generator)
{
    if (!CanUseElectricalDevice(this, Generator) || !IsValid(InventoryComponent) ||
        Generator->FuelLitres > 25.f || IsValid(Generator->Carrier)) return;
    if (InventoryComponent->TryRemoveItem(TEXT("gasoline_canister"), 1))
        Generator->RefuelOnServer(5.f);
}

void AAnomaliaSurvivor::ServerPickupGenerator_Implementation(AAnomaliaPowerGenerator* Generator)
{
    if (CanUseElectricalDevice(this, Generator)) Generator->TryPickupOnServer(this);
}

void AAnomaliaSurvivor::ServerPlaceGenerator_Implementation(AAnomaliaPowerGenerator* Generator)
{
    if (IsValid(Generator) && Generator->GetWorld() == GetWorld() &&
        Generator->Carrier == this) Generator->TryPlaceOnServer(this);
}

void AAnomaliaSurvivor::ServerTryEnterVehicle_Implementation()
{
    if (!HasAuthority() || !GetController() || Health <= 0.f || !GetWorld()) return;
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
