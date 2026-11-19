#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaZPrigimaliaWaterSource.generated.h"

class USceneComponent;

/**
 * Place this actor over a real river, fountain, well or lake in the authored world.
 * Authoritative requests check this exact actor and proximity; no client-provided
 * water quality, coordinates or item IDs are ever accepted.
 */
UCLASS(Blueprintable)
class ANOMALIAZPRIGIMALIA_API AAnomaliaZPrigimaliaWaterSource : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaZPrigimaliaWaterSource();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Water")
    TObjectPtr<USceneComponent> WaterPoint;

    /** A fountain/well may be potable; natural rivers and lakes default to untreated. */
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="ANOMALIA|Water")
    bool bPotable = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Water")
    bool bAvailable = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Water", meta=(ClampMin="50.0",ClampMax="400.0"))
    float FillRadiusCm = 250.f;

    bool CanFillFrom(const FVector& CharacterLocation) const;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
