#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../Vehicles/AnomaliaZPrigimaliaTransportDynamics.h"
#include "../AnomaliaZPrigimaliaVehicleCatalog.h"
#include "../AnomaliaZPrigimaliaVehiclePawn.h"
#include "../Vehicles/AnomaliaZPrigimaliaTransportMovement.h"
#include "../Vehicles/AnomaliaZPrigimaliaTransportEnvironment.h"
#include "../Vehicles/AnomaliaZPrigimaliaRailCarriage.h"
#include "Components/SplineComponent.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaZPrigimaliaTransportDynamicsTest,"AnomaliaZPrigimalia.Native.TransportDynamics",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaZPrigimaliaTransportDynamicsTest::RunTest(const FString& Parameters)
{
    using namespace AnomaliaZPrigimaliaTransport;
    Settings P; Controls I;
    const Vector F{1,0,0},U{0,0,1};
    TestTrue(TEXT("Unpowered helicopter falls"),Acceleration(Mode::Helicopter,{},F,U,I,P,false,false,0).Z<0);
    TestTrue(TEXT("Powered rotor can hover"),std::abs(Acceleration(Mode::Helicopter,{},F,U,I,P,true,false,0).Z)<0.001);
    TestTrue(TEXT("Plane cannot hover at zero airspeed"),Acceleration(Mode::Plane,{},F,U,I,P,true,false,0).Z<0);
    bool End=false;
    TestEqual(TEXT("Train stops at track end"),RailDistance(990,30,1000,false,End),1000.0);
    TestTrue(TEXT("Track end reported"),End);
    TestEqual(TEXT("Loop wraps reverse movement"),RailDistance(5,-20,1000,true,End),985.0);
    FAnomaliaZPrigimaliaVehicleDefinition D;
    TestTrue(TEXT("Transport aircraft is selectable"),UAnomaliaZPrigimaliaVehicleCatalog::FindVehicleDefinition(FName(TEXT("airplane")),D));
    TestTrue(TEXT("Locomotive is selectable"),UAnomaliaZPrigimaliaVehicleCatalog::FindVehicleDefinition(FName(TEXT("train")),D));
    TestTrue(TEXT("Locomotive uses rail movement"),D.Domain==EAnomaliaZPrigimaliaVehicleDomain::Rail);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaZPrigimaliaMetroConsistTest,"AnomaliaZPrigimalia.Native.MetroConsist",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaZPrigimaliaMetroConsistTest::RunTest(const FString& Parameters)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("Isolated temporary test world"),World)) return false;
    auto* Route=World->SpawnActor<AAnomaliaZPrigimaliaRailTrack>();
    Route->Track->ClearSplinePoints(false);
    for(const FVector Point : {FVector(0,0,160),FVector(10000,0,160),FVector(20000,10000,160),FVector(30000,10000,160)})
        Route->Track->AddSplinePoint(Point,ESplineCoordinateSpace::World,false);
    Route->Track->UpdateSpline();
    auto* Metro=World->SpawnActor<AAnomaliaZPrigimaliaVehiclePawn>();
    TestTrue(TEXT("Metro catalogue selection"),Metro->ConfigureVehicle(TEXT("metro")));
    Metro->SetActorLocation(Route->Track->GetLocationAtDistanceAlongSpline(14000,ESplineCoordinateSpace::World));
    TestTrue(TEXT("Join rail near train"),Metro->TransportMovement->AssignTrack(Route,14000));
    Metro->Tick(.016f);
    int32 Count=0;
    for(TActorIterator<AAnomaliaZPrigimaliaRailCarriage> It(World);It;++It)
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
    for(TActorIterator<AAnomaliaZPrigimaliaRailCarriage> It(World);It;++It)
        TestTrue(TEXT("Changing type destroys owned coaches"),It->IsActorBeingDestroyed());
    World->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaZPrigimaliaCableCabinTest,"AnomaliaZPrigimalia.Native.CableCabin",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaZPrigimaliaCableCabinTest::RunTest(const FString& Parameters)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("Isolated cable test world"),World)) return false;
    auto* Route=World->SpawnActor<AAnomaliaZPrigimaliaRailTrack>();
    Route->Track->ClearSplinePoints(false);
    Route->Track->AddSplinePoint(FVector(0,0,1000),ESplineCoordinateSpace::World,false);
    Route->Track->AddSplinePoint(FVector(10000,0,6000),ESplineCoordinateSpace::World,false);
    Route->Track->UpdateSpline();
    auto* Cabin=World->SpawnActor<AAnomaliaZPrigimaliaVehiclePawn>();
    TestTrue(TEXT("Cable car configuration"),Cabin->ConfigureVehicle(TEXT("cable_car")));
    Cabin->SetActorLocation(Route->Track->GetLocationAtDistanceAlongSpline(100,ESplineCoordinateSpace::World));
    TestTrue(TEXT("Join inclined cable"),Cabin->TransportMovement->AssignTrack(Route,100));
    AnomaliaZPrigimaliaTransport::Controls Input;Input.Throttle=1;
    for(int N=0;N<120;++N) Cabin->TransportMovement->Simulate(1.f/60,Input,true);
    TestTrue(TEXT("Cabin advances up the authored cable"),Cabin->TransportMovement->GetTrackDistance()>100);
    TestTrue(TEXT("Passenger cabin remains level on a slope"),FMath::Abs(Cabin->GetActorRotation().Pitch)<.01&&FMath::Abs(Cabin->GetActorRotation().Roll)<.01);
    Input={};Input.Brake=1;
    for(int N=0;N<120;++N) Cabin->TransportMovement->Simulate(1.f/60,Input,false);
    TestTrue(TEXT("Emergency braking stops cabin"),FMath::Abs(Cabin->TransportMovement->GetRailSpeed())<.01);
    Cabin->ConfigureVehicle(TEXT("train"));
    TestNull(TEXT("Locomotive does not inherit the cable route"),Cabin->TransportMovement->GetRailTrack());
    World->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaZPrigimaliaSeaRegionTest,"AnomaliaZPrigimalia.Native.NavigableSeaRegion",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaZPrigimaliaSeaRegionTest::RunTest(const FString& Parameters)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!TestNotNull(TEXT("Isolated water test world"),World)) return false;
    auto* Sea=World->SpawnActor<AAnomaliaZPrigimaliaNavigableWater>();
    Sea->SetActorLocation(FVector(0,0,-30000));
    Sea->Bounds->SetBoxExtent(FVector(2400000,2400000,30400));
    Sea->SurfaceOffset=30000;
    double Surface=0,Bottom=0;
    TestTrue(TEXT("Sea surface supports surface craft"),Sea->Sample(FVector(0,0,160),Surface,Bottom));
    TestEqual(TEXT("Surface is exactly sea level"),Surface,0.0);
    TestTrue(TEXT("Region covers the generated deep seabed"),Sea->Sample(FVector(0,0,-44000),Surface,Bottom));
    TestFalse(TEXT("No infinite water beyond world bounds"),Sea->Sample(FVector(2400001,0,0),Surface,Bottom));
    TestFalse(TEXT("No floating high above the sea"),Sea->Sample(FVector(0,0,401),Surface,Bottom));
    World->DestroyWorld(false);return true;
}
#endif
