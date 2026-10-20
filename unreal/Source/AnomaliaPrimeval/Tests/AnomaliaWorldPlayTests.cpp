#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"
#include "Editor.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "LandscapeProxy.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "../AnomaliaSurvivor.h"
#include "../AnomaliaInventoryComponent.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaWorldPlayTest,"Anomalia.World.ArchipelagoPIE",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaWorldPlayTest::RunTest(const FString& Parameters)
{
 const FString MapFile=FPaths::ProjectContentDir()/TEXT("Maps/ANOMALIA_Archipelago_v2.umap");
 if(!IFileManager::Get().FileExists(*MapFile)){AddError(TEXT("Generated real archipelago map is missing"));return false;}
 if(!AutomationOpenMap(TEXT("/Game/Maps/ANOMALIA_Archipelago_v2"))){AddError(TEXT("Could not open generated map"));return false;}
 ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
 struct FProbe { double Deadline=FPlatformTime::Seconds()+120; bool Started=false; float StartTime=0; FVector Origin=FVector::ZeroVector; };
 TSharedRef<FProbe> Probe=MakeShared<FProbe>();
 ADD_LATENT_AUTOMATION_COMMAND(FFunctionLatentCommand([this,Probe]()
 {
  if(FPlatformTime::Seconds()>Probe->Deadline){AddError(TEXT("Timed out waiting for playable character / terrain streaming"));return true;}
  UWorld* World=GEditor ? GEditor->PlayWorld : nullptr;
  if(!World || !World->HasBegunPlay())return false;
  APlayerController* PC=UGameplayStatics::GetPlayerController(World,0);
  AAnomaliaSurvivor* Pawn=PC ? Cast<AAnomaliaSurvivor>(PC->GetPawn()) : nullptr;
  if(!Pawn)return false;
  if(!Probe->Started){
   // Require real ground collision before starting movement, not a pawn falling through empty space.
   if(!Pawn->GetCharacterMovement()->IsMovingOnGround())return false;
   TestTrue(TEXT("PIE uses native authoritative survivor"),Pawn->HasAuthority());
   FHitResult Hit;FCollisionQueryParams Query;Query.AddIgnoredActor(Pawn);
   const bool GroundHit=World->LineTraceSingleByChannel(Hit,Pawn->GetActorLocation(),Pawn->GetActorLocation()-FVector(0,0,1000),ECC_Visibility,Query);
   TestTrue(TEXT("Character stands above actual Landscape collision"),GroundHit && Hit.GetActor() && Hit.GetActor()->IsA<ALandscapeProxy>());
   UAnomaliaInventoryComponent* Inventory=Pawn->FindComponentByClass<UAnomaliaInventoryComponent>();
   if(!TestNotNull(TEXT("Native inventory exists in PIE"),Inventory))return true;
   // Test a component owned by our own transient actor; never edit a loaded player profile.
   AActor* InventoryOwner=World->SpawnActor<AActor>();
   if(!TestNotNull(TEXT("Isolated live PIE inventory owner"),InventoryOwner))return true;
   UAnomaliaInventoryComponent* ProbeInventory=NewObject<UAnomaliaInventoryComponent>(InventoryOwner);
   InventoryOwner->AddInstanceComponent(ProbeInventory);ProbeInventory->RegisterComponent();
   const bool Added=ProbeInventory->TryAddItem(TEXT("bandage"),1);
   TestTrue(TEXT("Add a bandage to isolated inventory in real PIE"),Added);
   if(Added)TestTrue(TEXT("Remove the same bandage in real PIE"),ProbeInventory->TryRemoveItem(TEXT("bandage"),1));
   InventoryOwner->Destroy(); // Only our transient test actor.

   Probe->Started=true;Probe->StartTime=World->GetTimeSeconds();Probe->Origin=Pawn->GetActorLocation();
  }
  if(World->GetTimeSeconds()-Probe->StartTime<1.5f){Pawn->AddMovementInput(FVector(1,0,0),1.f);return false;}
  const FVector Travel=Pawn->GetActorLocation()-Probe->Origin;
  TestTrue(TEXT("Character actually walks at least 50cm on imported terrain"),Travel.Size2D()>50);
  TestTrue(TEXT("Character remains on ground after walking"),Pawn->GetCharacterMovement()->IsMovingOnGround());
  AddInfo(FString::Printf(TEXT("Actual PIE walking distance %.1f cm; no rendered visual/performance validation"),Travel.Size2D()));
  return true;
 }));
 ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
 return true;
}
#endif
