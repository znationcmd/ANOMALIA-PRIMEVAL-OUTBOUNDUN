#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "AnomaliaZPrigimaliaPregnancySubsystem.generated.h"

USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaPregnancyRecord
{
 GENERATED_BODY()
 UPROPERTY(BlueprintReadOnly) FString FamilyId;
 UPROPERTY(BlueprintReadOnly) FString CarryingPlayerId;
 UPROPERTY(BlueprintReadOnly) double StartedAtGameDays = 0.;
 UPROPERTY(BlueprintReadOnly) double DueAtGameDays = 0.;
};

UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaPregnancySubsystem : public UWorldSubsystem
{
 GENERATED_BODY()
public:
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="AnomaliaZPrigimalia|Family", meta=(ClampMin="0.01"))
 double GestationGameDays = 7.;
 UFUNCTION(BlueprintCallable, Category="AnomaliaZPrigimalia|Family")
 bool BeginPregnancy(const FString& FamilyId, const FString& CarryingPlayerId, bool bAdultConsentA, bool bAdultConsentB, bool bCarrierConsent, double CurrentGameDays);
 UFUNCTION(BlueprintPure, Category="AnomaliaZPrigimalia|Family")
 bool GetProgress(const FString& FamilyId, double CurrentGameDays, float& OutProgress, bool& bReadyForBirth) const;
 UFUNCTION(BlueprintCallable, Category="AnomaliaZPrigimalia|Family")
 bool CompleteBirth(const FString& FamilyId, double CurrentGameDays, bool bConfirmedByCarrier);
 UFUNCTION(BlueprintPure, Category="AnomaliaZPrigimalia|Family")
 bool GetPregnancy(const FString& FamilyId, FAnomaliaZPrigimaliaPregnancyRecord& OutRecord) const;
private:
 TMap<FString,FAnomaliaZPrigimaliaPregnancyRecord> Pregnancies;
};