#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "../Vehicles/AnomaliaVehicleSurvival.h"
#include "../Vehicles/AnomaliaChaosRoadVehicle.h"
#include "../AnomaliaInventoryComponent.h"
#include "../AnomaliaSurvivor.h"
#include "../AnomaliaConfigLibrary.h"
#include "Engine/World.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaVehicleSurvivalTest,"Anomalia.Native.VehicleKeyPartsCargoAndRecovery",
 EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FAnomaliaVehicleSurvivalTest::RunTest(const FString&)
{
 const FString Scope=TEXT("vehicle-test-")+FGuid::NewGuid().ToString(EGuidFormats::Digits);FString Error,Raw;
 auto* World=UWorld::CreateWorld(EWorldType::Game,false);if(!TestNotNull(TEXT("Isolated vehicle persistence world"),World))return false;
 auto* Services=World->GetSubsystem<UAnomaliaVehicleServiceSubsystem>();
 if(!Services||!TestTrue(TEXT("Configure independent vehicle journal"),Services->Configure(Scope,Error))){AddError(Error);World->DestroyWorld(false);return false;}
 auto* Car=World->SpawnActor<AAnomaliaChaosRoadVehicle>();auto* Other=World->SpawnActor<AAnomaliaChaosRoadVehicle>();auto* User=World->SpawnActor<AAnomaliaSurvivor>();
 auto* Systems=Car->SurvivalSystems.Get();Systems->PersistentId=TEXT("authored-e39");Systems->bReady=Services->RegisterVehicle(Systems,Error);
 Other->SurvivalSystems->PersistentId=TEXT("another-e39");Other->SurvivalSystems->bReady=Services->RegisterVehicle(Other->SurvivalSystems,Error);
 TestTrue(TEXT("Register stable authored identity"),Systems->bReady);
 TestFalse(TEXT("Complete car without matching carried object cannot start"),Systems->CanStart(User));
 TestTrue(TEXT("Genuine bound key is a real inventory object"),User->InventoryComponent->TryAddItem(Systems->State.KeyItemId,1));
 TestTrue(TEXT("Correct carried key satisfies start interlock"),Systems->CanStart(User));
 TestFalse(TEXT("Key from another E39 never satisfies ignition"),Other->SurvivalSystems->CanStart(User));
 TestFalse(TEXT("Malformed key names are not arbitrary inventory items"),User->InventoryComponent->TryAddItem(TEXT("vehicle_key_forged"),1));
 Systems->State.bBattery=false;TestFalse(TEXT("Missing battery blocks ignition"),Systems->CanStart(User));Systems->State.bBattery=true;
 Systems->State.bRadiator=false;TestFalse(TEXT("Missing required radiator blocks ignition"),Systems->CanStart(User));Systems->State.bRadiator=true;
 Systems->State.bSparkPlug=false;TestFalse(TEXT("Missing ignition plug blocks ignition"),Systems->CanStart(User));Systems->State.bSparkPlug=true;
 Systems->State.bLocked=true;TestFalse(TEXT("Locked ignition refuses even the matching key"),Systems->CanStart(User));Systems->State.bLocked=false;
 Systems->State.EngineHealth=0;TestFalse(TEXT("Destroyed engine refuses ignition"),Systems->CanStart(User));Systems->State.EngineHealth=1;
 auto* Inventory=User->InventoryComponent.Get();auto* Cargo=Car->CargoInventory.Get();
 TestEqual(TEXT("E39 cargo has requested initial 1000-cell grid"),Cargo->Compartments[0].Width*Cargo->Compartments[0].Height,1000);
 TestTrue(TEXT("Seed ordinary cargo in the real survivor inventory"),Inventory->TryAddItem(TEXT("wood"),3));
 const auto* Wood=Inventory->Stacks.FindByPredicate([](const auto& S){return S.ItemId==TEXT("wood");});
 if(!TestNotNull(TEXT("Actual selected stack"),Wood)){World->DestroyWorld(false);return false;}
 const int32 Selected=Wood->StackId;
 TestFalse(TEXT("Stale displayed count cannot move a different quantity"),Inventory->TryTransferStackTo(Selected,2,Cargo));
 TestTrue(TEXT("Whole selected stack moves to cargo"),Inventory->TryTransferStackTo(Selected,3,Cargo));
 TestFalse(TEXT("Source stack cannot be replayed for duplication"),Inventory->TryTransferStackTo(Selected,3,Cargo));
 TestEqual(TEXT("Destination retains all three items"),Cargo->Stacks[0].Count,3);
 TestFalse(TEXT("Cargo cannot transfer to itself"),Cargo->TryTransferStackTo(Cargo->Stacks[0].StackId,3,Cargo));
 TestTrue(TEXT("Square-style withdrawal goes to the real hands compartment"),Cargo->TryTransferStackTo(Cargo->Stacks[0].StackId,3,Inventory,true));
 const auto* Held=Inventory->Stacks.FindByPredicate([](const auto& S){return S.ItemId==TEXT("wood");});
 TestTrue(TEXT("Withdrawn stack is actually in hands"),Held&&Held->ContainerId==TEXT("hands"));
 if(!Held){World->DestroyWorld(false);return false;}
 TestTrue(TEXT("Preserve unrelated player profile fields"),UAnomaliaConfigLibrary::SavePlayerProfile(Scope,TEXT("native-player"),TEXT("{\"extension\":{\"keep\":true}}"),Error));
 TestTrue(TEXT("Persist before interrupted cargo transfer"),Inventory->SaveInventoryToPlayerProfile(Scope,TEXT("native-player"),Error));
 TestTrue(TEXT("Prepare real cargo side of interrupted transaction"),Inventory->TryTransferStackTo(Held->StackId,3,Cargo));
 TestTrue(TEXT("Persist vehicle side"),Services->SaveVehicle(Systems,Error));
 FString After;TestTrue(TEXT("Build player after-image"),Inventory->BuildInventoryProfile(Scope,TEXT("native-player"),After,Error));
 TestTrue(TEXT("Read journal for controlled interruption fixture"),UAnomaliaConfigLibrary::LoadWorldState(Scope,TEXT("vehicle-services-v1"),Raw,Error));
 TSharedPtr<FJsonObject> Ledger;if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw),Ledger)){World->DestroyWorld(false);return false;}
 auto Pending=MakeShared<FJsonObject>();Pending->SetStringField(TEXT("playerId"),TEXT("native-player"));Pending->SetStringField(TEXT("profileAfter"),After);Ledger->SetObjectField(TEXT("pending"),Pending);
 Raw.Empty();FJsonSerializer::Serialize(Ledger.ToSharedRef(),TJsonWriterFactory<>::Create(&Raw));
 TestTrue(TEXT("Persist interruption after durable intent"),UAnomaliaConfigLibrary::SaveWorldState(Scope,TEXT("vehicle-services-v1"),Raw,Error));World->DestroyWorld(false);
 for(int32 Restart=0;Restart<2;++Restart)
 {
  World=UWorld::CreateWorld(EWorldType::Game,false);Services=World->GetSubsystem<UAnomaliaVehicleServiceSubsystem>();
  TestTrue(TEXT("Recover interrupted exchange idempotently"),Services->Configure(Scope,Error));
  User=World->SpawnActor<AAnomaliaSurvivor>();Inventory=User->InventoryComponent.Get();
  TestTrue(TEXT("Restore player after-image"),Inventory->LoadInventoryFromPlayerProfile(Scope,TEXT("native-player"),Error));
  TestFalse(TEXT("Cargo item never reappears in the player after restart"),Inventory->Stacks.ContainsByPredicate([](const auto& S){return S.ItemId==TEXT("wood");}));
  Car=World->SpawnActor<AAnomaliaChaosRoadVehicle>();Systems=Car->SurvivalSystems.Get();Systems->PersistentId=TEXT("authored-e39");Systems->bReady=Services->RegisterVehicle(Systems,Error);Cargo=Car->CargoInventory.Get();
  TestTrue(TEXT("Stable E39 restores its cargo and key"),Systems->bReady&&Systems->HasPhysicalKey(User));
  TestTrue(TEXT("Exactly three cargo items survive repeated restart"),Cargo->Stacks.Num()==1&&Cargo->Stacks[0].ItemId==TEXT("wood")&&Cargo->Stacks[0].Count==3);
  auto Invalid=Systems->Export();Invalid->SetNumberField(TEXT("charge"),-1);TestFalse(TEXT("Malformed vehicle state cannot replace live state"),Systems->Restore(Invalid,Error));
  TestTrue(TEXT("Invalid restore preserves cargo"),Cargo->Stacks.Num()==1&&Cargo->Stacks[0].Count==3);
  TestFalse(TEXT("Uncontrolled remote actor cannot exchange cargo"),Systems->Execute(User,EAnomaliaVehicleServiceAction::Withdraw,1,3,Error));
  TestTrue(TEXT("Player extension remains readable"),UAnomaliaConfigLibrary::LoadPlayerProfile(Scope,TEXT("native-player"),Raw,Error)&&Raw.Contains(TEXT("extension")));
  World->DestroyWorld(false);
 }
 return true;
}
#endif
