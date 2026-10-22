#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "AnomaliaCryoSubsystem.generated.h"

USTRUCT(BlueprintType)
struct FAnomaliaCryoCreature
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
struct FAnomaliaCryoTerminal
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
 UPROPERTY(EditAnywhere,BlueprintReadWrite) TArray<FAnomaliaCryoCreature> Creatures;
};

UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaCryoSubsystem : public UWorldSubsystem
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable,Category="Anomalia|Cryo")
 bool RegisterTerminal(const FString& Id,const FString& OwnerId,FVector Location);
 /** Caller MUST provide authenticated actor identity/admin role from server state. */
 UFUNCTION(BlueprintCallable,Category="Anomalia|Cryo")
 bool CaptureCreature(const FString& TerminalId,const FString& ActorId,bool bIsServerAdmin,FAnomaliaCryoCreature Creature,bool bViaGun,float Distance,bool bAdminMode);
 /** World spawn MUST be validated and completed by server before releasing stored data. */
 UFUNCTION(BlueprintCallable,Category="Anomalia|Cryo")
 bool ReleaseCreature(const FString& TerminalId,const FString& CreatureId,const FString& ActorId,bool bIsServerAdmin,bool bSpawnAllowed,FAnomaliaCryoCreature& OutCreature);
 UFUNCTION(BlueprintCallable,Category="Anomalia|Cryo")
 bool ConfigureTerminal(const FString& TerminalId,const FString& ActorId,bool bIsServerAdmin,float Range,int32 Capacity,bool bAllowHybrids);
 UFUNCTION(BlueprintPure,Category="Anomalia|Cryo")
 bool GetTerminal(const FString& TerminalId,FAnomaliaCryoTerminal& OutTerminal) const;
private:
 TMap<FString,FAnomaliaCryoTerminal> Terminals;
 TSet<FString> StoredCreatureIds;
 bool CanAccess(const FAnomaliaCryoTerminal& Terminal,const FString& ActorId,bool bAdmin) const;
};