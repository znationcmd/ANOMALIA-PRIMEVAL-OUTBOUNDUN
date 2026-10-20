#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaHomesteadStation.generated.h"

class UStaticMeshComponent;
class AAnomaliaSurvivor;

/** First-pass placeable catalogue. Custom meshes/materials are assigned via Blueprint children. */
UENUM(BlueprintType)
enum class EAnomaliaHomesteadObject : uint8
{
    Bed, Table, Chair, Sofa, Wardrobe, Kitchen, Lamp,
    Cow, Chicken, Beehive, Doghouse, Barn, Fence, TractorShed
};

UCLASS(Blueprintable)
class ANOMALIAPRIMEVAL_API AAnomaliaHomesteadStation : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaHomesteadStation();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Homestead")
    TObjectPtr<UStaticMeshComponent> DisplayMesh;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Replicated, Category="ANOMALIA|Homestead")
    EAnomaliaHomesteadObject ObjectType = EAnomaliaHomesteadObject::Bed;

    /** Stable runtime placement ID; empty for legacy/server-authored scenery. */
    UPROPERTY(Replicated, VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Furniture")
    FString PlacementId;

    /** World time in seconds; replicated so UI may show the cooldown. */
    UPROPERTY(Replicated, BlueprintReadOnly, Category="ANOMALIA|Farm")
    float NextHarvestTime = 0.f;

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Homestead")
    bool IsRestPlace() const { return ObjectType == EAnomaliaHomesteadObject::Bed; }

    /** Returns the supported inventory item. None means this station has no harvest action. */
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Farm")
    FName GetHarvestItemId() const;

    /** Trusted server-only call; checked again for authority, distance and cooldown. */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Farm")
    bool TryHarvest(AAnomaliaSurvivor* Survivor);

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
