#include "AnomaliaZPrigimaliaVehicleSurvival.h"
#include "AnomaliaZPrigimaliaChaosRoadVehicle.h"
#include "AnomaliaZPrigimaliaVehiclePanelComponent.h"
#include "../AnomaliaZPrigimaliaSurvivor.h"
#include "../AnomaliaZPrigimaliaInventoryComponent.h"
#include "../AnomaliaZPrigimaliaGameMode.h"
#include "../AnomaliaZPrigimaliaConfigLibrary.h"
#include "../AnomaliaZPrigimaliaEconomySubsystem.h"
#include "../AnomaliaZPrigimaliaLootSubsystem.h"
#include "../ReactiveWorld/AnomaliaZPrigimaliaWorldStateSubsystem.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Controller.h"
#include "Engine/World.h"
#include "Misc/SecureHash.h"
#include "Kismet/GameplayStatics.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Net/UnrealNetwork.h"
namespace
{
 FString Json(const TSharedPtr<FJsonObject>& Object){FString Raw;FJsonSerializer::Serialize(Object.ToSharedRef(),TJsonWriterFactory<>::Create(&Raw));return Raw;}
 bool Parse(const FString& Raw,TSharedPtr<FJsonObject>& Object){return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw),Object)&&Object.IsValid();}
 bool KeyId(FName Id){FGuid Value;return Id.ToString().StartsWith(TEXT("vehicle_key_"))&&FGuid::ParseExact(Id.ToString().Mid(12),EGuidFormats::Digits,Value)&&Value.IsValid();}
}
UAnomaliaZPrigimaliaVehicleSurvivalComponent::UAnomaliaZPrigimaliaVehicleSurvivalComponent(){SetIsReplicatedByDefault(true);PrimaryComponentTick.bCanEverTick=false;}
void UAnomaliaZPrigimaliaVehicleSurvivalComponent::BeginPlay()
{
 Super::BeginPlay();if(!bEnabled||!GetOwner()->HasAuthority())return;
 if(PersistentId.IsEmpty())
 {
  const FString Identity=UGameplayStatics::GetCurrentLevelName(this,true)+TEXT(":")+GetOwner()->GetFName().ToString();
  FTCHARToUTF8 Bytes(*Identity);PersistentId=TEXT("vehicle_")+FSHA1::HashBuffer(Bytes.Get(),Bytes.Length()).ToString().ToLower();
 }
 FString Error;auto* Services=GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaVehicleServiceSubsystem>();
 bReady=Services&&Services->RegisterVehicle(this,Error);ApplyLocks();
 if(!bReady)UE_LOG(LogTemp,Warning,TEXT("Vehicle services unavailable: %s"),*Error);
}
UAnomaliaZPrigimaliaInventoryComponent* UAnomaliaZPrigimaliaVehicleSurvivalComponent::GetCargo() const
{const auto* Car=Cast<AAnomaliaZPrigimaliaChaosRoadVehicle>(GetOwner());return Car?Car->CargoInventory.Get():nullptr;}
bool UAnomaliaZPrigimaliaVehicleSurvivalComponent::HasPhysicalKey(const AAnomaliaZPrigimaliaSurvivor* User) const
{return User&&User->InventoryComponent&&KeyId(State.KeyItemId)&&User->InventoryComponent->Stacks.ContainsByPredicate([&](const auto& Stack){return Stack.ItemId==State.KeyItemId&&Stack.Count==1;});}
bool UAnomaliaZPrigimaliaVehicleSurvivalComponent::CanStart(const AAnomaliaZPrigimaliaSurvivor* User) const
{return !bEnabled||(bReady&&!State.bLocked&&HasPhysicalKey(User)&&State.bBattery&&State.bRadiator&&State.bSparkPlug&&State.BatteryCharge>.02f&&State.EngineHealth>0.f&&State.TemperatureC<130.f);}
bool UAnomaliaZPrigimaliaVehicleSurvivalComponent::HasOpenPanel(FName Id) const
{
 const auto* Car=Cast<AAnomaliaZPrigimaliaChaosRoadVehicle>(GetOwner());if(!Car)return false;
 for(const auto& Panel:Car->AdditionalPanels)if(Panel&&Panel->PanelId==Id)
  return Panel->bOpen&&!Panel->bObstructed&&FMath::Abs(Panel->AngleDegrees-Panel->OpenAngleDegrees)<1.f;
 return false;
}
void UAnomaliaZPrigimaliaVehicleSurvivalComponent::ApplyLocks()
{
 if(!bEnabled||!GetOwner()->HasAuthority())return;auto* Car=Cast<AAnomaliaZPrigimaliaChaosRoadVehicle>(GetOwner());if(!Car)return;
 if(Car->DriverDoor)Car->DriverDoor->bLocked=State.bLocked;
 for(const auto& Panel:Car->AdditionalPanels)if(Panel)Panel->bLocked=State.bLocked;
 OnServicesUpdated.Broadcast();GetOwner()->ForceNetUpdate();
}
bool UAnomaliaZPrigimaliaVehicleSurvivalComponent::ValidateAccess(AAnomaliaZPrigimaliaSurvivor* User,EAnomaliaZPrigimaliaVehicleServiceAction Action,FString& Error) const
{
 const auto* Car=Cast<AAnomaliaZPrigimaliaChaosRoadVehicle>(GetOwner());
 if(!bEnabled||!bReady||!Car||!Car->HasAuthority()||!IsValid(User)||User->Health<=0||User->bSleeping||
    !User->GetController()||User->GetController()->GetPawn()!=User||!User->GetController()->IsPlayerController()||
    !User->InventoryComponent||User->InventoryComponent->IsPersistenceLocked()||!GetCargo()||GetCargo()->IsPersistenceLocked()||
    Car->Body->Bounds.GetBox().ComputeSquaredDistanceToPoint(User->GetActorLocation())>FMath::Square(200.f)||
    Car->bEngineRunning||Car->Chassis->GetPhysicsLinearVelocity().Size()>5.f)
 {Error=TEXT("Approchez du véhicule arrêté, moteur coupé, avec votre inventaire disponible.");return false;}
 FVector Target=Car->Body->Bounds.GetBox().GetClosestPointTo(User->GetActorLocation());
 FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaZPrigimaliaVehicleService),true);Query.AddIgnoredActor(User);FHitResult Hit;
 FVector Eye;FRotator View;User->GetActorEyesViewPoint(Eye,View);
 if(GetWorld()->LineTraceSingleByChannel(Hit,Eye,Target,ECC_Visibility,Query)&&Hit.GetActor()!=Car)
 {Error=TEXT("Un obstacle empêche l’accès au véhicule.");return false;}
 if(Action==EAnomaliaZPrigimaliaVehicleServiceAction::TakeInitialKey)return !State.bKeyIssued;
 if(Action==EAnomaliaZPrigimaliaVehicleServiceAction::ToggleLock)
 {
  if(!HasPhysicalKey(User)){Error=TEXT("Il faut porter la clé de ce véhicule.");return false;}
  if(!State.bLocked)
  {
   if(Car->DriverDoor&&(Car->DriverDoor->bOpen||FMath::Abs(Car->DriverDoor->AngleDegrees)>1.f)){Error=TEXT("Fermez les ouvrants avant de verrouiller.");return false;}
   for(const auto& Panel:Car->AdditionalPanels)if(Panel&&Panel->GetStaticMesh()&&(Panel->bOpen||FMath::Abs(Panel->AngleDegrees)>1.f))
    {Error=TEXT("Fermez les ouvrants avant de verrouiller.");return false;}
  }
  return true;
 }
 if(State.bLocked){Error=TEXT("Véhicule verrouillé.");return false;}
 const bool Cargo=Action==EAnomaliaZPrigimaliaVehicleServiceAction::Deposit||Action==EAnomaliaZPrigimaliaVehicleServiceAction::Withdraw||Action==EAnomaliaZPrigimaliaVehicleServiceAction::WithdrawToHands;
 const bool Battery=Action==EAnomaliaZPrigimaliaVehicleServiceAction::InstallBattery||Action==EAnomaliaZPrigimaliaVehicleServiceAction::RemoveBattery;
 if(!HasOpenPanel(Cargo?FName(TEXT("trunk")):Battery?BatteryAccessPanel:FName(TEXT("hood"))))
 {Error=Cargo?TEXT("Ouvrez complètement le coffre."):Battery?TEXT("Ouvrez l’accès à la batterie."):TEXT("Ouvrez complètement le capot.");return false;}
 return true;
}
bool UAnomaliaZPrigimaliaVehicleSurvivalComponent::Change(AAnomaliaZPrigimaliaSurvivor* User,EAnomaliaZPrigimaliaVehicleServiceAction Action,int32 StackId,int32 ExpectedCount,FString& Error)
{
 auto* Inventory=User->InventoryComponent.Get();auto* Cargo=GetCargo();
 if(Action==EAnomaliaZPrigimaliaVehicleServiceAction::TakeInitialKey)
 {if(!Inventory->TryAddItem(State.KeyItemId,1)){Error=TEXT("Faites une place pour la clé.");return false;}State.bKeyIssued=true;return true;}
 if(Action==EAnomaliaZPrigimaliaVehicleServiceAction::ToggleLock){State.bLocked=!State.bLocked;return true;}
 if(Action==EAnomaliaZPrigimaliaVehicleServiceAction::Deposit||Action==EAnomaliaZPrigimaliaVehicleServiceAction::Withdraw||Action==EAnomaliaZPrigimaliaVehicleServiceAction::WithdrawToHands)
 {
  auto* From=Action==EAnomaliaZPrigimaliaVehicleServiceAction::Deposit?Inventory:Cargo;
  auto* To=From==Inventory?Cargo:Inventory;
  const auto* Stack=From->Stacks.FindByPredicate([&](const auto& S){return S.StackId==StackId;});
  if(!Stack||ExpectedCount<1||Stack->Count!=ExpectedCount){Error=TEXT("La pile a changé ; actualisez le coffre.");return false;}
  if(!From->TryTransferStackTo(StackId,ExpectedCount,To,Action==EAnomaliaZPrigimaliaVehicleServiceAction::WithdrawToHands))
  {Error=TEXT("Pas assez de place ou de capacité de charge.");return false;}
  return true;
 }
 bool* Installed=nullptr;FName Item;bool Install=false;
 switch(Action)
 {
 case EAnomaliaZPrigimaliaVehicleServiceAction::InstallBattery:case EAnomaliaZPrigimaliaVehicleServiceAction::RemoveBattery:Installed=&State.bBattery;Item=TEXT("car_battery");Install=Action==EAnomaliaZPrigimaliaVehicleServiceAction::InstallBattery;break;
 case EAnomaliaZPrigimaliaVehicleServiceAction::InstallRadiator:case EAnomaliaZPrigimaliaVehicleServiceAction::RemoveRadiator:Installed=&State.bRadiator;Item=TEXT("radiator");Install=Action==EAnomaliaZPrigimaliaVehicleServiceAction::InstallRadiator;break;
 case EAnomaliaZPrigimaliaVehicleServiceAction::InstallSparkPlug:case EAnomaliaZPrigimaliaVehicleServiceAction::RemoveSparkPlug:Installed=&State.bSparkPlug;Item=TEXT("spark_plug");Install=Action==EAnomaliaZPrigimaliaVehicleServiceAction::InstallSparkPlug;break;
 case EAnomaliaZPrigimaliaVehicleServiceAction::FillCoolant:
  if(!State.bRadiator||State.Coolant>=1.f||!Inventory->TryRemoveItem(TEXT("water"),1)){Error=TEXT("Radiateur présent, eau et réservoir à remplir nécessaires.");return false;}
  State.Coolant=FMath::Min(1.f,State.Coolant+.25f);return true;
 default:Error=TEXT("Action inconnue.");return false;
 }
 if(Install && StackId>0)
 {
  const auto* Selected=Inventory->Stacks.FindByPredicate([&](const auto& Stack){return Stack.StackId==StackId;});
  if(!Selected||Selected->ItemId!=Item||Selected->Count!=ExpectedCount){Error=TEXT("Cette pièce ne correspond pas à cet emplacement.");return false;}
 }
 if(*Installed==Install||(Install?!Inventory->TryRemoveItem(Item,1):!Inventory->TryAddItem(Item,1)))
 {Error=TEXT("Pièce déjà dans cet état, absente de l’inventaire ou inventaire plein.");return false;}
 *Installed=Install;
 // Charge belongs to this installed system for now; swapping generic items never resets it.
 if(Item==TEXT("radiator"))State.Coolant=0.f;
 return true;
}
bool UAnomaliaZPrigimaliaVehicleSurvivalComponent::Execute(AAnomaliaZPrigimaliaSurvivor* User,EAnomaliaZPrigimaliaVehicleServiceAction Action,int32 StackId,int32 ExpectedCount,FString& Error)
{auto* Services=GetWorld()?GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaVehicleServiceSubsystem>():nullptr;return Services&&Services->Execute(this,User,Action,StackId,ExpectedCount,Error);}
void UAnomaliaZPrigimaliaVehicleSurvivalComponent::SimulateEngine(float Delta,float Demand)
{
 if(!bEnabled||!GetOwner()->HasAuthority()||!FMath::IsFinite(Delta)||Delta<=0)return;
 if(!bReady)
 {
  SaveElapsed+=Delta;if(SaveElapsed>=1.f){SaveElapsed=0;FString Error;if(auto* Services=GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaVehicleServiceSubsystem>())bReady=Services->RegisterVehicle(this,Error);}return;
 }
 auto* Car=Cast<AAnomaliaZPrigimaliaChaosRoadVehicle>(GetOwner());if(!Car)return;const float Time=Delta;
 if(Car->bEngineRunning)
 {
  if(State.bBattery)State.BatteryCharge=FMath::Min(1.f,State.BatteryCharge+Time*.001f);
  const bool Cooled=State.bRadiator&&State.Coolant>.01f;
  State.TemperatureC=Cooled?95.f+(State.TemperatureC-95.f)*FMath::Exp(-.015f*Time):State.TemperatureC+Time*(2.f+3.f*FMath::Clamp(Demand,0.f,1.f));
  if(State.TemperatureC>110.f)State.Coolant=FMath::Max(0.f,State.Coolant-Time*.002f);
  if(State.TemperatureC>120.f)State.EngineHealth=FMath::Max(0.f,State.EngineHealth-Time*(State.TemperatureC-120.f)*.0005f);
  if(!State.bBattery||!State.bSparkPlug||State.EngineHealth<=0.f||State.TemperatureC>=130.f)Car->SetEngineRunningOnServer(Car->GetController(),false);
 }
 else
 {
  State.TemperatureC=FMath::FInterpConstantTo(State.TemperatureC,20.f,Time,.15f);
  if(State.bBattery&&Car->bHeadlightsOn)State.BatteryCharge=FMath::Max(0.f,State.BatteryCharge-Time*.00005f);
 }
 SaveElapsed+=Time;if(SaveElapsed>=10.f){SaveElapsed=0;FString Error;if(auto* Services=GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaVehicleServiceSubsystem>())Services->SaveVehicle(this,Error);}
}
TSharedPtr<FJsonObject> UAnomaliaZPrigimaliaVehicleSurvivalComponent::Export() const
{
 auto Row=MakeShared<FJsonObject>();Row->SetStringField(TEXT("key"),State.KeyItemId.ToString());
 Row->SetBoolField(TEXT("keyIssued"),State.bKeyIssued);Row->SetBoolField(TEXT("locked"),State.bLocked);
 Row->SetBoolField(TEXT("battery"),State.bBattery);Row->SetBoolField(TEXT("radiator"),State.bRadiator);Row->SetBoolField(TEXT("sparkPlug"),State.bSparkPlug);
 Row->SetNumberField(TEXT("charge"),State.BatteryCharge);Row->SetNumberField(TEXT("coolant"),State.Coolant);
 Row->SetNumberField(TEXT("temperature"),State.TemperatureC);Row->SetNumberField(TEXT("engineHealth"),State.EngineHealth);
 if(GetCargo())Row->SetObjectField(TEXT("cargo"),GetCargo()->ExportInventoryObject());return Row;
}
bool UAnomaliaZPrigimaliaVehicleSurvivalComponent::Restore(const TSharedPtr<FJsonObject>& Row,FString& Error)
{
 FAnomaliaZPrigimaliaVehicleSurvivalState Next;FString Key;double Charge=0,Coolant=0,Temperature=0,Health=0;const TSharedPtr<FJsonObject>* Cargo=nullptr;
 if(!Row.IsValid()||!Row->TryGetStringField(TEXT("key"),Key)||!KeyId(FName(*Key))||
 !Row->TryGetBoolField(TEXT("keyIssued"),Next.bKeyIssued)||!Row->TryGetBoolField(TEXT("locked"),Next.bLocked)||
 !Row->TryGetBoolField(TEXT("battery"),Next.bBattery)||!Row->TryGetBoolField(TEXT("radiator"),Next.bRadiator)||!Row->TryGetBoolField(TEXT("sparkPlug"),Next.bSparkPlug)||
 !Row->TryGetNumberField(TEXT("charge"),Charge)||!Row->TryGetNumberField(TEXT("coolant"),Coolant)||!Row->TryGetNumberField(TEXT("temperature"),Temperature)||!Row->TryGetNumberField(TEXT("engineHealth"),Health)||
 !FMath::IsFinite(Charge)||Charge<0||Charge>1||!FMath::IsFinite(Coolant)||Coolant<0||Coolant>1||!FMath::IsFinite(Temperature)||Temperature< -60||Temperature>200||!FMath::IsFinite(Health)||Health<0||Health>1||
 !Row->TryGetObjectField(TEXT("cargo"),Cargo)||!Cargo||!GetCargo())
 {Error=TEXT("Sauvegarde véhicule invalide ; données conservées.");return false;}
 if(!GetCargo()->LoadInventoryObject(*Cargo,Error))return false;
 Next.KeyItemId=FName(*Key);Next.BatteryCharge=Charge;Next.Coolant=Coolant;Next.TemperatureC=Temperature;Next.EngineHealth=Health;State=Next;ApplyLocks();return true;
}
void UAnomaliaZPrigimaliaVehicleSurvivalComponent::OnRep_State(FAnomaliaZPrigimaliaVehicleSurvivalState Previous)
{
 if(Previous.KeyItemId!=State.KeyItemId||Previous.bKeyIssued!=State.bKeyIssued||Previous.bLocked!=State.bLocked||
    Previous.bBattery!=State.bBattery||Previous.bRadiator!=State.bRadiator||Previous.bSparkPlug!=State.bSparkPlug||
    !FMath::IsNearlyEqual(Previous.Coolant,State.Coolant,.001f))OnServicesUpdated.Broadcast();
}
void UAnomaliaZPrigimaliaVehicleSurvivalComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(UAnomaliaZPrigimaliaVehicleSurvivalComponent,State);DOREPLIFETIME(UAnomaliaZPrigimaliaVehicleSurvivalComponent,bReady);}

