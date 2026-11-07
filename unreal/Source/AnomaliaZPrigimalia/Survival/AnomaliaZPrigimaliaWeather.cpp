#include "AnomaliaZPrigimaliaWeather.h"
#include "../AnomaliaZPrigimaliaGameMode.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Net/UnrealNetwork.h"

namespace { TArray<TWeakObjectPtr<UAnomaliaZPrigimaliaHeatSourceComponent>> HeatSources; }
AAnomaliaZPrigimaliaWeather::AAnomaliaZPrigimaliaWeather()
{
    bReplicates=true;bAlwaysRelevant=true;PrimaryActorTick.bCanEverTick=true;PrimaryActorTick.TickInterval=1;
    StormFog=CreateDefaultSubobject<UExponentialHeightFogComponent>(TEXT("StormFog"));RootComponent=StormFog;
    StormFog->SetVisibility(false);StormFog->SetFogMaxOpacity(1);
}
AAnomaliaZPrigimaliaWeather* AAnomaliaZPrigimaliaWeather::Find(const UWorld* World)
{
    if(!World)return nullptr;
    for(TActorIterator<AAnomaliaZPrigimaliaWeather> It(World);It;++It)return *It;
    return nullptr;
}
void AAnomaliaZPrigimaliaWeather::BeginPlay()
{
    Super::BeginPlay();
    if(HasAuthority())if(const auto* Mode=GetWorld()->GetAuthGameMode<AAnomaliaZPrigimaliaGameMode>())
        AirTemperatureC=BaselineTemperatureC=Mode->ActiveServerSettings.AmbientTemperatureC;
    OnRep_Weather();
}
bool AAnomaliaZPrigimaliaWeather::SetStorm(EAnomaliaStorm Kind,float Strength,float TemperatureC,float Duration)
{
    if(!HasAuthority()||static_cast<uint8>(Kind)>static_cast<uint8>(EAnomaliaStorm::Rain)||!FMath::IsFinite(Strength)||!FMath::IsFinite(TemperatureC)||!FMath::IsFinite(Duration)||Strength<0||Strength>1||TemperatureC< -60||TemperatureC>60||Duration<1||Duration>7200)return false;
    Storm=Kind;Intensity=Kind==EAnomaliaStorm::Clear?0:Strength;AirTemperatureC=TemperatureC;RemainingSeconds=Duration;
    WindSpeedMS=Storm==EAnomaliaStorm::Clear?0:(Storm==EAnomaliaStorm::Rain?22.f:35.f)*Intensity;
    OnRep_Weather();ForceNetUpdate();return true;
}
void AAnomaliaZPrigimaliaWeather::Tick(float Delta)
{
    Super::Tick(Delta);if(!HasAuthority()||!bAutomaticStorms||!FMath::IsFinite(Delta)||Delta<=0)return;
    RemainingSeconds-=FMath::Min(Delta,2.f);if(RemainingSeconds>0)return;
    if(Storm!=EAnomaliaStorm::Clear){SetStorm(EAnomaliaStorm::Clear,0,BaselineTemperatureC,FMath::FRandRange(900,2400));return;}
    const auto Kind=BaselineTemperatureC<=0?EAnomaliaStorm::Snow:BaselineTemperatureC>=35?EAnomaliaStorm::Sand:EAnomaliaStorm::Rain;
    const float Temperature=Kind==EAnomaliaStorm::Snow?FMath::Min(-12.f,BaselineTemperatureC-8):Kind==EAnomaliaStorm::Sand?BaselineTemperatureC+5:BaselineTemperatureC-6;
    SetStorm(Kind,FMath::FRandRange(.75f,1.f),FMath::Clamp(Temperature,-60.f,60.f),FMath::FRandRange(300,900));
}
void AAnomaliaZPrigimaliaWeather::OnRep_Weather()
{
    const bool Active=Storm!=EAnomaliaStorm::Clear&&Intensity>0;
    StormFog->SetVisibility(Active);if(!Active)return;
    StormFog->SetFogDensity((Storm==EAnomaliaStorm::Sand?.15f:Storm==EAnomaliaStorm::Snow?.10f:.035f)*Intensity);
    StormFog->SetFogHeightFalloff(.001f);
    StormFog->SetFogInscatteringColor(Storm==EAnomaliaStorm::Sand?FLinearColor(.55f,.35f,.12f):Storm==EAnomaliaStorm::Snow?FLinearColor(.72f,.8f,.9f):FLinearColor(.19f,.23f,.28f));
}
void AAnomaliaZPrigimaliaWeather::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(AAnomaliaZPrigimaliaWeather,Storm);DOREPLIFETIME(AAnomaliaZPrigimaliaWeather,Intensity);
    DOREPLIFETIME(AAnomaliaZPrigimaliaWeather,AirTemperatureC);DOREPLIFETIME(AAnomaliaZPrigimaliaWeather,WindSpeedMS);
}
UAnomaliaZPrigimaliaHeatSourceComponent::UAnomaliaZPrigimaliaHeatSourceComponent()
{PrimaryComponentTick.bCanEverTick=true;PrimaryComponentTick.TickInterval=1;SetIsReplicatedByDefault(true);}
void UAnomaliaZPrigimaliaHeatSourceComponent::BeginPlay(){Super::BeginPlay();HeatSources.AddUnique(this);}
void UAnomaliaZPrigimaliaHeatSourceComponent::EndPlay(const EEndPlayReason::Type Reason){HeatSources.Remove(this);Super::EndPlay(Reason);}
bool UAnomaliaZPrigimaliaHeatSourceComponent::Ignite()
{if(!GetOwner()||!GetOwner()->HasAuthority()||!FMath::IsFinite(FuelSeconds)||FuelSeconds<=0)return false;bBurning=true;GetOwner()->ForceNetUpdate();return true;}
void UAnomaliaZPrigimaliaHeatSourceComponent::Extinguish(){if(GetOwner()&&GetOwner()->HasAuthority()){bBurning=false;GetOwner()->ForceNetUpdate();}}
void UAnomaliaZPrigimaliaHeatSourceComponent::TickComponent(float Delta,ELevelTick Type,FActorComponentTickFunction* Function)
{
    Super::TickComponent(Delta,Type,Function);if(!GetOwner()||!GetOwner()->HasAuthority()||!bBurning||!FMath::IsFinite(Delta)||Delta<=0)return;
    FuelSeconds=FMath::Max(0.f,FuelSeconds-FMath::Min(Delta,2.f));if(FuelSeconds<=0)Extinguish();
}
float UAnomaliaZPrigimaliaHeatSourceComponent::Sample(UWorld* World,const FVector& Location,const AActor* Ignored)
{
    float Heat=0;
    for(const auto& Weak:HeatSources)
    {
        const auto* Source=Weak.Get();const auto* Owner=Source?Source->GetOwner():nullptr;
        if(!Owner||Owner->GetWorld()!=World||!Source->bBurning||!FMath::IsFinite(Source->FuelSeconds)||Source->FuelSeconds<=0||!FMath::IsFinite(Source->RadiusCm)||Source->RadiusCm<=0)continue;
        const FVector Flame=Owner->GetActorLocation()+FVector(0,0,60);
        const float Distance=FVector::Dist(Location,Flame);if(Distance>=Source->RadiusCm)continue;
        FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaFireHeat),true,Ignored);Query.AddIgnoredActor(Owner);FHitResult Hit;
        if(!World->LineTraceSingleByChannel(Hit,Location,Flame,ECC_Visibility,Query))Heat=FMath::Max(Heat,1-Distance/Source->RadiusCm);
    }
    return Heat;
}
void UAnomaliaZPrigimaliaHeatSourceComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(UAnomaliaZPrigimaliaHeatSourceComponent,FuelSeconds);DOREPLIFETIME(UAnomaliaZPrigimaliaHeatSourceComponent,bBurning);}
