#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaZPrigimaliaRailCarriage.generated.h"
class UStaticMeshComponent;
/** Server positioned metro coach. Passenger transport and animated coupling remain prototype work. */
UCLASS()
class ANOMALIAZPRIGIMALIA_API AAnomaliaZPrigimaliaRailCarriage : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaZPrigimaliaRailCarriage();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Rail")
    TObjectPtr<UStaticMeshComponent> Body;
protected:
    virtual void BeginPlay() override;
};