bool UAnomaliaZPrigimaliaVehicleServiceSubsystem::DoesSupportWorldType(EWorldType::Type Type) const{return Type==EWorldType::Game||Type==EWorldType::PIE;}
TStatId UAnomaliaZPrigimaliaVehicleServiceSubsystem::GetStatId() const{RETURN_QUICK_DECLARE_CYCLE_STAT(UAnomaliaZPrigimaliaVehicleServiceSubsystem,STATGROUP_Tickables);}
bool UAnomaliaZPrigimaliaVehicleServiceSubsystem::Configure(const FString& Scope,FString& Error)
{
 if(bConfigured||!GetWorld()||GetWorld()->GetNetMode()==NM_Client)return false;ServerId=Scope;FString Raw;
 if(UAnomaliaZPrigimaliaConfigLibrary::LoadWorldState(ServerId,TEXT("vehicle-services-v1"),Raw,Error))
 {
  double Version=0;const TSharedPtr<FJsonObject>* Vehicles=nullptr;
  if(!Parse(Raw,Ledger)||!Ledger->TryGetNumberField(TEXT("schemaVersion"),Version)||Version!=1||!Ledger->TryGetObjectField(TEXT("vehicles"),Vehicles)||!Vehicles||(*Vehicles)->Values.Num()>256)
  {Error=TEXT("Invalid vehicle ledger; existing state preserved");return false;}
 }
 else if(Error==TEXT("World state not found")){Ledger=MakeShared<FJsonObject>();Ledger->SetNumberField(TEXT("schemaVersion"),1);Ledger->SetObjectField(TEXT("vehicles"),MakeShared<FJsonObject>());Error.Empty();}
 else return false;
 bConfigured=true;if(!Recover(Error))return false;bReady=Persist(Error);return bReady;
}
bool UAnomaliaZPrigimaliaVehicleServiceSubsystem::Persist(FString& Error)
{return Ledger.IsValid()&&UAnomaliaZPrigimaliaConfigLibrary::SaveWorldState(ServerId,TEXT("vehicle-services-v1"),Json(Ledger),Error);}
bool UAnomaliaZPrigimaliaVehicleServiceSubsystem::HasPendingPlayer(const FString& Id) const
{const TSharedPtr<FJsonObject>* P=nullptr;FString Player;return Ledger.IsValid()&&Ledger->TryGetObjectField(TEXT("pending"),P)&&P&&(*P)->TryGetStringField(TEXT("playerId"),Player)&&Player==Id;}
bool UAnomaliaZPrigimaliaVehicleServiceSubsystem::Recover(FString& Error)
{
 if(!Ledger.IsValid()||!Ledger->HasField(TEXT("pending")))return true;const TSharedPtr<FJsonObject>* P=nullptr;FString Id,Profile;
 if(!Ledger->TryGetObjectField(TEXT("pending"),P)||!P||!(*P)->TryGetStringField(TEXT("playerId"),Id)||!(*P)->TryGetStringField(TEXT("profileAfter"),Profile))return false;
 const auto Pending=*P;if(!UAnomaliaZPrigimaliaConfigLibrary::SavePlayerProfile(ServerId,Id,Profile,Error))return false;
 Ledger->RemoveField(TEXT("pending"));if(!Persist(Error)){Ledger->SetObjectField(TEXT("pending"),Pending);return false;}
 if(auto* Inventory=PendingInventory.Get()){Inventory->bPersistenceLocked=false;Inventory->Commit(TArray<FAnomaliaZPrigimaliaInventoryStack>(Inventory->Stacks));}PendingInventory.Reset();bReady=true;return true;
}
void UAnomaliaZPrigimaliaVehicleServiceSubsystem::Tick(float Delta)
{if(!bConfigured||GetWorld()->GetNetMode()==NM_Client)return;Elapsed+=Delta;if(Elapsed<1.f)return;Elapsed=0;FString Error;Recover(Error);}
bool UAnomaliaZPrigimaliaVehicleServiceSubsystem::RegisterVehicle(UAnomaliaZPrigimaliaVehicleSurvivalComponent* C,FString& Error)
{
 if(!bReady||!C||!C->GetOwner()->HasAuthority()||C->PersistentId.IsEmpty()||!C->GetCargo())return false;
 auto Vehicles=Ledger->GetObjectField(TEXT("vehicles"));const TSharedPtr<FJsonObject>* Existing=nullptr;
 if(Vehicles->TryGetObjectField(C->PersistentId,Existing))return Existing&&C->Restore(*Existing,Error);
 if(Vehicles->Values.Num()>=256)return false;
 C->State.KeyItemId=FName(*(TEXT("vehicle_key_")+FGuid::NewGuid().ToString(EGuidFormats::Digits)));
 Vehicles->SetObjectField(C->PersistentId,C->Export());if(!Persist(Error)){Vehicles->RemoveField(C->PersistentId);return false;}return true;
}
bool UAnomaliaZPrigimaliaVehicleServiceSubsystem::SaveVehicle(UAnomaliaZPrigimaliaVehicleSurvivalComponent* C,FString& Error)
{
 if(!bReady||!C||!C->bReady||!C->GetOwner()->HasAuthority()||Ledger->HasField(TEXT("pending")))return false;
 auto Vehicles=Ledger->GetObjectField(TEXT("vehicles"));const auto Before=Vehicles->GetObjectField(C->PersistentId);
 Vehicles->SetObjectField(C->PersistentId,C->Export());if(!Persist(Error)){Vehicles->SetObjectField(C->PersistentId,Before);return false;}return true;
}
bool UAnomaliaZPrigimaliaVehicleServiceSubsystem::Execute(UAnomaliaZPrigimaliaVehicleSurvivalComponent* C,AAnomaliaZPrigimaliaSurvivor* User,EAnomaliaZPrigimaliaVehicleServiceAction Action,int32 StackId,int32 ExpectedCount,FString& Error)
{
 Error.Empty();if(!bReady||!C||C->GetWorld()!=GetWorld()||!User||User->GetWorld()!=GetWorld()||!C->ValidateAccess(User,Action,Error)||Ledger->HasField(TEXT("pending")))return false;
 const auto* Mode=GetWorld()->GetAuthGameMode<AAnomaliaZPrigimaliaGameMode>();const FString Player=Mode?Mode->GetPersistentPlayerId(User->GetController()):FString();
 const auto* Loot=GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaLootSubsystem>();const auto* Economy=GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaEconomySubsystem>();const auto* WorldState=GetWorld()->GetSubsystem<UAnomaliaZPrigimaliaWorldStateSubsystem>();
 if(Player.IsEmpty()||(Loot&&Loot->HasPendingPlayer(Player))||(Economy&&Economy->HasPendingPlayer(Player))||(WorldState&&WorldState->HasPendingPlayer(Player)))return false;
 auto* Inventory=User->InventoryComponent.Get();auto* Cargo=C->GetCargo();const auto BeforeStacks=Inventory->Stacks;const int32 BeforeId=Inventory->NextStackId;const auto BeforeCargo=Cargo->Stacks;const int32 CargoId=Cargo->NextStackId;
 const auto BeforeState=C->State;const FString BeforeLedger=Json(Ledger);
 auto Rollback=[&](){Inventory->Stacks=BeforeStacks;Inventory->NextStackId=BeforeId;Cargo->Stacks=BeforeCargo;Cargo->NextStackId=CargoId;C->State=BeforeState;Inventory->bSuppressNotifications=false;Cargo->bSuppressNotifications=false;};
 Inventory->bSuppressNotifications=true;Cargo->bSuppressNotifications=true;
 if(!C->Change(User,Action,StackId,ExpectedCount,Error)){Rollback();return false;}
 FString Profile;if(!Inventory->BuildInventoryProfile(ServerId,Player,Profile,Error)){Rollback();return false;}
 Ledger->GetObjectField(TEXT("vehicles"))->SetObjectField(C->PersistentId,C->Export());auto Pending=MakeShared<FJsonObject>();Pending->SetStringField(TEXT("playerId"),Player);Pending->SetStringField(TEXT("profileAfter"),Profile);Ledger->SetObjectField(TEXT("pending"),Pending);
 if(!Persist(Error)){Parse(BeforeLedger,Ledger);Rollback();return false;}
 Inventory->bPersistenceLocked=true;Inventory->bSuppressNotifications=false;Cargo->bSuppressNotifications=false;PendingInventory=Inventory;bReady=false;
 C->ApplyLocks();Cargo->Commit(TArray<FAnomaliaZPrigimaliaInventoryStack>(Cargo->Stacks));
 if(!Recover(Error))UE_LOG(LogTemp,Error,TEXT("Vehicle inventory exchange journal retained for recovery: %s"),*Error);
 return true;
}
