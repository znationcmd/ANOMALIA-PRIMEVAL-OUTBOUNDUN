#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaAuthenticGameProbe.generated.h"
class AAnomaliaSurvivor;
/** Runs only in an explicitly requested, isolated authentic-game validation session. */
UCLASS()
class ANOMALIAPRIMEVAL_API AAnomaliaAuthenticGameProbe : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaAuthenticGameProbe();
    virtual void Tick(float DeltaSeconds) override;
private:
    void Finish(const FString& Error=FString());
    void Screenshot(const TCHAR* Suffix);
    int32 Phase=0, CityMeshes=0;
    double Started=0, Next=0;
    FVector Before, DogBefore;
    float Walked=0, DogWalked=0, Driven=0;
    TWeakObjectPtr<AAnomaliaSurvivor> Survivor;
    TArray<FString> Checks;
};
