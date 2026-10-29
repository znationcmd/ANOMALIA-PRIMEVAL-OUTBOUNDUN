#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "AnomaliaZPrigimaliaFamilySubsystem.generated.h"

UENUM(BlueprintType)
enum class EAnomaliaZPrigimaliaLifeStage : uint8 { Newborn, Baby, Child, Teen, Adult };

USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaChildRecord
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
struct FAnomaliaZPrigimaliaFamilyRecord
{
 GENERATED_BODY()
 UPROPERTY(BlueprintReadOnly) FString Id;
 UPROPERTY(BlueprintReadOnly) FString ParentA;
 UPROPERTY(BlueprintReadOnly) FString ParentB;
 UPROPERTY(BlueprintReadOnly) TArray<FString> Children;
};

UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaFamilySubsystem : public UWorldSubsystem
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable, Category="AnomaliaZPrigimalia|Family")
 bool FoundFamily(const FString& FamilyId, const FString& ParentA, const FString& ParentB, bool bAdultA, bool bAdultB, bool bConsentA, bool bConsentB);
 UFUNCTION(BlueprintCallable, Category="AnomaliaZPrigimalia|Family")
 bool WelcomeChild(const FString& FamilyId, const FString& ChildId, const FString& Name, bool bMutualConsent, double CurrentGameDays);
 UFUNCTION(BlueprintCallable, Category="AnomaliaZPrigimalia|Family")
 bool CareForChild(const FString& ChildId, float Food, float Comfort, float Health);
 UFUNCTION(BlueprintCallable, Category="AnomaliaZPrigimalia|Family")
 bool FollowParent(const FString& ChildId, const FString& ParentId);
 UFUNCTION(BlueprintCallable, Category="AnomaliaZPrigimalia|Family")
 bool LearnSkill(const FString& ChildId, FName Skill, double CurrentGameDays);
 UFUNCTION(BlueprintPure, Category="AnomaliaZPrigimalia|Family")
 EAnomaliaZPrigimaliaLifeStage GetLifeStage(const FString& ChildId, double CurrentGameDays) const;
 UFUNCTION(BlueprintPure, Category="AnomaliaZPrigimalia|Family")
 bool GetChild(const FString& ChildId, FAnomaliaZPrigimaliaChildRecord& OutChild) const;
private:
 TMap<FString,FAnomaliaZPrigimaliaFamilyRecord> Families;
 TMap<FString,FAnomaliaZPrigimaliaChildRecord> Children;
};