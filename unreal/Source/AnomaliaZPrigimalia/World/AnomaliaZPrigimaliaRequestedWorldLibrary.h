#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AnomaliaZPrigimaliaRequestedWorldLibrary.generated.h"
UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaRequestedWorldLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable,Category="ANOMALIA|RequestedWorlds")
 static AActor* CreateNamedWorldLandscape(const FString& MapIdentifier);
 UFUNCTION(BlueprintPure,Category="ANOMALIA|RequestedWorlds")
 static double NamedWorldHeight(const FString& MapIdentifier,double EastMeters,double NorthMeters);
};
