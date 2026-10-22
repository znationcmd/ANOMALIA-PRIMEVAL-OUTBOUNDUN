#include "AnomaliaFamilySubsystem.h"
bool UAnomaliaFamilySubsystem::FoundFamily(const FString& Id,const FString& A,const FString& B,bool AdultA,bool AdultB,bool ConsentA,bool ConsentB)
{
 if(Id.IsEmpty()||A.IsEmpty()||B.IsEmpty()||A==B||!AdultA||!AdultB||!ConsentA||!ConsentB||Families.Contains(Id))return false;
 FAnomaliaFamilyRecord Record;Record.Id=Id;Record.ParentA=A;Record.ParentB=B;Families.Add(Id,MoveTemp(Record));return true;
}
bool UAnomaliaFamilySubsystem::WelcomeChild(const FString& FamilyId,const FString& ChildId,const FString& Name,bool Consent,double Days)
{
 FAnomaliaFamilyRecord* Family=Families.Find(FamilyId);
 if(!Family||ChildId.IsEmpty()||Children.Contains(ChildId)||!Consent||!FMath::IsFinite(Days))return false;
 FAnomaliaChildRecord Child;Child.Id=ChildId;Child.FamilyId=FamilyId;Child.Name=Name.IsEmpty()?TEXT("Enfant"):Name;Child.BornAtDays=Days;
 Children.Add(ChildId,MoveTemp(Child));Family->Children.Add(ChildId);return true;
}
bool UAnomaliaFamilySubsystem::CareForChild(const FString& Id,float Food,float Comfort,float Health)
{
 FAnomaliaChildRecord* Child=Children.Find(Id);if(!Child)return false;
 Child->Food=FMath::Clamp(Child->Food+FMath::Max(0.f,Food),0.f,100.f);
 Child->Comfort=FMath::Clamp(Child->Comfort+FMath::Max(0.f,Comfort),0.f,100.f);
 Child->Health=FMath::Clamp(Child->Health+FMath::Max(0.f,Health),0.f,100.f);return true;
}
bool UAnomaliaFamilySubsystem::FollowParent(const FString& Id,const FString& ParentId)
{
 FAnomaliaChildRecord* Child=Children.Find(Id);if(!Child)return false;
 const FAnomaliaFamilyRecord* Family=Families.Find(Child->FamilyId);
 if(!Family||(ParentId!=Family->ParentA&&ParentId!=Family->ParentB))return false;
 Child->FollowingParent=ParentId;return true;
}
EAnomaliaLifeStage UAnomaliaFamilySubsystem::GetLifeStage(const FString& Id,double Days) const
{
 const FAnomaliaChildRecord* Child=Children.Find(Id);if(!Child)return EAnomaliaLifeStage::Newborn;
 const double Age=FMath::Max(0.,Days-Child->BornAtDays);
 return Age>=90.?EAnomaliaLifeStage::Adult:Age>=30.?EAnomaliaLifeStage::Teen:Age>=7.?EAnomaliaLifeStage::Child:Age>=1.?EAnomaliaLifeStage::Baby:EAnomaliaLifeStage::Newborn;
}
bool UAnomaliaFamilySubsystem::LearnSkill(const FString& Id,FName Skill,double Days)
{
 FAnomaliaChildRecord* Child=Children.Find(Id);
 if(!Child||Skill.IsNone()||!FMath::IsFinite(Days))return false;
 const EAnomaliaLifeStage Stage=GetLifeStage(Id,Days);
 if(Stage!=EAnomaliaLifeStage::Teen&&Stage!=EAnomaliaLifeStage::Adult)return false;
 Child->Skills.AddUnique(Skill);return true;
}
bool UAnomaliaFamilySubsystem::GetChild(const FString& Id,FAnomaliaChildRecord& OutChild) const
{
 const FAnomaliaChildRecord* Child=Children.Find(Id);if(!Child)return false;OutChild=*Child;return true;
}