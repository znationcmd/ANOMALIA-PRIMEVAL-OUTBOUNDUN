#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "AnomaliaFamilySubsystem.generated.h"

UENUM(BlueprintType)
enum class EAnomaliaLifeStage : uint8 { Newborn, Baby, Child, Teen, Adult };

USTRUCT(BlueprintType)
struct FAnomaliaChildRecord
{
 GENERATED_BODY()
 UPROPERTY(BlueprintReadOnly) FString Id;
 UPROPERTY(BlueprintReadOnly) FString FamilyId;
 UPROPERTY(BlueprintReadOnly) FString Name;
 UPROPERTY(BlueprintReadOnly) double BornAtDays = 0.;
 UPROPERTY(BlueprintReadOnly) float Food = 100.f;
 UPROPERTY(BlueprintReadOnly) float Comfort = 100.f;
 UPROPERTY(BlueprintReadOnly) float Health = 100.f;
 UPROPERTY(BlueprintReadOnly) FString FollowingParent;
 UPROPERTY(BlueprintReadOnly) TArray<FName> Skills;
};

USTRUCT(BlueprintType)
struct FAnomaliaFamilyRecord
{
 GENERATED_BODY()
 UPROPERTY(BlueprintReadOnly) FString Id;
 UPROPERTY(BlueprintReadOnly) FString ParentA;
 UPROPERTY(BlueprintReadOnly) FString ParentB;
 UPROPERTY(BlueprintReadOnly) TArray<FString> Children;
};

UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaFamilySubsystem : public UWorldSubsystem
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable, Category="Anomalia|Family")
 bool FoundFamily(const FString& FamilyId, const FString& ParentA, const FString& ParentB, bool bAdultA, bool bAdultB, bool bConsentA, bool bConsentB);
 UFUNCTION(BlueprintCallable, Category="Anomalia|Family")
 bool WelcomeChild(const FString& FamilyId, const FString& ChildId, const FString& Name, bool bMutualConsent, double CurrentGameDays);
 UFUNCTION(BlueprintCallable, Category="Anomalia|Family")
 bool CareForChild(const FString& ChildId, float Food, float Comfort, float Health);
 UFUNCTION(BlueprintCallable, Category="Anomalia|Family")
 bool FollowParent(const FString& ChildId, const FString& ParentId);
 UFUNCTION(BlueprintCallable, Category="Anomalia|Family")
 bool LearnSkill(const FString& ChildId, FName Skill, double CurrentGameDays);
 UFUNCTION(BlueprintPure, Category="Anomalia|Family")
 EAnomaliaLifeStage GetLifeStage(const FString& ChildId, double CurrentGameDays) const;
 UFUNCTION(BlueprintPure, Category="Anomalia|Family")
 bool GetChild(const FString& ChildId, FAnomaliaChildRecord& OutChild) const;
private:
 TMap<FString,FAnomaliaFamilyRecord> Families;
 TMap<FString,FAnomaliaChildRecord> Children;
};