#include "AnomaliaVehicleKeyComponent.h"
#include "GameFramework/Actor.h"

UAnomaliaVehicleKeyComponent::UAnomaliaVehicleKeyComponent()
{
 PrimaryComponentTick.bCanEverTick=false;
}
bool UAnomaliaVehicleKeyComponent::IsServer() const
{
 return GetOwner()&&GetOwner()->HasAuthority();
}
bool UAnomaliaVehicleKeyComponent::AssignOwner(const FString& Id)
{
 if(!IsServer()||Id.IsEmpty()||!OwnerId.IsEmpty())return false;
 OwnerId=Id;AuthorizedPlayers.AddUnique(Id);return true;
}
bool UAnomaliaVehicleKeyComponent::HasKey(const FString& Id) const
{
 return !Id.IsEmpty()&&AuthorizedPlayers.Contains(Id);
}
bool UAnomaliaVehicleKeyComponent::GrantDuplicateKey(const FString& Owner,const FString& Recipient)
{
 if(!IsServer()||Owner.IsEmpty()||Owner!=OwnerId||Recipient.IsEmpty())return false;
 AuthorizedPlayers.AddUnique(Recipient);return true;
}
bool UAnomaliaVehicleKeyComponent::RevokeDuplicateKey(const FString& Owner,const FString& Recipient)
{
 if(!IsServer()||Owner!=OwnerId||Recipient==OwnerId)return false;
 return AuthorizedPlayers.Remove(Recipient)>0;
}
bool UAnomaliaVehicleKeyComponent::SetLocked(const FString& Id,bool NewLocked)
{
 if(!IsServer()||!HasKey(Id))return false;
 bLocked=NewLocked;
 if(bLocked)bIgnitionOn=false;
 return true;
}
bool UAnomaliaVehicleKeyComponent::SetIgnition(const FString& Id,bool NewIgnitionOn,bool HasFuel)
{
 if(!IsServer()||!HasKey(Id)||(NewIgnitionOn&&(bLocked||!HasFuel)))return false;
 bIgnitionOn=NewIgnitionOn;return true;
}