#include "AnomaliaM5PresentationComponent.h"
#include "AnomaliaChaosRoadVehicle.h"
#include "ChaosWheeledVehicleMovementComponent.h"
#include "Components/AudioComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Camera/CameraComponent.h"
#include "Engine/StaticMesh.h"
#include "Sound/SoundBase.h"
#include "Net/UnrealNetwork.h"

UAnomaliaM5PresentationComponent::UAnomaliaM5PresentationComponent()
{
    PrimaryComponentTick.bCanEverTick=true;
    SetIsReplicatedByDefault(true);
    EngineMesh=TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(TEXT("/Game/Anomalia/E39M5S62_v1/SM_engine_bay.SM_engine_bay")));
    IdleRecording=TSoftObjectPtr<USoundBase>(FSoftObjectPath(TEXT("/Game/Anomalia/E39M5S62Audio_v1/S_m5_idle.S_m5_idle")));
    LoadRecording=TSoftObjectPtr<USoundBase>(FSoftObjectPath(TEXT("/Game/Anomalia/E39M5S62Audio_v1/S_m5_load.S_m5_load")));
}
void UAnomaliaM5PresentationComponent::BeginPlay()
{
    Super::BeginPlay();
    auto* Car=Cast<AAnomaliaChaosRoadVehicle>(GetOwner());
    if(!bEnabled || !Car || !Car->ActorHasTag(FName(TEXT("ANOMALIA_AUTHENTIC_E39"))))
    {SetComponentTickEnabled(false);return;}
    if(auto* Mesh=EngineMesh.LoadSynchronous())
    {
        Car->EngineBayMesh=Mesh;
        Car->EngineBayDetails->SetStaticMesh(Mesh);
        Car->EngineBayDetails->SetRelativeTransform(FTransform::Identity);
        Car->EngineBayDetails->SetVisibility(true);
        Car->EngineBayDetails->SetHiddenInGame(false);
    }
    if(Car->GetNetMode()==NM_DedicatedServer)return;
    const auto CreateAudio=[&](FName Name,USoundBase* Sound)->UAudioComponent*
    {
        if(!Sound)return nullptr;
        auto* Audio=NewObject<UAudioComponent>(Car,Name);
        Car->AddInstanceComponent(Audio);
        Audio->bAutoActivate=false;
        Audio->bAutoDestroy=false;
        Audio->bStopWhenOwnerDestroyed=true;
        Audio->SetupAttachment(Car->Chassis);
        Audio->SetRelativeLocation(FVector(-215,0,45)); // Exhaust, in authored chassis space.
        Audio->bOverrideAttenuation=true;
        Audio->AttenuationOverrides.bAttenuate=true;
        Audio->AttenuationOverrides.bSpatialize=true;
        Audio->AttenuationOverrides.AttenuationShapeExtents=FVector(200,0,0);
        Audio->AttenuationOverrides.FalloffDistance=8000.f;
        Audio->SetSound(Sound);
        Audio->RegisterComponent();
        return Audio;
    };
    IdleAudio=CreateAudio(TEXT("M5RecordedIdle"),IdleRecording.LoadSynchronous());
    LoadAudio=CreateAudio(TEXT("M5RecordedLoad"),LoadRecording.LoadSynchronous());
    UE_LOG(LogTemp,Display,TEXT("ANOMALIA_M5_AUDIO_READY idle=%d load=%d mesh=%d"),IdleAudio!=nullptr,LoadAudio!=nullptr,Car->EngineBayDetails->GetStaticMesh()!=nullptr);
}
void UAnomaliaM5PresentationComponent::TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime,TickType,ThisTickFunction);
    auto* Car=Cast<AAnomaliaChaosRoadVehicle>(GetOwner());
    if(!Car || !FMath::IsFinite(DeltaTime) || DeltaTime<=0.f)return;
    if(Car->HasAuthority())
    {
        NetworkElapsed+=DeltaTime;
        if(NetworkElapsed>=.1f)
        {
            NetworkElapsed=0.f;
            const float RawRPM=Car->bEngineRunning && Car->IsChaosDriveReady()?Car->ChaosMovement->GetEngineRotationSpeed():0.f;
            EngineRPM=Car->bEngineRunning && FMath::IsFinite(RawRPM)?FMath::Clamp(RawRPM,800.f,7000.f):0.f;
            const float RawLoad=Car->ChaosMovement->GetThrottleInput();
            EngineLoad=FMath::IsFinite(RawLoad)?FMath::Clamp(FMath::Abs(RawLoad),0.f,1.f):0.f;
            Car->ForceNetUpdate();
        }
    }
    if(Car->GetNetMode()==NM_DedicatedServer || !IdleAudio || !LoadAudio)return;
    if(!Car->bEngineRunning)
    {
        if(bPlaybackActive){IdleAudio->FadeOut(.2f,0.f);LoadAudio->FadeOut(.2f,0.f);bPlaybackActive=false;}
        return;
    }
    if(!bPlaybackActive)
    {
        IdleAudio->SetVolumeMultiplier(.001f);LoadAudio->SetVolumeMultiplier(.001f);
        IdleAudio->Play();LoadAudio->Play();bPlaybackActive=true;
    }
    const float SafeRPM=FMath::IsFinite(EngineRPM)?FMath::Clamp(EngineRPM,800.f,7000.f):800.f;
    DisplayRPM=FMath::FInterpTo(DisplayRPM,SafeRPM,DeltaTime,10.f);
    const float Blend=FMath::Clamp((DisplayRPM-1100.f)/1000.f,0.f,1.f);
    const float SafeLoad=FMath::IsFinite(EngineLoad)?FMath::Clamp(EngineLoad,0.f,1.f):0.f;
    const float Gain=.65f+.35f*SafeLoad;
    IdleAudio->SetPitchMultiplier(FMath::Clamp(DisplayRPM/800.f,.8f,2.65f));
    LoadAudio->SetPitchMultiplier(FMath::Clamp(DisplayRPM/2100.f,.5f,3.34f));
    IdleAudio->SetVolumeMultiplier(FMath::Max(.001f,FMath::Sqrt(1.f-Blend)*Gain));
    LoadAudio->SetVolumeMultiplier(FMath::Max(.001f,FMath::Sqrt(Blend)*Gain));
    const bool Interior=Car->IsLocallyControlled() && Car->InteriorCamera->IsActive();
    for(auto* Audio:{IdleAudio.Get(),LoadAudio.Get()})
    {Audio->SetLowPassFilterEnabled(Interior);Audio->SetLowPassFilterFrequency(Interior?2600.f:20000.f);}
}
void UAnomaliaM5PresentationComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    for(auto* Audio:{IdleAudio.Get(),LoadAudio.Get()})if(Audio){Audio->Stop();Audio->DestroyComponent();}
    Super::EndPlay(Reason);
}
void UAnomaliaM5PresentationComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UAnomaliaM5PresentationComponent,EngineRPM);
    DOREPLIFETIME(UAnomaliaM5PresentationComponent,EngineLoad);
}
