#include "AnomaliaVehicleCatalog.h"
#include "AnomaliaStorageCatalog.h"

namespace
{
    FAnomaliaVehicleDefinition MakeVehicle(const TCHAR* Id, const TCHAR* Label,
        EAnomaliaVehicleDomain Domain, float MaxSpeed, int32 Seats, int32 Storage,
        bool bEmergency = false, bool bMilitary = false)
    {
        FAnomaliaVehicleDefinition Result;
        Result.Id = FName(Id);
        Result.Label = Label;
        Result.Domain = Domain;
        Result.MaxSpeedKmh = MaxSpeed;
        Result.Seats = Seats;
        Result.StorageSlots = UAnomaliaStorageCatalog::GetVehicleCapacity(Result.Id,Storage);
        Result.bEmergencyVehicle = bEmergency;
        Result.bMilitaryVehicle = bMilitary;
        return Result;
    }
}

TArray<FAnomaliaVehicleDefinition> UAnomaliaVehicleCatalog::GetDefaultVehicleCatalog()
{
    using D = EAnomaliaVehicleDomain;
    return {
        MakeVehicle(TEXT("transport_truck"), TEXT("Camion de transport"), D::Ground, 100, 3, 150),
        MakeVehicle(TEXT("farm_tractor"), TEXT("Tracteur agricole"), D::Ground, 35, 2, 45),
        MakeVehicle(TEXT("semi_truck"), TEXT("Poids lourd avec remorque"), D::Ground, 95, 2, 300),
        MakeVehicle(TEXT("quad"), TEXT("Quad"), D::Ground, 95, 2, 10),
        MakeVehicle(TEXT("buggy"), TEXT("Buggy"), D::Ground, 120, 2, 25),
        MakeVehicle(TEXT("snowmobile"), TEXT("Motoneige"), D::Ground, 110, 2, 8),
        MakeVehicle(TEXT("dirt_bike"), TEXT("Moto cross"), D::Ground, 125, 2, 5),
        MakeVehicle(TEXT("motorcycle"), TEXT("Moto"), D::Ground, 190, 2, 6),
        MakeVehicle(TEXT("kart"), TEXT("Karting"), D::Ground, 90, 1, 0),
        MakeVehicle(TEXT("formula_one"), TEXT("Formule 1"), D::Ground, 320, 1, 0),
        MakeVehicle(TEXT("car"), TEXT("Voiture"), D::Ground, 160, 5, 40),
        MakeVehicle(TEXT("suv"), TEXT("SUV"), D::Ground, 150, 7, 70),
        MakeVehicle(TEXT("van"), TEXT("Fourgon"), D::Ground, 125, 3, 100),
        MakeVehicle(TEXT("police"), TEXT("Police"), D::Ground, 180, 5, 35, true),
        MakeVehicle(TEXT("gendarmerie"), TEXT("Gendarmerie"), D::Ground, 180, 5, 35, true),
        MakeVehicle(TEXT("fire_engine"), TEXT("Camion de pompiers"), D::Ground, 110, 6, 120, true),
        MakeVehicle(TEXT("ambulance"), TEXT("Ambulance"), D::Ground, 145, 4, 70, true),
        MakeVehicle(TEXT("armored_van"), TEXT("Fourgon blindé"), D::Ground, 110, 6, 80, false, true),
        MakeVehicle(TEXT("monster_truck"), TEXT("Monster truck"), D::Ground, 115, 2, 20),
        MakeVehicle(TEXT("jetski"), TEXT("Jet ski"), D::Water, 95, 2, 2),
        MakeVehicle(TEXT("zodiac"), TEXT("Zodiaque"), D::Water, 75, 8, 25),
        MakeVehicle(TEXT("boat"), TEXT("Bateau"), D::Water, 65, 8, 50),
        MakeVehicle(TEXT("carrier"), TEXT("Porte-avions"), D::Water, 55, 100, 500, false, true),
        MakeVehicle(TEXT("warship"), TEXT("Navire de guerre"), D::Water, 65, 45, 300, false, true),
        MakeVehicle(TEXT("submarine"), TEXT("Sous-marin"), D::Underwater, 50, 25, 200, false, true),
        MakeVehicle(TEXT("metro"), TEXT("Métro avec trois voitures voyageurs"), D::Rail, 80, 1, 0),
        MakeVehicle(TEXT("train"), TEXT("Locomotive"), D::Rail, 120, 2, 60),
        MakeVehicle(TEXT("airliner"), TEXT("Avion de ligne"), D::Air, 850, 180, 200),
        MakeVehicle(TEXT("airplane"), TEXT("Avion de transport léger"), D::Air, 320, 6, 40),
        MakeVehicle(TEXT("fighter_jet"), TEXT("Avion de chasse"), D::Air, 1500, 2, 10, false, true),
        MakeVehicle(TEXT("attack_helicopter"), TEXT("Helicoptere d'attaque"), D::Air, 310, 2, 25, false, true),
        MakeVehicle(TEXT("transport_helicopter"), TEXT("Helicoptere de transport"), D::Air, 285, 20, 180, false, true)
    };
}

bool UAnomaliaVehicleCatalog::FindVehicleDefinition(FName VehicleId, FAnomaliaVehicleDefinition& OutDefinition)
{
    for (const FAnomaliaVehicleDefinition& Definition : GetDefaultVehicleCatalog())
    {
        if (Definition.Id == VehicleId)
        {
            OutDefinition = Definition;
            return true;
        }
    }
    return false;
}
