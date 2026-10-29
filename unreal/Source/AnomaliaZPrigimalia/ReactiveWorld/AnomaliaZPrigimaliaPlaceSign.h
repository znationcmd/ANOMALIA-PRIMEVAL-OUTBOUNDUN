#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaZPrigimaliaPlaceSign.generated.h"
class UStaticMeshComponent;
class UTextRenderComponent;

/** Native named sign, authored into the map and preserved by stable place ID. */
UCLASS(Blueprintable)
class ANOMALIAZPRIGIMALIA_API AAnomaliaZPrigimaliaPlaceSign : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaZPrigimaliaPlaceSign();
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Place") FName PlaceId;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Place") FText PlaceName;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UStaticMeshComponent> Board;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UTextRenderComponent> FrontText;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UTextRenderComponent> BackText;
    virtual void OnConstruction(const FTransform& Transform) override;
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|Place") bool SnapToGround(float ExpectedGroundZCm);
};
