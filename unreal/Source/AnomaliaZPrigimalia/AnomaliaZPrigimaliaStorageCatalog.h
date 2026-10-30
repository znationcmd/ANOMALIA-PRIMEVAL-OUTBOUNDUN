#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AnomaliaZPrigimaliaStorageCatalog.generated.h"

/** Shared dimensions for worn cargo and world/vehicle storage. Weight remains a separate limit. */
UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaStorageCatalog : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    static constexpr int32 MaxDimension = 1000;
    static constexpr int32 MaxCells = 100000;
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Inventory")
    static bool GetGrid(FName PresetId, FIntPoint& OutGrid);
    static TArray<FName> GetPresetIds();
    /** Exact approved vehicle presets, otherwise x10 the original reference once. */
    static int32 GetVehicleCapacity(FName VehicleId,int32 ReferenceCells);
    static bool IsValidGrid(int32 Width,int32 Height)
    { return Width>0 && Height>0 && Width<=MaxDimension && Height<=MaxDimension && static_cast<int64>(Width)*Height<=MaxCells; }
};
