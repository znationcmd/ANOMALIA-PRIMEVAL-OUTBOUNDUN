#include "AnomaliaStorageCatalog.h"
namespace
{
    const TMap<FName,FIntPoint>& StorageGrids()
    {
        static const TMap<FName,FIntPoint> Grids={
            {TEXT("jacket_light"),{10,10}}, {TEXT("jacket_military"),{12,15}},
            {TEXT("pants"),{10,8}}, {TEXT("vest_tactical"),{10,10}},
            {TEXT("backpack_small"),{10,10}}, {TEXT("backpack_medium"),{10,15}},
            {TEXT("backpack_large"),{12,15}}, {TEXT("backpack_military"),{12,20}},
            {TEXT("tent_small"),{10,20}}, {TEXT("tent_large"),{20,40}},
            {TEXT("tent_vehicle"),{20,50}}, {TEXT("barrel"),{15,20}}, {TEXT("crate"),{10,15}},
            {TEXT("car"),{20,50}}, {TEXT("suv"),{20,65}}, {TEXT("van"),{40,40}},
            {TEXT("truck"),{50,60}}, {TEXT("motorcycle"),{20,50}},
            {TEXT("airplane"),{20,25}}, {TEXT("helicopter"),{20,25}}, {TEXT("boat"),{20,25}},
            {TEXT("tank"),{50,110}}, {TEXT("military_vehicle"),{50,110}}, {TEXT("civil_vehicle"),{20,50}},
            {TEXT("f1"),{20,25}}, {TEXT("kart"),{30,50}}, {TEXT("quad"),{30,50}},
            {TEXT("snowmobile"),{30,50}}, {TEXT("jet_ski"),{30,50}}, {TEXT("yacht"),{100,100}},
            {TEXT("dinosaur"),{1000,100}},
            // Defaults for requested variants without a specified reference capacity.
            {TEXT("tent_medium"),{20,20}}, {TEXT("tent_military"),{20,40}},
            {TEXT("cabinet"),{15,20}}, {TEXT("safe"),{10,15}}, {TEXT("shipping_container"),{20,50}}
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
