#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaZPrigimaliaDogCompanion.h"
#include "../AnomaliaZPrigimaliaSurvivor.h"
#include "Engine/World.h"
#include "Engine/DamageEvents.h"
#include "GameFramework/PlayerController.h"
#include <limits>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaZPrigimaliaDogAuthorityTest,"AnomaliaZPrigimalia.Native.DogOwnershipAndNonLethalDamage",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaZPrigimaliaDogAuthorityTest::RunTest(const FString& Parameters)
{
 auto* World=UWorld::CreateWorld(EWorldType::Game,false);if(!TestNotNull(TEXT("Private dog rules world"),World))return false;
 auto* User=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();auto* Other=World->SpawnActor<AAnomaliaZPrigimaliaSurvivor>();
 auto* PC=World->SpawnActor<APlayerController>();PC->Possess(User);
 auto* Dog=World->SpawnActor<AAnomaliaZPrigimaliaDogCompanion>();Dog->SetActorLocation(User->GetActorLocation()+FVector(100,0,0));
 TestFalse(TEXT("Unassigned dog refuses a command"),Dog->RequestCommand(EAnomaliaZPrigimaliaDogCommand::Follow));
 TestTrue(TEXT("Authority assigns the actual survivor"),Dog->AssignSurvivor(User));
 TestFalse(TEXT("Another survivor cannot steal ownership"),Dog->AssignSurvivor(Other));
 TestTrue(TEXT("Follow command accepted for live possessed owner"),Dog->RequestCommand(EAnomaliaZPrigimaliaDogCommand::Follow));
 TestTrue(TEXT("Follow state is authoritative"),Dog->Command==EAnomaliaZPrigimaliaDogCommand::Follow);
 TestFalse(TEXT("Absent sit animation is not advertised"),Dog->IsCommandAvailable(EAnomaliaZPrigimaliaDogCommand::Sit));
 TestFalse(TEXT("Absent lie animation is not advertised"),Dog->IsCommandAvailable(EAnomaliaZPrigimaliaDogCommand::LieDown));
 TestFalse(TEXT("Absent attack animation is not advertised"),Dog->RequestCommand(EAnomaliaZPrigimaliaDogCommand::Attack));
 FDamageEvent Event;
 Dog->TakeDamage(90,Event,nullptr,nullptr);TestTrue(TEXT("Serious injury is represented"),Dog->bInjured);
 Dog->TakeDamage(10000,Event,nullptr,nullptr);TestEqual(TEXT("Lethal hit leaves one health"),Dog->Health,1.f);
 TestFalse(TEXT("Dog is not destroyed by lethal damage"),Dog->IsActorBeingDestroyed());
 TestEqual(TEXT("Repeated lethal hit cannot kill"),Dog->TakeDamage(10000,Event,nullptr,nullptr),0.f);
 TestEqual(TEXT("Negative damage cannot heal"),Dog->TakeDamage(-25,Event,nullptr,nullptr),0.f);
 TestEqual(TEXT("NaN damage is rejected"),Dog->TakeDamage(std::numeric_limits<float>::quiet_NaN(),Event,nullptr,nullptr),0.f);
 TestEqual(TEXT("Rejected damage preserves health"),Dog->Health,1.f);
 TestFalse(TEXT("NaN treatment is rejected"),Dog->TreatInjury(std::numeric_limits<float>::quiet_NaN()));
 TestTrue(TEXT("Trusted treatment restores health"),Dog->TreatInjury(50));TestEqual(TEXT("Treatment bounded"),Dog->Health,51.f);
 TestFalse(TEXT("Recovered dog no longer marked injured"),Dog->bInjured);
 auto* StayingDog=World->SpawnActor<AAnomaliaZPrigimaliaDogCompanion>();StayingDog->SetActorLocation(User->GetActorLocation()+FVector(200,0,0));StayingDog->AssignSurvivor(User);
 TestTrue(TEXT("Stay command accepted"),StayingDog->RequestCommand(EAnomaliaZPrigimaliaDogCommand::Stay));
 World->DestroyWorld(false);return true;
}
#endif
