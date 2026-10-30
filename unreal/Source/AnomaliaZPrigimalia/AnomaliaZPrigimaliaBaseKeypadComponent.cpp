#include "AnomaliaZPrigimaliaBaseKeypadComponent.h"
#include "GameFramework/Actor.h"
#include "Misc/Guid.h"
#include "Misc/SecureHash.h"

UAnomaliaZPrigimaliaBaseKeypadComponent::UAnomaliaZPrigimaliaBaseKeypadComponent()
{
 PrimaryComponentTick.bCanEverTick=false;
}
bool UAnomaliaZPrigimaliaBaseKeypadComponent::IsServer() const
{
 return GetOwner()&&GetOwner()->HasAuthority();
}
bool UAnomaliaZPrigimaliaBaseKeypadComponent::ValidCode(const FString& Code)
{
 if(Code.Len()<4||Code.Len()>8)return false;
 for(TCHAR C:Code)if(C<TEXT('0')||C>TEXT('9'))return false;
 return true;
}
FString UAnomaliaZPrigimaliaBaseKeypadComponent::ComputeVerifier(const FString& Salt,const FString& Code)
{
 return FMD5::HashAnsiString(*(Salt+TEXT(":")+Code));
}
bool UAnomaliaZPrigimaliaBaseKeypadComponent::ConfigureCode(const FString& Owner,const FString& Code)
{
 if(!IsServer()||!OwnerId.IsEmpty()||Owner.IsEmpty()||!ValidCode(Code))return false;
 OwnerId=Owner;
 CodeSalt=FGuid::NewGuid().ToString(EGuidFormats::Digits);
 CodeVerifier=ComputeVerifier(CodeSalt,Code);
 bLocked=true;return true;
}
bool UAnomaliaZPrigimaliaBaseKeypadComponent::ChangeCode(const FString& Owner,const FString& Code)
{
 if(!IsServer()||Owner.IsEmpty()||Owner!=OwnerId||!ValidCode(Code))return false;
 CodeSalt=FGuid::NewGuid().ToString(EGuidFormats::Digits);
 CodeVerifier=ComputeVerifier(CodeSalt,Code);
 FailedAttempts=0;LockedOutUntil=0.;bLocked=true;return true;
}
bool UAnomaliaZPrigimaliaBaseKeypadComponent::TryUnlock(const FString& Player,const FString& Code,double Now)
{
 if(!IsServer()||OwnerId.IsEmpty()||Player.IsEmpty()||!FMath::IsFinite(Now)||Now<LockedOutUntil)return false;
 const bool Match=ValidCode(Code)&&ComputeVerifier(CodeSalt,Code)==CodeVerifier;
 if(!Match)
 {
  ++FailedAttempts;
  if(FailedAttempts>=5){LockedOutUntil=Now+60.;FailedAttempts=0;}
  return false;
 }
 FailedAttempts=0;bLocked=false;return true;
}
bool UAnomaliaZPrigimaliaBaseKeypadComponent::Lock(const FString& Owner)
{
 if(!IsServer()||Owner.IsEmpty()||Owner!=OwnerId)return false;
 bLocked=true;return true;
}