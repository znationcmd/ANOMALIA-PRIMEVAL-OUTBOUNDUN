#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaZPrigimaliaCryoSubsystem.h"
#include "Engine/World.h"
#include <limits>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaZPrigimaliaCryoStorageTest,"AnomaliaZPrigimalia.Native.CryoStorage",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaZPrigimaliaCryoStorageTest::RunTest(const FString& Parameters)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("Isolated test world"),World)) return false;
    auto* Storage=NewObject<UAnomaliaZPrigimaliaCryoSubsystem>(World);
    TestFalse(TEXT("Reject infinite position"),Storage->RegisterTerminal(TEXT("invalid"),TEXT("owner"),
        FVector(std::numeric_limits<double>::infinity(),0,0)));
    TestFalse(TEXT("Reject NaN position"),Storage->RegisterTerminal(TEXT("nan"),TEXT("owner"),
        FVector(0,std::numeric_limits<double>::quiet_NaN(),0)));
    TestTrue(TEXT("Register finite terminal"),Storage->RegisterTerminal(TEXT("first"),TEXT("owner"),FVector::ZeroVector));
    TestTrue(TEXT("Register another terminal"),Storage->RegisterTerminal(TEXT("second"),TEXT("owner"),FVector::ZeroVector));
    FAnomaliaZPrigimaliaCryoCreature Creature;
    Creature.Id=TEXT("creature");Creature.OwnerId=TEXT("owner");Creature.bTamed=true;
    TestFalse(TEXT("Unauthorized player cannot capture"),Storage->CaptureCreature(TEXT("first"),TEXT("intruder"),false,Creature,false,0,false));
    TestTrue(TEXT("Owner captures once"),Storage->CaptureCreature(TEXT("first"),TEXT("owner"),false,Creature,false,0,false));
    TestFalse(TEXT("Prevent duplication across terminals"),Storage->CaptureCreature(TEXT("second"),TEXT("owner"),false,Creature,false,0,false));
    FAnomaliaZPrigimaliaCryoCreature Released;
    TestFalse(TEXT("Unauthorized player cannot release"),Storage->ReleaseCreature(TEXT("first"),Creature.Id,TEXT("intruder"),false,true,Released));
    TestFalse(TEXT("Failed spawn preserves stored creature"),Storage->ReleaseCreature(TEXT("first"),Creature.Id,TEXT("owner"),false,false,Released));
    TestTrue(TEXT("Validated spawn releases creature"),Storage->ReleaseCreature(TEXT("first"),Creature.Id,TEXT("owner"),false,true,Released));
    TestFalse(TEXT("Released creature is no longer stored"),Released.bStored);
    TestFalse(TEXT("Cannot release twice"),Storage->ReleaseCreature(TEXT("first"),Creature.Id,TEXT("owner"),false,true,Released));
    World->DestroyWorld(false);
    return true;
}
#endif
