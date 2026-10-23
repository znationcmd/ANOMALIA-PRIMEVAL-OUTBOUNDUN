#include "AnomaliaEquipmentSlotsLibrary.h"
#include "AnomaliaStorageCatalog.h"

bool UAnomaliaEquipmentSlotsLibrary::CanEquip(EAnomaliaEquipmentSlot Slot,const FAnomaliaEquipmentItem& Item,bool Backpack,bool Belt,bool Vest)
{
 if(Item.ItemId.IsNone()||Item.Category.IsNone()||!FMath::IsFinite(Item.WeightKg)||Item.WeightKg<0.f)return false;
 const FName C=Item.Category;
 switch(Slot)
 {
 case EAnomaliaEquipmentSlot::Vest: return C==TEXT("vest");
 case EAnomaliaEquipmentSlot::Top: return C==TEXT("top");
 case EAnomaliaEquipmentSlot::Belt: return C==TEXT("belt");
 case EAnomaliaEquipmentSlot::Legs: return C==TEXT("legs");
 case EAnomaliaEquipmentSlot::Back: return C==TEXT("backpack");
 case EAnomaliaEquipmentSlot::Head: return C==TEXT("head");
 case EAnomaliaEquipmentSlot::Face: return C==TEXT("face");
 case EAnomaliaEquipmentSlot::Eyes: return C==TEXT("eyes");
 case EAnomaliaEquipmentSlot::Gloves: return C==TEXT("gloves");
 case EAnomaliaEquipmentSlot::Feet: return C==TEXT("feet");
 case EAnomaliaEquipmentSlot::Armband: return C==TEXT("armband");
 case EAnomaliaEquipmentSlot::ShoulderPrimary:
 case EAnomaliaEquipmentSlot::ShoulderSecondary: return C==TEXT("long_weapon")||C==TEXT("long_tool");
 case EAnomaliaEquipmentSlot::BackpackTool: return Backpack&&(C==TEXT("tool")||C==TEXT("long_tool"));
 case EAnomaliaEquipmentSlot::BackpackStrapLeft:
 case EAnomaliaEquipmentSlot::BackpackStrapRight: return Backpack&&(C==TEXT("long_weapon")||C==TEXT("long_tool")||C==TEXT("tool"));
 case EAnomaliaEquipmentSlot::BeltHolster: return Belt&&C==TEXT("holster");
 case EAnomaliaEquipmentSlot::BeltKnife: return Belt&&C==TEXT("knife");
 case EAnomaliaEquipmentSlot::VestPouches: return Vest&&C==TEXT("pouches");
 case EAnomaliaEquipmentSlot::Hands: return true;
 default: return false;
 }
}

FIntPoint UAnomaliaEquipmentSlotsLibrary::SuggestedCargoGrid(FName Garment)
{
 FName Preset=Garment;
 if(Garment==TEXT("shirt")||Garment==TEXT("jacket"))Preset=TEXT("jacket_light");
 else if(Garment==TEXT("coat"))Preset=TEXT("jacket_military");
 else if(Garment==TEXT("jeans"))Preset=TEXT("pants");
 else if(Garment==TEXT("vest"))Preset=TEXT("vest_tactical");
 else if(Garment==TEXT("backpack")||Garment==TEXT("bag"))Preset=TEXT("backpack_small");
 FIntPoint Grid;
 UAnomaliaStorageCatalog::GetGrid(Preset,Grid);
 return Grid;
}

FName UAnomaliaEquipmentSlotsLibrary::SlotContainerId(EAnomaliaEquipmentSlot Slot)
{
 switch(Slot)
 {
 case EAnomaliaEquipmentSlot::Vest: return TEXT("equip_vest");
 case EAnomaliaEquipmentSlot::Top: return TEXT("equip_top");
 case EAnomaliaEquipmentSlot::Belt: return TEXT("equip_belt");
 case EAnomaliaEquipmentSlot::Legs: return TEXT("equip_legs");
 case EAnomaliaEquipmentSlot::Back: return TEXT("equip_back");
 case EAnomaliaEquipmentSlot::Head: return TEXT("equip_head");
 case EAnomaliaEquipmentSlot::Face: return TEXT("equip_face");
 case EAnomaliaEquipmentSlot::Eyes: return TEXT("equip_eyes");
 case EAnomaliaEquipmentSlot::Gloves: return TEXT("equip_gloves");
 case EAnomaliaEquipmentSlot::Feet: return TEXT("equip_feet");
 case EAnomaliaEquipmentSlot::Armband: return TEXT("equip_armband");
 case EAnomaliaEquipmentSlot::ShoulderPrimary: return TEXT("attach_shoulder_1");
 case EAnomaliaEquipmentSlot::ShoulderSecondary: return TEXT("attach_shoulder_2");
 case EAnomaliaEquipmentSlot::BackpackTool: return TEXT("attach_backpack_tool");
 case EAnomaliaEquipmentSlot::BackpackStrapLeft: return TEXT("attach_backpack_strap_1");
 case EAnomaliaEquipmentSlot::BackpackStrapRight: return TEXT("attach_backpack_strap_2");
 case EAnomaliaEquipmentSlot::BeltHolster: return TEXT("attach_belt_holster");
 case EAnomaliaEquipmentSlot::BeltKnife: return TEXT("attach_belt_knife");
 case EAnomaliaEquipmentSlot::VestPouches: return TEXT("attach_vest_pouches");
 case EAnomaliaEquipmentSlot::Hands: return TEXT("hands");
 default: return NAME_None;
 }
}
