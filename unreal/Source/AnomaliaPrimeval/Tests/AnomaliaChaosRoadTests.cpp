#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../Vehicles/AnomaliaChaosRoadVehicle.h"
#include "../Vehicles/AnomaliaVehiclePanelComponent.h"
#include "../AnomaliaSurvivor.h"
#include "ChaosWheeledVehicleMovementComponent.h"
#include "Components/SphereComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/FloatingPawnMovement.h"
#include "GameFramework/PlayerController.h"
#include <limits>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaChaosRoadTest,"Anomalia.Native.ChaosRoadConfiguration",
 EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FAnomaliaChaosRoadTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("Isolated native world"),World))return false;
    auto* Car=World->SpawnActor<AAnomaliaChaosRoadVehicle>();
    auto* Survivor=World->SpawnActor<AAnomaliaSurvivor>();
    auto* Controller=World->SpawnActor<APlayerController>(); Controller->Possess(Survivor);
    TestTrue(TEXT("Real Chaos component is the movement provider"),Car->GetMovementComponent()==Car->ChaosMovement);
    TestTrue(TEXT("Skeletal chassis is collision root"),Car->GetRootComponent()==Car->Chassis);
    TestNotNull(TEXT("Separate driver door component is available"),Car->DriverDoor.Get());
    TestFalse(TEXT("Door without real art refuses interaction"),Car->DriverDoor->TryToggle(Survivor));
    auto* Wheel=NewObject<UAnomaliaRoadFrontWheel>();
    TestEqual(TEXT("Engine conversion preserves calibrated spring stiffness"),Wheel->GetPhysicsSuspensionConfig().SpringRate,45000.f);
    TestFalse(TEXT("No rig does not become a fake playable car"),Car->IsChaosDriveReady());
    TestFalse(TEXT("Parked engine starts switched off"),Car->bEngineRunning);
    TestFalse(TEXT("Non-driver cannot start the engine"),Car->SetEngineRunningOnServer(Controller,true));
    TestFalse(TEXT("No rig refuses entry before hiding survivor"),Car->EnterVehicle(Controller,Survivor));
    TestTrue(TEXT("Entry failure retains original survivor possession"),Controller->GetPawn()==Survivor);
    TestFalse(TEXT("Unpossessed car rejects server control request"),Car->SetDriverControlsOnServer(Controller,1,0,0));
    TestFalse(TEXT("Nonfinite commands rejected"),Car->SetDriverControlsOnServer(Controller,std::numeric_limits<float>::quiet_NaN(),0,0));
    TestEqual(TEXT("Unused sphere cannot collide with actual chassis"),Car->Collision->GetCollisionEnabled(),ECollisionEnabled::NoCollision);
    TestFalse(TEXT("Legacy floating movement remains stopped"),Car->Movement->IsComponentTickEnabled());
    World->DestroyWorld(false);
    return true;
}
#endif
