#include "AnomaliaStorageCatalog.h"
namespace
{
    const TMap<FName,FIntPoint>& StorageGrids()
    {
        static const TMap<FName,FIntPoint> Grids={
            // Latest approved design: ten times the TOTAL reference cells; weight is independent.
            {TEXT("jacket_light"),{10,20}}, {TEXT("jacket_military"),{10,40}},
            {TEXT("pants"),{10,20}}, {TEXT("vest_tactical"),{10,30}},
            {TEXT("backpack_small"),{10,35}}, {TEXT("backpack_medium"),{15,42}},
            {TEXT("backpack_large"),{20,45}}, {TEXT("backpack_military"),{20,60}},
            {TEXT("tent_small"),{20,50}}, {TEXT("tent_medium"),{40,50}},
            {TEXT("tent_large"),{50,80}}, {TEXT("tent_military"),{50,80}},
            {TEXT("tent_vehicle"),{50,100}}, {TEXT("barrel"),{30,50}},
            {TEXT("crate"),{20,25}}, {TEXT("chest"),{20,50}}, {TEXT("cabinet"),{20,50}},
            {TEXT("motorcycle"),{10,20}}, {TEXT("dirt_bike"),{10,10}},
            {TEXT("motorcycle_touring"),{20,30}}, {TEXT("quad"),{20,20}},
            {TEXT("buggy"),{20,40}}, {TEXT("snowmobile"),{20,20}},
            {TEXT("car"),{20,25}}, {TEXT("suv"),{30,50}}, {TEXT("van"),{50,60}},
            {TEXT("truck"),{50,100}},
            {TEXT("jet_ski"),{10,20}}, {TEXT("zodiac"),{20,50}},
            {TEXT("boat"),{30,50}}, {TEXT("fishing_boat"),{50,60}},
            {TEXT("yacht"),{60,100}}, {TEXT("superyacht"),{100,120}},
            {TEXT("submarine"),{80,100}}, {TEXT("carrier"),{100,300}},
            {TEXT("airplane"),{20,50}}, {TEXT("transport_airplane"),{80,100}},
            {TEXT("fighter_jet"),{20,20}}, {TEXT("helicopter"),{20,50}},
            {TEXT("transport_helicopter"),{60,100}}, {TEXT("attack_helicopter"),{20,50}},
            {TEXT("armored_vehicle"),{40,50}}, {TEXT("tank"),{30,50}},
            {TEXT("military_truck"),{60,100}}, {TEXT("missile_vehicle"),{40,50}},
            // Retained generic IDs: explicit configurable defaults for unclassified models.
            {TEXT("military_vehicle"),{40,50}}, {TEXT("civil_vehicle"),{20,25}},
            {TEXT("f1"),{20,25}}, {TEXT("kart"),{10,10}},
            {TEXT("dinosaur"),{20,25}},
            {TEXT("dino_ground_small"),{10,20}}, {TEXT("dino_ground_medium"),{20,25}},
            {TEXT("dino_ground_large"),{20,50}}, {TEXT("dino_ground_giant"),{40,50}},
            {TEXT("dino_flying_small"),{10,20}}, {TEXT("dino_flying_medium"),{20,25}},
            {TEXT("dino_flying_large"),{20,50}},
            {TEXT("dino_aquatic_small"),{15,20}}, {TEXT("dino_aquatic_medium"),{20,40}},
            {TEXT("dino_aquatic_large"),{30,50}}, {TEXT("dino_aquatic_giant"),{50,60}},
            // Additional requested storage: design defaults until individually configured.
            {TEXT("refrigerator"),{20,50}}, {TEXT("freezer"),{40,50}},
            {TEXT("gun_cabinet"),{20,50}}, {TEXT("safe"),{20,50}},
            {TEXT("shipping_container"),{100,100}}, {TEXT("warehouse"),{100,300}},
            {TEXT("building_storage"),{100,100}}
        };
        return Grids;
    }
}
bool UAnomaliaStorageCatalog::GetGrid(FName PresetId,FIntPoint& OutGrid)
{
    OutGrid=FIntPoint::ZeroValue;
    if(const auto* Grid=StorageGrids().Find(PresetId)) { OutGrid=*Grid;return true; }
    return false;
}
TArray<FName> UAnomaliaStorageCatalog::GetPresetIds()
{ TArray<FName> Ids;StorageGrids().GetKeys(Ids);Ids.Sort(FNameLexicalLess());return Ids; }

int32 UAnomaliaStorageCatalog::GetVehicleCapacity(FName VehicleId,int32 ReferenceCells)
{
    static const TMap<FName,FName> Aliases={
        {TEXT("transport_truck"),TEXT("truck")}, {TEXT("semi_truck"),TEXT("truck")},
        {TEXT("armored_van"),TEXT("armored_vehicle")}, {TEXT("jetski"),TEXT("jet_ski")},
        {TEXT("formula_one"),TEXT("f1")}
    };
    const FName* Alias=Aliases.Find(VehicleId);
    FIntPoint Grid;
    if(GetGrid(Alias ? *Alias : VehicleId,Grid)) return Grid.X*Grid.Y;
    // Input is always the unscaled catalogue reference, never a saved/previously scaled capacity.
    return static_cast<int32>(FMath::Clamp(static_cast<int64>(ReferenceCells)*10,static_cast<int64>(0),static_cast<int64>(MaxCells)));
}
