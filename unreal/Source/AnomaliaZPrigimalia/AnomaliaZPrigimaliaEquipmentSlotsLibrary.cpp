#include "AnomaliaZPrigimaliaEquipmentSlotsLibrary.h"
#include "AnomaliaZPrigimaliaStorageCatalog.h"

bool UAnomaliaZPrigimaliaEquipmentSlotsLibrary::CanEquip(EAnomaliaZPrigimaliaEquipmentSlot Slot,const FAnomaliaZPrigimaliaEquipmentItem& Item,bool Backpack,bool Belt,bool Vest)
{
 if(Item.ItemId.IsNone()||Item.Category.IsNone()||!FMath::IsFinite(Item.WeightKg)||Item.WeightKg<0.f)return false;
 const FName C=Item.Category;
 switch(Slot)
 {
 case EAnomaliaZPrigimaliaEquipmentSlot::Vest: return C==TEXT("vest");
 case EAnomaliaZPrigimaliaEquipmentSlot::Top: return C==TEXT("top");
 case EAnomaliaZPrigimaliaEquipmentSlot::Belt: return C==TEXT("belt");
 case EAnomaliaZPrigimaliaEquipmentSlot::Legs: return C==TEXT("legs");
 case EAnomaliaZPrigimaliaEquipmentSlot::Back: return C==TEXT("backpack");
 case EAnomaliaZPrigimaliaEquipmentSlot::Head: return C==TEXT("head");
 case EAnomaliaZPrigimaliaEquipmentSlot::Face: return C==TEXT("face");
 case EAnomaliaZPrigimaliaEquipmentSlot::Eyes: return C==TEXT("eyes");
 case EAnomaliaZPrigimaliaEquipmentSlot::Gloves: return C==TEXT("gloves");
 case EAnomaliaZPrigimaliaEquipmentSlot::Feet: return C==TEXT("feet");
 case EAnomaliaZPrigimaliaEquipmentSlot::Armband: return C==TEXT("armband");
 case EAnomaliaZPrigimaliaEquipmentSlot::ShoulderPrimary:
 case EAnomaliaZPrigimaliaEquipmentSlot::ShoulderSecondary: return C==TEXT("long_weapon")||C==TEXT("long_tool");
 case EAnomaliaZPrigimaliaEquipmentSlot::BackpackTool: return Backpack&&(C==TEXT("tool")||C==TEXT("long_tool"));
 case EAnomaliaZPrigimaliaEquipmentSlot::BackpackStrapLeft:
 case EAnomaliaZPrigimaliaEquipmentSlot::BackpackStrapRight: return Backpack&&(C==TEXT("long_weapon")||C==TEXT("long_tool")||C==TEXT("tool"));
 case EAnomaliaZPrigimaliaEquipmentSlot::BeltHolster: return Belt&&C==TEXT("holster");
 case EAnomaliaZPrigimaliaEquipmentSlot::BeltKnife: return Belt&&C==TEXT("knife");
 case EAnomaliaZPrigimaliaEquipmentSlot::VestPouches: return Vest&&C==TEXT("pouches");
 case EAnomaliaZPrigimaliaEquipmentSlot::Hands: return true;
 default: return false;
 }
}

FIntPoint UAnomaliaZPrigimaliaEquipmentSlotsLibrary::SuggestedCargoGrid(FName Garment)
{
 FName Preset=Garment;
 if(Garment==TEXT("shirt")||Garment==TEXT("jacket"))Preset=TEXT("jacket_light");
 else if(Garment==TEXT("coat"))Preset=TEXT("jacket_military");
 else if(Garment==TEXT("jeans"))Preset=TEXT("pants");
 else if(Garment==TEXT("vest"))Preset=TEXT("vest_tactical");
 else if(Garment==TEXT("backpack")||Garment==TEXT("bag"))Preset=TEXT("backpack_small");
 FIntPoint Grid;
 UAnomaliaZPrigimaliaStorageCatalog::GetGrid(Preset,Grid);
 return Grid;
}

FName UAnomaliaZPrigimaliaEquipmentSlotsLibrary::SlotContainerId(EAnomaliaZPrigimaliaEquipmentSlot Slot)
{
 switch(Slot)
 {
 case EAnomaliaZPrigimaliaEquipmentSlot::Vest: return TEXT("equip_vest");
 case EAnomaliaZPrigimaliaEquipmentSlot::Top: return TEXT("equip_top");
 case EAnomaliaZPrigimaliaEquipmentSlot::Belt: return TEXT("equip_belt");
 case EAnomaliaZPrigimaliaEquipmentSlot::Legs: return TEXT("equip_legs");
 case EAnomaliaZPrigimaliaEquipmentSlot::Back: return TEXT("equip_back");
 case EAnomaliaZPrigimaliaEquipmentSlot::Head: return TEXT("equip_head");
 case EAnomaliaZPrigimaliaEquipmentSlot::Face: return TEXT("equip_face");
 case EAnomaliaZPrigimaliaEquipmentSlot::Eyes: return TEXT("equip_eyes");
 case EAnomaliaZPrigimaliaEquipmentSlot::Gloves: return TEXT("equip_gloves");
 case EAnomaliaZPrigimaliaEquipmentSlot::Feet: return TEXT("equip_feet");
 case EAnomaliaZPrigimaliaEquipmentSlot::Armband: return TEXT("equip_armband");
 case EAnomaliaZPrigimaliaEquipmentSlot::ShoulderPrimary: return TEXT("attach_shoulder_1");
 case EAnomaliaZPrigimaliaEquipmentSlot::ShoulderSecondary: return TEXT("attach_shoulder_2");
 case EAnomaliaZPrigimaliaEquipmentSlot::BackpackTool: return TEXT("attach_backpack_tool");
 case EAnomaliaZPrigimaliaEquipmentSlot::BackpackStrapLeft: return TEXT("attach_backpack_strap_1");
 case EAnomaliaZPrigimaliaEquipmentSlot::BackpackStrapRight: return TEXT("attach_backpack_strap_2");
 case EAnomaliaZPrigimaliaEquipmentSlot::BeltHolster: return TEXT("attach_belt_holster");
 case EAnomaliaZPrigimaliaEquipmentSlot::BeltKnife: return TEXT("attach_belt_knife");
 case EAnomaliaZPrigimaliaEquipmentSlot::VestPouches: return TEXT("attach_vest_pouches");
 case EAnomaliaZPrigimaliaEquipmentSlot::Hands: return TEXT("hands");
 default: return NAME_None;
 }
}
