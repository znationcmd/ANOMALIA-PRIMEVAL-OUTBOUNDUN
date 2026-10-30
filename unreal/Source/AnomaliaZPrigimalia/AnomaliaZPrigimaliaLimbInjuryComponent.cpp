#include "AnomaliaZPrigimaliaLimbInjuryComponent.h"
UAnomaliaZPrigimaliaLimbInjuryComponent::UAnomaliaZPrigimaliaLimbInjuryComponent(){PrimaryComponentTick.bCanEverTick=true;}
void UAnomaliaZPrigimaliaLimbInjuryComponent::BeginPlay(){Super::BeginPlay();}
int32 UAnomaliaZPrigimaliaLimbInjuryComponent::ApplyImpact(EAnomaliaZPrigimaliaLimb Limb,float Force,float Protection)
{
 if(!FMath::IsFinite(Force)||!FMath::IsFinite(Protection))return Injuries.FindRef(Limb).Severity;
 const float Impact=FMath::Max(0.f,Force)*(1.f-FMath::Clamp(Protection,0.f,1.f));
 FAnomaliaZPrigimaliaLimbInjury& Injury=Injuries.FindOrAdd(Limb);
 const int32 NewSeverity=Impact>=90.f?3:Impact>=60.f?2:Impact>=30.f?1:0;
 if(NewSeverity>Injury.Severity){Injury.Severity=NewSeverity;Injury.Healing=0.f;}
 return Injury.Severity;
}
bool UAnomaliaZPrigimaliaLimbInjuryComponent::ApplySplint(EAnomaliaZPrigimaliaLimb Limb)
{
 FAnomaliaZPrigimaliaLimbInjury* Injury=Injuries.Find(Limb);
 if(!Injury||Injury->Severity<=0||Injury->bImmobilized)return false;
 // Caller must validate and consume one splint from server-authoritative inventory.
 Injury->bImmobilized=true;return true;
}
FAnomaliaZPrigimaliaLimbEffects UAnomaliaZPrigimaliaLimbInjuryComponent::GetEffects() const
{
 auto Severity=[this](EAnomaliaZPrigimaliaLimb Limb){return Injuries.FindRef(Limb).Severity;};
 const int32 Arms=FMath::Max(Severity(EAnomaliaZPrigimaliaLimb::LeftArm),Severity(EAnomaliaZPrigimaliaLimb::RightArm));
 const int32 Legs=FMath::Max(Severity(EAnomaliaZPrigimaliaLimb::LeftLeg),Severity(EAnomaliaZPrigimaliaLimb::RightLeg));
 FAnomaliaZPrigimaliaLimbEffects Effects;
 Effects.AimSway=Arms*.3f;Effects.ReloadMultiplier=1.f+Arms*.45f;
 Effects.MovementMultiplier=FMath::Max(.25f,1.f-Legs*.22f);
 Effects.bCanUseTwoHandedWeapons=Arms<2;Effects.bCanSprint=Legs<2;Effects.bCanClimb=Arms<2&&Legs<2;
 return Effects;
}
void UAnomaliaZPrigimaliaLimbInjuryComponent::TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction)
{
 Super::TickComponent(DeltaTime,TickType,ThisTickFunction);
 if(!GetOwner()||!GetOwner()->HasAuthority())return;
 for(auto& Pair:Injuries)
 {
  FAnomaliaZPrigimaliaLimbInjury& Injury=Pair.Value;
  if(Injury.Severity<=0)continue;
  Injury.Healing+=FMath::Max(0.f,DeltaTime)*(Injury.bImmobilized?2.f:.35f);
  if(Injury.Healing>=1800.f){Injury.Severity=FMath::Max(0,Injury.Severity-1);Injury.Healing=0.f;}
 }
}