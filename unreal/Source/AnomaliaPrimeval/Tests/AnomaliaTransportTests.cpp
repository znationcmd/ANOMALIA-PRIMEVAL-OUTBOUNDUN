#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../Vehicles/AnomaliaTransportDynamics.h"
#include "../AnomaliaVehicleCatalog.h"

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
#endif
