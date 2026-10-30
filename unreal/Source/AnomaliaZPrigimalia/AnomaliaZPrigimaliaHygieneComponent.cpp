#include "AnomaliaZPrigimaliaHygieneComponent.h"

UAnomaliaZPrigimaliaHygieneComponent::UAnomaliaZPrigimaliaHygieneComponent()
{
 PrimaryComponentTick.bCanEverTick = true;
}
void UAnomaliaZPrigimaliaHygieneComponent::BeginPlay()
{
 Super::BeginPlay();
}
void UAnomaliaZPrigimaliaHygieneComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
 Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
 const float Minutes = FMath::Max(0.f, DeltaTime) / 60.f;
 State.Hygiene = FMath::Clamp(State.Hygiene - Minutes * .15f, 0.f, 100.f);
 State.Bladder = FMath::Clamp(State.Bladder + Minutes * .14f, 0.f, 100.f);
 State.Bowel = FMath::Clamp(State.Bowel + Minutes * .07f, 0.f, 100.f);
}
bool UAnomaliaZPrigimaliaHygieneComponent::UseFixture(EAnomaliaZPrigimaliaSanitaryFixture Fixture, bool bHasWater, FName& OutAnimation)
{
 OutAnimation = NAME_None;
 switch (Fixture)
 {
 case EAnomaliaZPrigimaliaSanitaryFixture::Toilet:
  if (State.Bladder < 10.f && State.Bowel < 10.f) return false;
  State.Bladder = 0.f; State.Bowel = 0.f; OutAnimation = TEXT("hygiene_toilet"); return true;
 case EAnomaliaZPrigimaliaSanitaryFixture::Urinal:
  if (State.Bladder < 10.f) return false;
  State.Bladder = 0.f; OutAnimation = TEXT("hygiene_urinate"); return true;
 case EAnomaliaZPrigimaliaSanitaryFixture::Shower:
  if (!bHasWater) return false;
  State.Hygiene = 100.f; OutAnimation = TEXT("hygiene_shower"); return true;
 case EAnomaliaZPrigimaliaSanitaryFixture::Bathtub:
  if (!bHasWater) return false;
  State.Hygiene = 100.f; OutAnimation = TEXT("hygiene_bathe"); return true;
 case EAnomaliaZPrigimaliaSanitaryFixture::Sink:
  if (!bHasWater) return false;
  State.Hygiene = FMath::Clamp(State.Hygiene + 25.f, 0.f, 100.f);
  OutAnimation = TEXT("hygiene_wash_hands"); return true;
 }
 return false;
}