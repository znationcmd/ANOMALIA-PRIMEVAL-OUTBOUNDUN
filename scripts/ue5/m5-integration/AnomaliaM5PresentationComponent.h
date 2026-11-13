#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AnomaliaM5PresentationComponent.generated.h"
class UStaticMesh;
class USoundBase;
class UAudioComponent;

/** Opt-in E39 presentation using recorded S62 audio and authored V8 geometry. */
UCLASS(ClassGroup=(ANOMALIA), meta=(BlueprintSpawnableComponent))
class ANOMALIAPRIMEVAL_API UAnomaliaM5PresentationComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UAnomaliaM5PresentationComponent();
    UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="ANOMALIA|M5") bool bEnabled=true;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="ANOMALIA|M5") TSoftObjectPtr<UStaticMesh> EngineMesh;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="ANOMALIA|M5") TSoftObjectPtr<USoundBase> IdleRecording;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="ANOMALIA|M5") TSoftObjectPtr<USoundBase> LoadRecording;
    UPROPERTY(Replicated,VisibleAnywhere,BlueprintReadOnly,Category="ANOMALIA|M5") float EngineRPM=0.f;
    UPROPERTY(Replicated,VisibleAnywhere,BlueprintReadOnly,Category="ANOMALIA|M5") float EngineLoad=0.f;
    virtual void TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> IdleAudio;
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> LoadAudio;
    bool bPlaybackActive=false;
    float DisplayRPM=800.f;
    float NetworkElapsed=0.f;
};
