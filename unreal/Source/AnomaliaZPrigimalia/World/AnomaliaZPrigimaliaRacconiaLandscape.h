#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AnomaliaZPrigimaliaRacconiaLandscape.generated.h"

class AActor;

/** Imports the user-supplied 16 km real RACCONIA R16 terrain into a NEW isolated
 * World Partition level. Never overwrites an existing UE map or stages blockouts
 * as if they were final realistic buildings. Editor only; not shipped gameplay. */
UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaRacconiaLandscape : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="ANOMALIA|RACCONIA|Editor")
    static AActor* CreateRacconiaVerifiedLandscape();
};
