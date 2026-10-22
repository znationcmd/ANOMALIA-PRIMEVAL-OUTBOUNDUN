#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AnomaliaVehicleKeyComponent.generated.h"

UCLASS(ClassGroup=(Anomalia),meta=(BlueprintSpawnableComponent))
class ANOMALIAPRIMEVAL_API UAnomaliaVehicleKeyComponent : public UActorComponent
{
 GENERATED_BODY()
public:
 UAnomaliaVehicleKeyComponent();
 /** Owner identity and key grants are controlled by trusted server code. */
 UFUNCTION(BlueprintCallable,BlueprintAuthorityOnly,Category="ANOMALIA|Vehicle|Keys")
 bool AssignOwner(const FString& PersistentPlayerId);
 UFUNCTION(BlueprintCallable,BlueprintAuthorityOnly,Category="ANOMALIA|Vehicle|Keys")
 bool GrantDuplicateKey(const FString& OwnerPlayerId,const FString& RecipientPlayerId);
 UFUNCTION(BlueprintCallable,BlueprintAuthorityOnly,Category="ANOMALIA|Vehicle|Keys")
 bool RevokeDuplicateKey(const FString& OwnerPlayerId,const FString& RecipientPlayerId);
 UFUNCTION(BlueprintCallable,BlueprintAuthorityOnly,Category="ANOMALIA|Vehicle|Keys")
 bool SetLocked(const FString& PlayerId,bool bNewLocked);
 UFUNCTION(BlueprintCallable,BlueprintAuthorityOnly,Category="ANOMALIA|Vehicle|Keys")
 bool SetIgnition(const FString& PlayerId,bool bNewIgnitionOn,bool bHasFuel);
 UFUNCTION(BlueprintPure,Category="ANOMALIA|Vehicle|Keys")
 bool HasKey(const FString& PlayerId) const;
 UFUNCTION(BlueprintPure,Category="ANOMALIA|Vehicle|Keys")
 bool IsLocked() const { return bLocked; }
 UFUNCTION(BlueprintPure,Category="ANOMALIA|Vehicle|Keys")
 bool IsIgnitionOn() const { return bIgnitionOn; }
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="ANOMALIA|Vehicle|Keys")
 FString OwnerId;
private:
 UPROPERTY() TArray<FString> AuthorizedPlayers;
 UPROPERTY() bool bLocked=false;
 UPROPERTY() bool bIgnitionOn=false;
 bool IsServer() const;
};