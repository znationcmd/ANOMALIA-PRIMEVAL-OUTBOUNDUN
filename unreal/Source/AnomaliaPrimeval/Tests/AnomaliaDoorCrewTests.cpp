#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../AnomaliaDoorActor.h"
#include "../AnomaliaVehiclePawn.h"
#include "../AnomaliaSurvivor.h"
#include "Components/BoxComponent.h"
#include "Components/SceneComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"

namespace {
struct FInteractionWorld {
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    ~FInteractionWorld(){if(World)World->DestroyWorld(false);}
    AActor* Box(FVector Centre,FVector Extent) {
        auto* A=World->SpawnActor<AActor>();
        auto* B=NewObject<UBoxComponent>(A);A->SetRootComponent(B);
        B->SetBoxExtent(Extent);B->SetCollisionProfileName(TEXT("BlockAll"));
        B->RegisterComponent();A->SetActorLocation(Centre);return A;
    }
    AAnomaliaSurvivor* Player(FVector Location) {
        auto* S=World->SpawnActor<AAnomaliaSurvivor>();S->SetActorLocation(Location);
        auto* C=World->SpawnActor<APlayerController>();C->Possess(S);return S;
    }
};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaDoorLeafTest,"Anomalia.Native.DoorLeafAuthorityAndCollision",
 EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FAnomaliaDoorLeafTest::RunTest(const FString&) {
    FInteractionWorld T;if(!TestNotNull(TEXT("Temporary physics world"),T.World))return false;
    auto* D=T.World->SpawnActor<AAnomaliaDoorActor>();
    auto* S=T.Player(FVector(60,-180,88));
    TestTrue(TEXT("Closed leaf blocks the doorway"),D->LeafCollision->GetCollisionEnabled()!=ECollisionEnabled::NoCollision);
    TestTrue(TEXT("Server can lock door"),D->SetLockedOnServer(true));
    TestFalse(TEXT("Locked door cannot open"),D->TryToggle(S));
    D->SetLockedOnServer(false);S->SetActorLocation(FVector(0,-1000,88));
    TestFalse(TEXT("Remote interaction refused"),D->TryToggle(S));
    S->SetActorLocation(FVector(60,-180,88));
    auto* Wall=T.Box(FVector(60,-90,100),FVector(100,10,150));
    TestFalse(TEXT("Wall blocks door interaction"),D->TryToggle(S));Wall->Destroy();
    TestTrue(TEXT("Nearby unlocked interaction accepted"),D->TryToggle(S));
    for(int I=0;I<90;++I)D->Tick(1.f/60);
    TestTrue(TEXT("Leaf opens ninety degrees about its hinge"),FMath::IsNearlyEqual(D->DoorAngleDegrees,90.f,.01f));
    TestTrue(TEXT("Leaf centre follows hinge arc"),D->LeafCollision->GetComponentLocation().Equals(FVector(0,59,109),.1f));
    FHitResult Hit;FCollisionQueryParams Q;Q.AddIgnoredActor(S);
    TestFalse(TEXT("Open doorway ray is clear"),T.World->LineTraceSingleByChannel(Hit,FVector(60,-100,100),FVector(60,100,100),ECC_Pawn,Q));
    // A player/object in the closing arc must not be crushed by a teleporting panel.
    S->SetActorLocation(FVector(180,120,88));
    T.Box(FVector(32,49,109),FVector(10,10,90));
    TestTrue(TEXT("Closing request accepted before sweep check"),D->TryToggle(S));
    for(int I=0;I<90;++I)D->Tick(1.f/60);
    TestTrue(TEXT("Closing arc obstruction reported"),D->bObstructed);
    TestTrue(TEXT("Blocked leaf remains short of closed pose"),D->DoorAngleDegrees>1.f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaCrewGeometryTest,"Anomalia.Native.CrewEntryAndSafeExitGeometry",
 EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FAnomaliaCrewGeometryTest::RunTest(const FString&) {
    FInteractionWorld T;if(!TestNotNull(TEXT("Temporary crew world"),T.World))return false;
    T.Box(FVector(0,0,-50),FVector(3000,3000,50));
    auto* V=T.World->SpawnActor<AAnomaliaVehiclePawn>();V->SetActorLocation(FVector(0,0,160));
    auto* S=T.Player(FVector(0,300,90));
    TestTrue(TEXT("Clear legacy entry remains compatible"),V->CanEnterFrom(S));
    auto* Wall=T.Box(FVector(0,230,150),FVector(120,10,150));
    TestFalse(TEXT("Cannot enter through a wall"),V->CanEnterFrom(S));Wall->Destroy();
    V->bUseAuthoredDriverPoints=true;V->DriverEntryPoint->SetRelativeLocation(FVector(900,0,0));
    TestFalse(TEXT("Authored entry replaces vehicle-centre interaction"),V->CanEnterFrom(S));
    S->SetActorLocation(FVector(900,180,90));
    TestTrue(TEXT("Real door marker is interactable at model-specific location"),V->CanEnterFrom(S));
    FVector Exit;V->DriverExitPoint->SetRelativeLocation(FVector(0,350,-160));
    TestTrue(TEXT("Authored clear floor exit found"),V->FindSafeDriverExit(S,Exit));
    TestTrue(TEXT("Exit feet rest above traced ground"),FMath::IsNearlyEqual(Exit.Z,S->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()+2.f,.1f));
    auto* Obstacle=T.Box(FVector(0,350,150),FVector(100,100,150));
    TestFalse(TEXT("Blocked authored exit does not teleport into wall or choose arbitrary side"),V->FindSafeDriverExit(S,Exit));Obstacle->Destroy();
    V->DriverExitPoint->SetRelativeLocation(FVector(0,100,-160));
    TestFalse(TEXT("Exit cannot overlap the vehicle's root"),V->FindSafeDriverExit(S,Exit));
    V->DriverExitPoint->SetRelativeLocation(FVector(0,5000,-160));
    TestFalse(TEXT("No floor means no safe standing exit"),V->FindSafeDriverExit(S,Exit));
    return true;
}
#endif
