#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AnomaliaZPrigimaliaEquipmentSlotsLibrary.generated.h"

UENUM(BlueprintType)
enum class EAnomaliaZPrigimaliaEquipmentSlot : uint8
{
    Vest, Top, Belt, Legs, Back, Head, Face, Eyes, Gloves, Feet, Armband,
    ShoulderPrimary, ShoulderSecondary, BackpackTool, BackpackStrapLeft,
    BackpackStrapRight, BeltHolster, BeltKnife, VestPouches, Hands
};

USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaEquipmentItem
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName ItemId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName Category;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float WeightKg = 0.f;
};

/** Shared equipment rules. Character equip actions and meshes are separate integrations. */
UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaEquipmentSlotsLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Equipment")
    static bool CanEquip(EAnomaliaZPrigimaliaEquipmentSlot Slot,const FAnomaliaZPrigimaliaEquipmentItem& Item,bool Backpack,bool Belt,bool Vest);
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Equipment")
    static FIntPoint SuggestedCargoGrid(FName Garment);
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Equipment")
    static FName SlotContainerId(EAnomaliaZPrigimaliaEquipmentSlot Slot);
};
