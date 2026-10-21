#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaRailCarriage.generated.h"
class UStaticMeshComponent;
/** Server positioned metro coach. Passenger transport and animated coupling remain prototype work. */
UCLASS()
class ANOMALIAPRIMEVAL_API AAnomaliaRailCarriage : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaRailCarriage();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Rail")
    TObjectPtr<UStaticMeshComponent> Body;
protected:
    virtual void BeginPlay() override;
};
