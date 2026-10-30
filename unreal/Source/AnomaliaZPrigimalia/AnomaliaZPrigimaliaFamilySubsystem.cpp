#include "AnomaliaZPrigimaliaFamilySubsystem.h"
bool UAnomaliaZPrigimaliaFamilySubsystem::FoundFamily(const FString& Id,const FString& A,const FString& B,bool AdultA,bool AdultB,bool ConsentA,bool ConsentB)
{
 if(Id.IsEmpty()||A.IsEmpty()||B.IsEmpty()||A==B||!AdultA||!AdultB||!ConsentA||!ConsentB||Families.Contains(Id))return false;
 FAnomaliaZPrigimaliaFamilyRecord Record;Record.Id=Id;Record.ParentA=A;Record.ParentB=B;Families.Add(Id,MoveTemp(Record));return true;
}
bool UAnomaliaZPrigimaliaFamilySubsystem::WelcomeChild(const FString& FamilyId,const FString& ChildId,const FString& Name,bool Consent,double Days)
{
 FAnomaliaZPrigimaliaFamilyRecord* Family=Families.Find(FamilyId);
 if(!Family||ChildId.IsEmpty()||Children.Contains(ChildId)||!Consent||!FMath::IsFinite(Days))return false;
 FAnomaliaZPrigimaliaChildRecord Child;Child.Id=ChildId;Child.FamilyId=FamilyId;Child.Name=Name.IsEmpty()?TEXT("Enfant"):Name;Child.BornAtDays=Days;
 Children.Add(ChildId,MoveTemp(Child));Family->Children.Add(ChildId);return true;
}
bool UAnomaliaZPrigimaliaFamilySubsystem::CareForChild(const FString& Id,float Food,float Comfort,float Health)
{
 FAnomaliaZPrigimaliaChildRecord* Child=Children.Find(Id);if(!Child)return false;
 Child->Food=FMath::Clamp(Child->Food+FMath::Max(0.f,Food),0.f,100.f);
 Child->Comfort=FMath::Clamp(Child->Comfort+FMath::Max(0.f,Comfort),0.f,100.f);
 Child->Health=FMath::Clamp(Child->Health+FMath::Max(0.f,Health),0.f,100.f);return true;
}
bool UAnomaliaZPrigimaliaFamilySubsystem::FollowParent(const FString& Id,const FString& ParentId)
{
 FAnomaliaZPrigimaliaChildRecord* Child=Children.Find(Id);if(!Child)return false;
 const FAnomaliaZPrigimaliaFamilyRecord* Family=Families.Find(Child->FamilyId);
 if(!Family||(ParentId!=Family->ParentA&&ParentId!=Family->ParentB))return false;
 Child->FollowingParent=ParentId;return true;
}
EAnomaliaZPrigimaliaLifeStage UAnomaliaZPrigimaliaFamilySubsystem::GetLifeStage(const FString& Id,double Days) const
{
 const FAnomaliaZPrigimaliaChildRecord* Child=Children.Find(Id);if(!Child)return EAnomaliaZPrigimaliaLifeStage::Newborn;
 const double Age=FMath::Max(0.,Days-Child->BornAtDays);
 return Age>=90.?EAnomaliaZPrigimaliaLifeStage::Adult:Age>=30.?EAnomaliaZPrigimaliaLifeStage::Teen:Age>=7.?EAnomaliaZPrigimaliaLifeStage::Child:Age>=1.?EAnomaliaZPrigimaliaLifeStage::Baby:EAnomaliaZPrigimaliaLifeStage::Newborn;
}
bool UAnomaliaZPrigimaliaFamilySubsystem::LearnSkill(const FString& Id,FName Skill,double Days)
{
 FAnomaliaZPrigimaliaChildRecord* Child=Children.Find(Id);
 if(!Child||Skill.IsNone()||!FMath::IsFinite(Days))return false;
 const EAnomaliaZPrigimaliaLifeStage Stage=GetLifeStage(Id,Days);
 if(Stage!=EAnomaliaZPrigimaliaLifeStage::Teen&&Stage!=EAnomaliaZPrigimaliaLifeStage::Adult)return false;
 Child->Skills.AddUnique(Skill);return true;
}
bool UAnomaliaZPrigimaliaFamilySubsystem::GetChild(const FString& Id,FAnomaliaZPrigimaliaChildRecord& OutChild) const
{
 const FAnomaliaZPrigimaliaChildRecord* Child=Children.Find(Id);if(!Child)return false;OutChild=*Child;return true;
}