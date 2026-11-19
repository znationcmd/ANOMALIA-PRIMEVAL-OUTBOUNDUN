#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/ActorComponent.h"
#include "AnomaliaZPrigimaliaWeather.generated.h"
class UExponentialHeightFogComponent;

UENUM(BlueprintType)
enum class EAnomaliaStorm : uint8 { Clear, Sand, Snow, Rain };

UCLASS(Blueprintable)
class ANOMALIAZPRIGIMALIA_API AAnomaliaZPrigimaliaWeather : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaZPrigimaliaWeather();
    UPROPERTY(ReplicatedUsing=OnRep_Weather,BlueprintReadOnly) EAnomaliaStorm Storm=EAnomaliaStorm::Clear;
    UPROPERTY(ReplicatedUsing=OnRep_Weather,BlueprintReadOnly) float Intensity=0;
    UPROPERTY(Replicated,BlueprintReadOnly) float AirTemperatureC=20;
    UPROPERTY(Replicated,BlueprintReadOnly) float WindSpeedMS=0;
    UPROPERTY(EditAnywhere,BlueprintReadOnly) bool bAutomaticStorms=true;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly) TObjectPtr<UExponentialHeightFogComponent> StormFog;
    UFUNCTION(BlueprintCallable,BlueprintAuthorityOnly) bool SetStorm(EAnomaliaStorm Kind,float Strength,float TemperatureC,float DurationSeconds);
    UFUNCTION(BlueprintPure) float GetRainExposure() const { return Storm==EAnomaliaStorm::Rain?Intensity:0; }
    virtual void Tick(float DeltaSeconds) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Props) const override;
    static AAnomaliaZPrigimaliaWeather* Find(const UWorld* World);
protected:
    virtual void BeginPlay() override;
private:
    UFUNCTION() void OnRep_Weather();
    float RemainingSeconds=900;
    float BaselineTemperatureC=20;
};

/** Attach to an existing authored fire/heater actor. No replacement mesh is generated. */
UCLASS(ClassGroup=(ANOMALIA),meta=(BlueprintSpawnableComponent))
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaHeatSourceComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UAnomaliaZPrigimaliaHeatSourceComponent();
    UPROPERTY(EditAnywhere,Replicated,BlueprintReadOnly) float FuelSeconds=0;
    UPROPERTY(Replicated,BlueprintReadOnly) bool bBurning=false;
    UPROPERTY(EditAnywhere,BlueprintReadOnly) float RadiusCm=500;
    UFUNCTION(BlueprintCallable,BlueprintAuthorityOnly) bool Ignite();
    UFUNCTION(BlueprintCallable,BlueprintAuthorityOnly) void Extinguish();
    static float Sample(UWorld* World,const FVector& Location,const AActor* Ignored);
    virtual void TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* Function) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Props) const override;
protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
};
