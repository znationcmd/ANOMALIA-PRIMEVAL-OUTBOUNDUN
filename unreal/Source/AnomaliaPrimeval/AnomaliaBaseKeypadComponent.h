#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AnomaliaBaseKeypadComponent.generated.h"

/** Server-side logical base lock. Never replicate PIN or its verifier. */
UCLASS(ClassGroup=(Anomalia),meta=(BlueprintSpawnableComponent))
class ANOMALIAPRIMEVAL_API UAnomaliaBaseKeypadComponent : public UActorComponent
{
 GENERATED_BODY()
public:
 UAnomaliaBaseKeypadComponent();
 UFUNCTION(BlueprintCallable,BlueprintAuthorityOnly,Category="ANOMALIA|Base|Keypad")
 bool ConfigureCode(const FString& OwnerPlayerId,const FString& NewCode);
 UFUNCTION(BlueprintCallable,BlueprintAuthorityOnly,Category="ANOMALIA|Base|Keypad")
 bool ChangeCode(const FString& OwnerPlayerId,const FString& NewCode);
 UFUNCTION(BlueprintCallable,BlueprintAuthorityOnly,Category="ANOMALIA|Base|Keypad")
 bool TryUnlock(const FString& PlayerId,const FString& Code,double NowSeconds);
 UFUNCTION(BlueprintCallable,BlueprintAuthorityOnly,Category="ANOMALIA|Base|Keypad")
 bool Lock(const FString& OwnerPlayerId);
 UFUNCTION(BlueprintPure,Category="ANOMALIA|Base|Keypad")
 bool IsLocked() const { return bLocked; }
 UFUNCTION(BlueprintPure,Category="ANOMALIA|Base|Keypad")
 bool IsConfigured() const { return !OwnerId.IsEmpty(); }
private:
 UPROPERTY() FString OwnerId;
 FString CodeVerifier;
 FString CodeSalt;
 bool bLocked=true;
 int32 FailedAttempts=0;
 double LockedOutUntil=0.;
 bool IsServer() const;
 static bool ValidCode(const FString& Code);
 static FString ComputeVerifier(const FString& Salt,const FString& Code);
};