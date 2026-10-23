#include "AnomaliaPregnancySubsystem.h"

bool UAnomaliaPregnancySubsystem::BeginPregnancy(const FString& FamilyId,const FString& Carrier,bool ConsentA,bool ConsentB,bool CarrierConsent,double Days)
{
 if(FamilyId.IsEmpty()||Carrier.IsEmpty()||!ConsentA||!ConsentB||!CarrierConsent||!FMath::IsFinite(Days)||Pregnancies.Contains(FamilyId))return false;
 FAnomaliaPregnancyRecord Record;
 Record.FamilyId=FamilyId;Record.CarryingPlayerId=Carrier;
 Record.StartedAtGameDays=Days;
 Record.DueAtGameDays=Days+FMath::Max(.01,GestationGameDays);
 Pregnancies.Add(FamilyId,MoveTemp(Record));
 return true;
}
bool UAnomaliaPregnancySubsystem::GetProgress(const FString& FamilyId,double Days,float& Progress,bool& Ready) const
{
 Progress=0.f;Ready=false;
 const FAnomaliaPregnancyRecord* Record=Pregnancies.Find(FamilyId);
 if(!Record||!FMath::IsFinite(Days))return false;
 const double Duration=FMath::Max(.01,Record->DueAtGameDays-Record->StartedAtGameDays);
 Progress=static_cast<float>(FMath::Clamp((Days-Record->StartedAtGameDays)/Duration,0.,1.));
 Ready=Days>=Record->DueAtGameDays;
 return true;
}
bool UAnomaliaPregnancySubsystem::CompleteBirth(const FString& FamilyId,double Days,bool Confirmed)
{
 float Progress=0.f;bool Ready=false;
 if(!Confirmed||!GetProgress(FamilyId,Days,Progress,Ready)||!Ready)return false;
 return Pregnancies.Remove(FamilyId)>0;
}
bool UAnomaliaPregnancySubsystem::GetPregnancy(const FString& FamilyId,FAnomaliaPregnancyRecord& OutRecord) const
{
 const FAnomaliaPregnancyRecord* Record=Pregnancies.Find(FamilyId);
 if(!Record)return false;
 OutRecord=*Record;return true;
}