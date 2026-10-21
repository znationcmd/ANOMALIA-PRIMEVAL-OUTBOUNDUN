#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../Vehicles/AnomaliaTransportDynamics.h"
#include "../AnomaliaVehicleCatalog.h"
#include "../AnomaliaVehiclePawn.h"
#include "../Vehicles/AnomaliaTransportMovement.h"
#include "../Vehicles/AnomaliaTransportEnvironment.h"
#include "../Vehicles/AnomaliaRailCarriage.h"
#include "Components/SplineComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaTransportDynamicsTest,"Anomalia.Native.TransportDynamics",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaTransportDynamicsTest::RunTest(const FString& Parameters)
{
    using namespace AnomaliaTransport;
    Settings P; Controls I;
    const Vector F{1,0,0},U{0,0,1};
    TestTrue(TEXT("Unpowered helicopter falls"),Acceleration(Mode::Helicopter,{},F,U,I,P,false,false,0).Z<0);
    TestTrue(TEXT("Powered rotor can hover"),std::abs(Acceleration(Mode::Helicopter,{},F,U,I,P,true,false,0).Z)<0.001);
    TestTrue(TEXT("Plane cannot hover at zero airspeed"),Acceleration(Mode::Plane,{},F,U,I,P,true,false,0).Z<0);
    bool End=false;
    TestEqual(TEXT("Train stops at track end"),RailDistance(990,30,1000,false,End),1000.0);
    TestTrue(TEXT("Track end reported"),End);
    TestEqual(TEXT("Loop wraps reverse movement"),RailDistance(5,-20,1000,true,End),985.0);
    FAnomaliaVehicleDefinition D;
    TestTrue(TEXT("Transport aircraft is selectable"),UAnomaliaVehicleCatalog::FindVehicleDefinition(FName(TEXT("airplane")),D));
    TestTrue(TEXT("Locomotive is selectable"),UAnomaliaVehicleCatalog::FindVehicleDefinition(FName(TEXT("train")),D));
    TestTrue(TEXT("Locomotive uses rail movement"),D.Domain==EAnomaliaVehicleDomain::Rail);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaMetroConsistTest,"Anomalia.Native.MetroConsist",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaMetroConsistTest::RunTest(const FString& Parameters)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("Isolated temporary test world"),World)) return false;
    World->InitializeNewWorld(UWorld::InitializationValues().AllowAudioPlayback(false).CreatePhysicsScene(true).RequiresHitProxies(false).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false).SetTransactional(false));
    auto* Route=World->SpawnActor<AAnomaliaRailTrack>();
    Route->Track->ClearSplinePoints(false);
    for(const FVector Point : {FVector(0,0,160),FVector(10000,0,160),FVector(20000,10000,160),FVector(30000,10000,160)})
        Route->Track->AddSplinePoint(Point,ESplineCoordinateSpace::World,false);
    Route->Track->UpdateSpline();
    auto* Metro=World->SpawnActor<AAnomaliaVehiclePawn>();
    TestTrue(TEXT("Metro catalogue selection"),Metro->ConfigureVehicle(TEXT("metro")));
    Metro->SetActorLocation(Route->Track->GetLocationAtDistanceAlongSpline(14000,ESplineCoordinateSpace::World));
    TestTrue(TEXT("Join rail near train"),Metro->TransportMovement->AssignTrack(Route,14000));
    Metro->Tick(.016f);
    int32 Count=0;
    for(TActorIterator<AAnomaliaRailCarriage> It(World);It;++It)
    {
        ++Count;TestEqual(TEXT("Coach belongs to lead"),It->GetOwner(),static_cast<AActor*>(Metro));
        const FVector Actual=It->GetActorLocation();bool Matches=false;
        for(int32 Index=1;Index<=3;++Index)
            Matches|=Actual.Equals(Route->Track->GetLocationAtDistanceAlongSpline(14000-1850*Index,ESplineCoordinateSpace::World),1.f);
        TestTrue(TEXT("Coach follows curved route at its own distance"),Matches);
        TestFalse(TEXT("Valid coach visible"),It->IsHidden());
    }
    TestEqual(TEXT("Three trailing coaches"),Count,3);
    Metro->ConfigureVehicle(TEXT("train"));Metro->Tick(.016f);
    for(TActorIterator<AAnomaliaRailCarriage> It(World);It;++It)
        TestTrue(TEXT("Changing type destroys owned coaches"),It->IsActorBeingDestroyed());
    World->DestroyWorld(false);return true;
}
#endif
