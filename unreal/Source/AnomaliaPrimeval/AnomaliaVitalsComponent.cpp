#include "AnomaliaVitalsComponent.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaItemEffectsComponent.h"
#include "AnomaliaInventoryComponent.h"
#include "AnomaliaGameMode.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Net/UnrealNetwork.h"

UAnomaliaVitalsComponent::UAnomaliaVitalsComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    SetIsReplicatedByDefault(true);
}

void UAnomaliaVitalsComponent::RequestSprint(bool bWanted)
{
    AAnomaliaSurvivor* Survivor = Cast<AAnomaliaSurvivor>(GetOwner());
    if (!Survivor || !Survivor->IsLocallyControlled()) return;
    if (Survivor->HasAuthority())
    {
        bSprintRequested = bWanted && Survivor->Health > 0.f;
    }
    else
    {
        ServerRequestSprint(bWanted);
    }
}

void UAnomaliaVitalsComponent::ServerRequestSprint_Implementation(bool bWanted)
{
    const AAnomaliaSurvivor* Survivor = Cast<AAnomaliaSurvivor>(GetOwner());
    if (!Survivor || !Survivor->HasAuthority() || !Survivor->GetController()) return;
    // Network ownership of this character component is enforced by Unreal RPC routing.
    bSprintRequested = bWanted && Survivor->Health > 0.f;
}

void UAnomaliaVitalsComponent::RequestPaceStep(uint8 RequestedStep)
{
    AAnomaliaSurvivor* Survivor = Cast<AAnomaliaSurvivor>(GetOwner());
    if (!Survivor || !Survivor->IsLocallyControlled()) return;
    RequestedStep = FMath::Min<uint8>(RequestedStep, 6);
    if (!Survivor->HasAuthority())
    {
        PaceStep = RequestedStep; // Owning client predicts only the capped presentation speed.
        ApplyMovementSpeed();
        ServerRequestPaceStep(RequestedStep);
        return;
    }
    PaceStep = RequestedStep;
    ApplyMovementSpeed();
}

void UAnomaliaVitalsComponent::ServerRequestPaceStep_Implementation(uint8 RequestedStep)
{
    const AAnomaliaSurvivor* Survivor = Cast<AAnomaliaSurvivor>(GetOwner());
    if (!Survivor || !Survivor->HasAuthority() || !Survivor->GetController()) return;
    PaceStep = FMath::Min<uint8>(RequestedStep, 6);
    ApplyMovementSpeed();
}

float UAnomaliaVitalsComponent::CalculateTacticalSpeed(uint8 Step, float LoadKg, float FatiguePercent, float InjuryScale)
{
    static const float Speeds[7] = { 150.f, 215.f, 280.f, 355.f, 450.f, 515.f, 575.f };
    const float Load = FMath::IsFinite(LoadKg) ? FMath::Clamp(LoadKg, 0.f, 100.f) : 100.f;
    const float Fatigue = FMath::IsFinite(FatiguePercent) ? FMath::Clamp(FatiguePercent, 0.f, 100.f) : 100.f;
    const float SafeInjuryScale = FMath::IsFinite(InjuryScale) ? FMath::Clamp(InjuryScale, .25f, 1.f) : .25f;
    const float LoadScale = FMath::Clamp(1.f - FMath::Max(0.f, Load - 8.f) * .009f, .5f, 1.f);
    const float FatigueScale = FMath::Clamp(1.f - Fatigue * .002f, .8f, 1.f);
    return Speeds[FMath::Min<uint8>(Step, 6)] * LoadScale * FatigueScale * SafeInjuryScale;
}

float UAnomaliaVitalsComponent::GetPlannedWalkSpeed() const
{
    const AAnomaliaSurvivor* Survivor = Cast<AAnomaliaSurvivor>(GetOwner());
    if (!Survivor) return 450.f;
    const float LoadKg = Survivor->InventoryComponent ? Survivor->InventoryComponent->GetCurrentWeightKg() : 0.f;
    const float InjuryScale = Survivor->ItemEffectsComponent ? Survivor->ItemEffectsComponent->GetMovementScale() : 1.f;
    const uint8 EffectiveStep = (Stamina <= 0.f && PaceStep >= 5) ? 4 : PaceStep;
    return CalculateTacticalSpeed(EffectiveStep, LoadKg, Survivor->Fatigue, InjuryScale);
}

void UAnomaliaVitalsComponent::RestoreVitals(float SavedStamina, float SavedTemperatureC)
{
    const AAnomaliaSurvivor* Survivor = Cast<AAnomaliaSurvivor>(GetOwner());
    if (!Survivor || !Survivor->HasAuthority() ||
        !FMath::IsFinite(SavedStamina) || !FMath::IsFinite(SavedTemperatureC)) return;

    Stamina = FMath::Clamp(SavedStamina, 0.f, 100.f);
    BodyTemperatureC = FMath::Clamp(SavedTemperatureC, 25.f, 45.f);
    bExhausted = Stamina <= 0.f;
    bSprintRequested = false;
    bIsSprinting = false;
    ApplyMovementSpeed();
    OnVitalsChanged();
}

void UAnomaliaVitalsComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    AAnomaliaSurvivor* Survivor = Cast<AAnomaliaSurvivor>(GetOwner());
    if (!Survivor || DeltaTime <= 0.f) return;
    if (!Survivor->HasAuthority()) { ApplyMovementSpeed(); return; }

    // Avoid a huge drain caused by a hitch/resume from Windows sleep.
    const float Step = FMath::Min(DeltaTime, 0.25f);
    const AAnomaliaGameMode* Rules = Survivor->GetWorld()
        ? Cast<AAnomaliaGameMode>(Survivor->GetWorld()->GetAuthGameMode()) : nullptr;
    const float Ambient = Rules ? Rules->ActiveServerSettings.AmbientTemperatureC : 20.f;

    const float PreviousStamina = Stamina;
    const float PreviousBodyTemperature = BodyTemperatureC;

    // Coarse first-pass physiology: calibrated ambient-to-body equilibrium.
    // No weather volumes, wetness or insulating clothes yet.
    const float TargetTemperature = FMath::Clamp(37.f + (Ambient - 20.f) * 0.08f, 30.f, 43.f);
    BodyTemperatureC = FMath::FInterpConstantTo(BodyTemperatureC, TargetTemperature, Step, 0.02f);

    if (Survivor->Health <= 0.f)
    {
        bSprintRequested = false;
    }
    if (bExhausted && Stamina >= 25.f) bExhausted = false;

    const bool bMoving = Survivor->GetVelocity().SizeSquared2D() > FMath::Square(75.f);
    const float LoadKg = Survivor->InventoryComponent ? Survivor->InventoryComponent->GetCurrentWeightKg() : 0.f;
    const bool bCanSprint = bSprintRequested && !bExhausted && Stamina > 0.f &&
                            Survivor->Health > 0.f && !Survivor->bIsCrouched && LoadKg < 45.f && bMoving;
    if (bCanSprint)
    {
        Stamina = FMath::Max(0.f, Stamina - SprintDrainPerSecond * (1.f + LoadKg * .018f) * Step);
        if (Stamina <= 0.f) bExhausted = true;
    }
    else if (bMoving && PaceStep >= 5 && !Survivor->bIsCrouched)
    {
        // Fast tactical movement is sustainable only for a limited period.
        Stamina = FMath::Max(0.f, Stamina - (PaceStep == 6 ? 3.0f : 1.4f) * (1.f + LoadKg * .012f) * Step);
    }
    else
    {
        const float ItemScale=Survivor->ItemEffectsComponent?Survivor->ItemEffectsComponent->GetStaminaRecoveryScale():1.f;
        const float RecoveryScale = FMath::Clamp(1.f - LoadKg * .008f - Survivor->Fatigue * .003f, .35f, 1.f);
        Stamina = FMath::Min(100.f, Stamina + StaminaRecoveryPerSecond * ItemScale * RecoveryScale * Step);
    }

    const bool bNewSprint = bCanSprint && !bExhausted;
    if (bIsSprinting != bNewSprint)
    {
        bIsSprinting = bNewSprint;
        ApplyMovementSpeed();
    }
    // Apply changing intoxication/pain even when sprint state does not change.
    ApplyMovementSpeed();

    // Temperature damage is authoritative; client profiles cannot set it.
    if (BodyTemperatureC < 35.f || BodyTemperatureC > 40.f)
    {
        Survivor->Health = FMath::Max(0.f, Survivor->Health - 0.15f * Step);
        Survivor->OnSurvivalChanged();
    }

    if (!FMath::IsNearlyEqual(PreviousStamina, Stamina, 0.01f) ||
        !FMath::IsNearlyEqual(PreviousBodyTemperature, BodyTemperatureC, 0.001f))
    {
        OnVitalsChanged();
    }
}

void UAnomaliaVitalsComponent::ApplyMovementSpeed()
{
    AAnomaliaSurvivor* Survivor = Cast<AAnomaliaSurvivor>(GetOwner());
    if (!Survivor || !Survivor->GetCharacterMovement()) return;
    const float TacticalSpeed = GetPlannedWalkSpeed();
    const float Baseline = CalculateTacticalSpeed(4, 0.f, 0.f, 1.f);
    const float LoadKg = Survivor->InventoryComponent ? Survivor->InventoryComponent->GetCurrentWeightKg() : 0.f;
    const float InjuryScale = Survivor->ItemEffectsComponent ? Survivor->ItemEffectsComponent->GetMovementScale() : 1.f;
    // Sprint is the existing independent high-speed mode, not derived from the walk pace step.
    const float Scale = CalculateTacticalSpeed(4, LoadKg, Survivor->Fatigue, InjuryScale) / Baseline;
    UCharacterMovementComponent* Move = Survivor->GetCharacterMovement();
    Move->MaxWalkSpeed = bIsSprinting ? SprintWalkSpeed * Scale : TacticalSpeed;
    Move->MaxWalkSpeedCrouched = TacticalSpeed * .55f;
    Move->MaxAcceleration = 2048.f * FMath::Clamp(Scale, .4f, 1.1f);
    Move->BrakingDecelerationWalking = 2048.f * FMath::Clamp(Scale, .4f, 1.1f);
}

void UAnomaliaVitalsComponent::OnRep_Vitals()
{
    OnVitalsChanged();
}

void UAnomaliaVitalsComponent::OnRep_PaceStep()
{
    PaceStep = FMath::Min<uint8>(PaceStep, 6);
    ApplyMovementSpeed();
    OnVitalsChanged();
}

void UAnomaliaVitalsComponent::OnRep_Sprinting()
{
    ApplyMovementSpeed();
    OnVitalsChanged();
}

void UAnomaliaVitalsComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UAnomaliaVitalsComponent, Stamina);
    DOREPLIFETIME(UAnomaliaVitalsComponent, BodyTemperatureC);
    DOREPLIFETIME(UAnomaliaVitalsComponent, bIsSprinting);
    DOREPLIFETIME(UAnomaliaVitalsComponent, PaceStep);
}
