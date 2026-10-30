#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaZPrigimaliaHomesteadStation.generated.h"

class UStaticMeshComponent;
class AAnomaliaZPrigimaliaSurvivor;

/** First-pass placeable catalogue. Custom meshes/materials are assigned via Blueprint children. */
UENUM(BlueprintType)
enum class EAnomaliaZPrigimaliaHomesteadObject : uint8
{
    Bed, Table, Chair, Sofa, Wardrobe, Kitchen, Lamp,
    Cow, Chicken, Beehive, Doghouse, Barn, Fence, TractorShed
};

UCLASS(Blueprintable)
class ANOMALIAZPRIGIMALIA_API AAnomaliaZPrigimaliaHomesteadStation : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaZPrigimaliaHomesteadStation();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Homestead")
    TObjectPtr<UStaticMeshComponent> DisplayMesh;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Replicated, Category="ANOMALIA|Homestead")
    EAnomaliaZPrigimaliaHomesteadObject ObjectType = EAnomaliaZPrigimaliaHomesteadObject::Bed;

    /** World time in seconds; replicated so UI may show the cooldown. */
    UPROPERTY(Replicated, BlueprintReadOnly, Category="ANOMALIA|Farm")
    float NextHarvestTime = 0.f;

    UFUNCTION(BlueprintPure, Category="ANOMALIA|Homestead")
    bool IsRestPlace() const { return ObjectType == EAnomaliaZPrigimaliaHomesteadObject::Bed; }

    /** Returns the supported inventory item. None means this station has no harvest action. */
    UFUNCTION(BlueprintPure, Category="ANOMALIA|Farm")
    FName GetHarvestItemId() const;

    /** Trusted server-only call; checked again for authority, distance and cooldown. */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Farm")
    bool TryHarvest(AAnomaliaZPrigimaliaSurvivor* Survivor);

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
