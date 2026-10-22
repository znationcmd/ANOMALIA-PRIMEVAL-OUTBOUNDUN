#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "AnomaliaPregnancySubsystem.generated.h"

USTRUCT(BlueprintType)
struct FAnomaliaPregnancyRecord
{
 GENERATED_BODY()
 UPROPERTY(BlueprintReadOnly) FString FamilyId;
 UPROPERTY(BlueprintReadOnly) FString CarryingPlayerId;
 UPROPERTY(BlueprintReadOnly) double StartedAtGameDays = 0.;
 UPROPERTY(BlueprintReadOnly) double DueAtGameDays = 0.;
};

UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaPregnancySubsystem : public UWorldSubsystem
{
 GENERATED_BODY()
public:
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Anomalia|Family", meta=(ClampMin="0.01"))
 double GestationGameDays = 7.;
 UFUNCTION(BlueprintCallable, Category="Anomalia|Family")
 bool BeginPregnancy(const FString& FamilyId, const FString& CarryingPlayerId, bool bAdultConsentA, bool bAdultConsentB, bool bCarrierConsent, double CurrentGameDays);
 UFUNCTION(BlueprintPure, Category="Anomalia|Family")
 bool GetProgress(const FString& FamilyId, double CurrentGameDays, float& OutProgress, bool& bReadyForBirth) const;
 UFUNCTION(BlueprintCallable, Category="Anomalia|Family")
 bool CompleteBirth(const FString& FamilyId, double CurrentGameDays, bool bConfirmedByCarrier);
 UFUNCTION(BlueprintPure, Category="Anomalia|Family")
 bool GetPregnancy(const FString& FamilyId, FAnomaliaPregnancyRecord& OutRecord) const;
private:
 TMap<FString,FAnomaliaPregnancyRecord> Pregnancies;
};