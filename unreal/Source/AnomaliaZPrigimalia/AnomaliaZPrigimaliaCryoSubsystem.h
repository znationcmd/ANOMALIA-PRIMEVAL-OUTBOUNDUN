#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "AnomaliaZPrigimaliaCryoSubsystem.generated.h"

USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaCryoCreature
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FString Id;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FString OwnerId;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FString Species;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) bool bTamed=false;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) bool bDead=false;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) bool bInCombat=false;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) bool bHybrid=false;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) bool bStored=false;
};

USTRUCT(BlueprintType)
struct FAnomaliaZPrigimaliaCryoTerminal
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FString Id;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FString OwnerId;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) FVector Location=FVector::ZeroVector;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) float Range=35.f;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) int32 Capacity=-1;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) bool bAllowHybrids=true;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) bool bCryoSickness=false;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) TArray<FString> AllowedIds;
 UPROPERTY(EditAnywhere,BlueprintReadWrite) TArray<FAnomaliaZPrigimaliaCryoCreature> Creatures;
};

UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaCryoSubsystem : public UWorldSubsystem
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable,Category="AnomaliaZPrigimalia|Cryo")
 bool RegisterTerminal(const FString& Id,const FString& OwnerId,FVector Location);
 /** Caller MUST provide authenticated actor identity/admin role from server state. */
 UFUNCTION(BlueprintCallable,Category="AnomaliaZPrigimalia|Cryo")
 bool CaptureCreature(const FString& TerminalId,const FString& ActorId,bool bIsServerAdmin,FAnomaliaZPrigimaliaCryoCreature Creature,bool bViaGun,float Distance,bool bAdminMode);
 /** World spawn MUST be validated and completed by server before releasing stored data. */
 UFUNCTION(BlueprintCallable,Category="AnomaliaZPrigimalia|Cryo")
 bool ReleaseCreature(const FString& TerminalId,const FString& CreatureId,const FString& ActorId,bool bIsServerAdmin,bool bSpawnAllowed,FAnomaliaZPrigimaliaCryoCreature& OutCreature);
 UFUNCTION(BlueprintCallable,Category="AnomaliaZPrigimalia|Cryo")
 bool ConfigureTerminal(const FString& TerminalId,const FString& ActorId,bool bIsServerAdmin,float Range,int32 Capacity,bool bAllowHybrids);
 UFUNCTION(BlueprintPure,Category="AnomaliaZPrigimalia|Cryo")
 bool GetTerminal(const FString& TerminalId,FAnomaliaZPrigimaliaCryoTerminal& OutTerminal) const;
private:
 TMap<FString,FAnomaliaZPrigimaliaCryoTerminal> Terminals;
 TSet<FString> StoredCreatureIds;
 bool CanAccess(const FAnomaliaZPrigimaliaCryoTerminal& Terminal,const FString& ActorId,bool bAdmin) const;
};