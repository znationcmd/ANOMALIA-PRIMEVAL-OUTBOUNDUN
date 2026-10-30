#include "AnomaliaZPrigimaliaVehicleKeyComponent.h"
#include "GameFramework/Actor.h"

UAnomaliaZPrigimaliaVehicleKeyComponent::UAnomaliaZPrigimaliaVehicleKeyComponent()
{
 PrimaryComponentTick.bCanEverTick=false;
}
bool UAnomaliaZPrigimaliaVehicleKeyComponent::IsServer() const
{
 return GetOwner()&&GetOwner()->HasAuthority();
}
bool UAnomaliaZPrigimaliaVehicleKeyComponent::AssignOwner(const FString& Id)
{
 if(!IsServer()||Id.IsEmpty()||!OwnerId.IsEmpty())return false;
 OwnerId=Id;AuthorizedPlayers.AddUnique(Id);return true;
}
bool UAnomaliaZPrigimaliaVehicleKeyComponent::HasKey(const FString& Id) const
{
 return !Id.IsEmpty()&&AuthorizedPlayers.Contains(Id);
}
bool UAnomaliaZPrigimaliaVehicleKeyComponent::GrantDuplicateKey(const FString& Owner,const FString& Recipient)
{
 if(!IsServer()||Owner.IsEmpty()||Owner!=OwnerId||Recipient.IsEmpty())return false;
 AuthorizedPlayers.AddUnique(Recipient);return true;
}
bool UAnomaliaZPrigimaliaVehicleKeyComponent::RevokeDuplicateKey(const FString& Owner,const FString& Recipient)
{
 if(!IsServer()||Owner!=OwnerId||Recipient==OwnerId)return false;
 return AuthorizedPlayers.Remove(Recipient)>0;
}
bool UAnomaliaZPrigimaliaVehicleKeyComponent::SetLocked(const FString& Id,bool NewLocked)
{
 if(!IsServer()||!HasKey(Id))return false;
 bLocked=NewLocked;
 if(bLocked)bIgnitionOn=false;
 return true;
}
bool UAnomaliaZPrigimaliaVehicleKeyComponent::SetIgnition(const FString& Id,bool NewIgnitionOn,bool HasFuel)
{
 if(!IsServer()||!HasKey(Id)||(NewIgnitionOn&&(bLocked||!HasFuel)))return false;
 bIgnitionOn=NewIgnitionOn;return true;
}