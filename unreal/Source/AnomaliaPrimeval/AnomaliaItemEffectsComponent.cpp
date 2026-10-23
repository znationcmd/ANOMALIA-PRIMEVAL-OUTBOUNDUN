#include "AnomaliaItemEffectsComponent.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaInventoryComponent.h"
#include "AnomaliaVitalsComponent.h"
#include "Camera/CameraComponent.h"
#include "Dom/JsonObject.h"
#include "Net/UnrealNetwork.h"

#define ANOMALIA_EFFECT_FIELDS(X) X(Blood,100) X(Bleeding,100) X(Pain,100) X(Infection,100) X(Poison,100) X(Intoxication,100) X(Dependence,100) X(RemainingSeconds,3600) X(Diagnosed,1)

UAnomaliaItemEffectsComponent::UAnomaliaItemEffectsComponent()
{
    PrimaryComponentTick.bCanEverTick=true;
    PrimaryComponentTick.TickInterval=.25f;
    SetIsReplicatedByDefault(true);
}
bool UAnomaliaItemEffectsComponent::IsKnownEffect(const FString& Effect)
{
    static const TSet<FString> Names={TEXT("bandage"),TEXT("rags"),TEXT("analgesic"),TEXT("antibiotic"),
        TEXT("antidote"),TEXT("saline"),TEXT("blood"),TEXT("splint"),TEXT("disinfectant"),TEXT("vitamins"),
        TEXT("diagnostic"),TEXT("stimulant"),TEXT("opioid"),TEXT("depressant"),TEXT("hallucinogen"),
        TEXT("cannabinoid"),TEXT("veterinary"),TEXT("anomaly"),TEXT("nicotine"),TEXT("alcohol"),TEXT("raw_food"),TEXT("recovery")};
    return Names.Contains(Effect);
}
bool UAnomaliaItemEffectsComponent::IsValidState(const FAnomaliaItemEffectsState& Value)
{
#define CHECK_FIELD(Name,Max) if(!FMath::IsFinite(Value.Name) || Value.Name<0.f || Value.Name>Max) return false;
    ANOMALIA_EFFECT_FIELDS(CHECK_FIELD)
#undef CHECK_FIELD
    return Value.ActiveEffect.IsEmpty() || IsKnownEffect(Value.ActiveEffect);
}
bool UAnomaliaItemEffectsComponent::ReadState(const TSharedPtr<FJsonObject>& Survival,FAnomaliaItemEffectsState& Out,FString& Error)
{
    if(!Survival.IsValid()) { Error=TEXT("Profil de survie invalide.");return false; }
    Out=FAnomaliaItemEffectsState();
    if(!Survival->HasField(TEXT("itemEffects"))) return true;
    const TSharedPtr<FJsonObject>* Object=nullptr;
    if(!Survival->TryGetObjectField(TEXT("itemEffects"),Object) || !Object || !Object->IsValid())
    { Error=TEXT("Effets existants invalides : profil conservé.");return false; }
#define READ_FIELD(Name,Max) if((*Object)->HasField(TEXT(#Name))) { double Number=0; if(!(*Object)->TryGetNumberField(TEXT(#Name),Number) || !FMath::IsFinite(Number) || Number<0 || Number>Max) { Error=TEXT("Effets existants hors limites.");return false; } Out.Name=static_cast<float>(Number); }
    ANOMALIA_EFFECT_FIELDS(READ_FIELD)
#undef READ_FIELD
    if((*Object)->HasField(TEXT("activeEffect")) && !(*Object)->TryGetStringField(TEXT("activeEffect"),Out.ActiveEffect)) return false;
    if(!IsValidState(Out)) { Error=TEXT("Effet inconnu dans le profil.");return false; }
    return true;
}
bool UAnomaliaItemEffectsComponent::WriteState(const TSharedPtr<FJsonObject>& Survival,const FAnomaliaItemEffectsState& Value,FString& Error)
{
    FAnomaliaItemEffectsState Existing;
    if(!IsValidState(Value) || !ReadState(Survival,Existing,Error)) return false;
    const TSharedPtr<FJsonObject>* Previous=nullptr;
    auto Object=Survival->TryGetObjectField(TEXT("itemEffects"),Previous)?*Previous:MakeShared<FJsonObject>();
#define WRITE_FIELD(Name,Max) Object->SetNumberField(TEXT(#Name),Value.Name);
    ANOMALIA_EFFECT_FIELDS(WRITE_FIELD)
#undef WRITE_FIELD
    Object->SetStringField(TEXT("activeEffect"),Value.ActiveEffect);
    Survival->SetObjectField(TEXT("itemEffects"),Object);
    return true;
}
bool UAnomaliaItemEffectsComponent::PreviewUse(const FString& Effect,FAnomaliaItemEffectsState& Out) const
{
    Out=State;
    if(!GetOwner() || !GetOwner()->HasAuthority() || !IsValidState(State)) return false;
    if(Effect.IsEmpty()) return true;
    if(!IsKnownEffect(Effect)) return false;
    if(Effect==TEXT("bandage")) { Out.Bleeding=FMath::Max(0.f,Out.Bleeding-60);Out.Pain=FMath::Max(0.f,Out.Pain-5); }
    else if(Effect==TEXT("rags")) { Out.Bleeding=FMath::Max(0.f,Out.Bleeding-25); }
    else if(Effect==TEXT("antibiotic")) Out.Infection=FMath::Max(0.f,Out.Infection-30);
    else if(Effect==TEXT("antidote")) Out.Poison=FMath::Max(0.f,Out.Poison-35);
    else if(Effect==TEXT("saline")) Out.Blood=FMath::Min(100.f,Out.Blood+10);
    else if(Effect==TEXT("blood")) Out.Blood=FMath::Min(100.f,Out.Blood+25);
    else if(Effect==TEXT("splint")) Out.Pain=FMath::Max(0.f,Out.Pain-20);
    else if(Effect==TEXT("disinfectant")) Out.Infection=FMath::Max(0.f,Out.Infection-15);
    else if(Effect==TEXT("vitamins")) { Out.RemainingSeconds=FMath::Max(Out.RemainingSeconds,60.f);Out.ActiveEffect=Effect; }
    else if(Effect==TEXT("diagnostic")) Out.Diagnosed=1;
    else if(Effect==TEXT("recovery")) { Out.Intoxication=FMath::Max(0.f,Out.Intoxication-25);Out.Poison=FMath::Max(0.f,Out.Poison-20); }
    else if(Effect==TEXT("raw_food")) { Out.Poison=FMath::Min(100.f,Out.Poison+12); }
    else
    {
        // Deliberately fictional points and timings, shared by broad RP families.
        const bool Nicotine=Effect==TEXT("nicotine");
        const bool Alcohol=Effect==TEXT("alcohol");
        Out.Intoxication=FMath::Min(100.f,Out.Intoxication+(Nicotine?5.f:Alcohol?20.f:30.f));
        Out.Dependence=FMath::Min(100.f,Out.Dependence+(Nicotine?8.f:Alcohol?4.f:12.f));
        Out.RemainingSeconds=FMath::Min(3600.f,Out.RemainingSeconds+(Nicotine?60.f:120.f));
        Out.ActiveEffect=Effect;
        if(Effect==TEXT("analgesic") || Effect==TEXT("opioid")) Out.Pain=FMath::Max(0.f,Out.Pain-40);
        if(Effect==TEXT("veterinary") || Effect==TEXT("anomaly")) Out.Poison=FMath::Min(100.f,Out.Poison+15);
    }
    return true;
}
bool UAnomaliaItemEffectsComponent::HasChange(const FAnomaliaItemEffectsState& Value) const
{
#define COMPARE_FIELD(Name,Max) if(Value.Name!=State.Name) return true;
    ANOMALIA_EFFECT_FIELDS(COMPARE_FIELD)
#undef COMPARE_FIELD
    return Value.ActiveEffect!=State.ActiveEffect;
}
void UAnomaliaItemEffectsComponent::ApplyState(const FAnomaliaItemEffectsState& Value)
{
    if(!GetOwner() || !GetOwner()->HasAuthority() || !IsValidState(Value)) return;
    State=Value;GetOwner()->ForceNetUpdate();ApplyLocalVisuals();
}
float UAnomaliaItemEffectsComponent::GetMovementScale() const
{ return FMath::Clamp(1.f-State.Intoxication*.005f-State.Pain*.002f,.35f,1.f); }
float UAnomaliaItemEffectsComponent::GetStaminaRecoveryScale() const
{
    if(State.RemainingSeconds<=0) return 1.f;
    if(State.ActiveEffect==TEXT("stimulant") || State.ActiveEffect==TEXT("vitamins")) return 1.1f;
    if(State.ActiveEffect==TEXT("depressant") || State.ActiveEffect==TEXT("veterinary")) return .5f;
    if(State.ActiveEffect==TEXT("opioid") || State.ActiveEffect==TEXT("alcohol")) return .7f;
    return .9f;
}
void UAnomaliaItemEffectsComponent::AddInjury(float Severity)
{
    if(!GetOwner() || !GetOwner()->HasAuthority() || !FMath::IsFinite(Severity) || Severity<=0) return;
    auto Next=State;Next.Pain=FMath::Clamp(Next.Pain+Severity,0.f,100.f);
    Next.Bleeding=FMath::Clamp(Next.Bleeding+Severity*.4f,0.f,100.f);ApplyState(Next);
}
void UAnomaliaItemEffectsComponent::AdvanceSimulation(float DeltaSeconds)
{
    auto* Survivor=Cast<AAnomaliaSurvivor>(GetOwner());
    if(!Survivor || !Survivor->HasAuthority() || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds<=0 ||
        Survivor->Health<=0 || (Survivor->InventoryComponent && Survivor->InventoryComponent->IsPersistenceLocked())) return;
    const float Step=FMath::Min(DeltaSeconds,.25f);
    State.RemainingSeconds=FMath::Max(0.f,State.RemainingSeconds-Step);
    if(State.RemainingSeconds<=0) State.ActiveEffect.Empty();
    State.Intoxication=FMath::Max(0.f,State.Intoxication-.15f*Step);
    State.Dependence=FMath::Max(0.f,State.Dependence-.002f*Step);
    State.Blood=FMath::Max(0.f,State.Blood-State.Bleeding*.002f*Step);
    if(State.Bleeding<=0 && Survivor->Hunger>25 && Survivor->Thirst>25) State.Blood=FMath::Min(100.f,State.Blood+.01f*Step);
    if(State.Intoxication>=80 || State.Poison>=60 || State.Infection>=60 || State.Blood<25)
        Survivor->Health=FMath::Max(0.f,Survivor->Health-.4f*Step);
    if(State.Dependence>40 && State.Intoxication<5) Survivor->Fatigue=FMath::Min(100.f,Survivor->Fatigue+.02f*Step);
    if(State.Intoxication>20) Survivor->Thirst=FMath::Max(0.f,Survivor->Thirst-.02f*Step);
    if(State.RemainingSeconds>0 && State.ActiveEffect==TEXT("stimulant")) Survivor->Fatigue=FMath::Max(0.f,Survivor->Fatigue-.02f*Step);
    if(State.RemainingSeconds>0 && (State.ActiveEffect==TEXT("depressant") || State.ActiveEffect==TEXT("veterinary")))
        Survivor->Fatigue=FMath::Min(100.f,Survivor->Fatigue+.04f*Step);
    Survivor->OnSurvivalChanged();
}
void UAnomaliaItemEffectsComponent::ApplyLocalVisuals()
{
    auto* Survivor=Cast<AAnomaliaSurvivor>(GetOwner());
    if(!Survivor || !Survivor->IsLocallyControlled() || !Survivor->FollowCamera) return;
    auto& Settings=Survivor->FollowCamera->PostProcessSettings;
    if(!bCapturedVignette) { BaseVignette=Settings.VignetteIntensity;bCapturedVignette=true; }
    Settings.bOverride_VignetteIntensity=true;
    Settings.VignetteIntensity=FMath::Clamp(BaseVignette+State.Intoxication*.004f,0.f,1.f);
}
void UAnomaliaItemEffectsComponent::OnRep_State()
{
    ApplyLocalVisuals();
    if(auto* Survivor=Cast<AAnomaliaSurvivor>(GetOwner()))
        if(Survivor->VitalsComponent) Survivor->VitalsComponent->RefreshMovementSpeed();
}
void UAnomaliaItemEffectsComponent::TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* Function)
{ Super::TickComponent(DeltaTime,TickType,Function);AdvanceSimulation(DeltaTime);ApplyLocalVisuals(); }
void UAnomaliaItemEffectsComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{ Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(UAnomaliaItemEffectsComponent,State); }
#undef ANOMALIA_EFFECT_FIELDS
