#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaSurvivor.h"
#include "../AnomaliaVitalsComponent.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaTacticalSpeedTest,
    "Anomalia.Native.TacticalMovement.SpeedLoadFatigueAndCrouch",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAnomaliaTacticalSpeedTest::RunTest(const FString&)
{
    const float Normal = UAnomaliaVitalsComponent::CalculateTacticalSpeed(4, 0.f, 0.f, 1.f);
    const float Light = UAnomaliaVitalsComponent::CalculateTacticalSpeed(4, 8.f, 0.f, 1.f);
    const float Heavy = UAnomaliaVitalsComponent::CalculateTacticalSpeed(4, 35.f, 0.f, 1.f);
    TestTrue(TEXT("Normal pace is 450 cm/s"), FMath::IsNearlyEqual(Normal,450.f));
    TestTrue(TEXT("Lightweight equipment does not penalize"), FMath::IsNearlyEqual(Normal,Light));
    TestTrue(TEXT("Real load reduces walking speed"),Heavy<Normal);
    TestTrue(TEXT("Fatigue reduces heavy-loaded speed"),UAnomaliaVitalsComponent::CalculateTacticalSpeed(4,35.f,80.f,1.f)<Heavy);
    TestTrue(TEXT("Injury effects further reduce speed"),UAnomaliaVitalsComponent::CalculateTacticalSpeed(4,35.f,80.f,.6f)<
        UAnomaliaVitalsComponent::CalculateTacticalSpeed(4,35.f,80.f,1.f));
    TestTrue(TEXT("Lowest tactical pace is slower"),UAnomaliaVitalsComponent::CalculateTacticalSpeed(0,0.f,0.f,1.f)<Normal);
    TestTrue(TEXT("Highest tactical pace is faster"),UAnomaliaVitalsComponent::CalculateTacticalSpeed(6,0.f,0.f,1.f)>Normal);
    TestTrue(TEXT("Invalid pace is bounded"),FMath::IsNearlyEqual(
        UAnomaliaVitalsComponent::CalculateTacticalSpeed(255,0.f,0.f,1.f),
        UAnomaliaVitalsComponent::CalculateTacticalSpeed(6,0.f,0.f,1.f)));
    UWorld* World = UWorld::CreateWorld(EWorldType::Game,false);
    if (!TestNotNull(TEXT("Tactical test world"),World)) return false;
    AAnomaliaSurvivor* Survivor = World->SpawnActor<AAnomaliaSurvivor>();
    if (TestNotNull(TEXT("Actual game survivor"),Survivor))
    {
        TestNotNull(TEXT("Uses existing stamina component"),Survivor->VitalsComponent);
        TestTrue(TEXT("Native crouch supported"),Survivor->GetCharacterMovement()->NavAgentProps.bCanCrouch);
        TestTrue(TEXT("Crouch has physically lower capsule"),Survivor->GetCharacterMovement()->CrouchedHalfHeight<
            Survivor->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight());
        TestTrue(TEXT("Tactical speed drives actual character movement"),
            FMath::IsNearlyEqual(Survivor->VitalsComponent->GetPlannedWalkSpeed(),Normal));
    }
    World->DestroyWorld(false);
    return true;
}
#endif
