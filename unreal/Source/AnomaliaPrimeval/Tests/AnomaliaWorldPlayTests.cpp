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
#include "../World/AnomaliaArchipelagoHeight.h"
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
 struct FProbe { double Deadline=FPlatformTime::Seconds()+120; bool Started=false; bool TerrainPassed=false; bool BridgeStarted=false; bool BridgePaused=false; int32 SpanSamples=0; int32 LastSpan=-1; double LastProgress=0; double FurthestX=0; float StartTime=0; FVector Origin=FVector::ZeroVector; };
 TSharedRef<FProbe> Probe=MakeShared<FProbe>();
 ADD_LATENT_AUTOMATION_COMMAND(FFunctionLatentCommand([this,Probe]()
 {
  if(FPlatformTime::Seconds()>Probe->Deadline){AddError(TEXT("Timed out waiting for playable character / terrain streaming"));return true;}
  UWorld* World=GEditor ? GEditor->PlayWorld : nullptr;
  if(!World || !World->HasBegunPlay())return false;
  APlayerController* PC=UGameplayStatics::GetPlayerController(World,0);
  AAnomaliaSurvivor* Pawn=PC ? Cast<AAnomaliaSurvivor>(PC->GetPawn()) : nullptr;
  if(!Pawn)return false;
  if(Probe->TerrainPassed){
   const double H0=AnomaliaArchipelago::Height(13500,-9000),H1=AnomaliaArchipelago::Height(16000,-9000);
   const double Deck=AnomaliaArchipelago::Height(13005,-9000)+.30;
   const FVector BridgePoint(1300500,900000,Deck*100+110);
   auto DeckHit=[&](const FVector& Point,FHitResult& Hit){
    FCollisionQueryParams Query;Query.AddIgnoredActor(Pawn);
    return World->LineTraceSingleByChannel(Hit,Point+FVector(0,0,300),Point-FVector(0,0,500),ECC_Visibility,Query)
     && Hit.GetActor() && (Hit.GetActor()->ActorHasTag(TEXT("ANOMALIA_DetroitBridge_v1")) || Hit.GetActor()->ActorHasTag(TEXT("ANOMALIA_DetroitRoads_v1")));
   };
   if(!Probe->BridgeStarted){
    FHitResult Hit;if(!DeckHit(BridgePoint,Hit))return false;
    Pawn->SetActorLocation(BridgePoint,false,nullptr,ETeleportType::TeleportPhysics);
    Pawn->GetCharacterMovement()->MaxWalkSpeed=2500; // Accelerated test pawn only: 25m/s.
    Pawn->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    Probe->BridgeStarted=true;Probe->StartTime=World->GetTimeSeconds();Probe->Origin=BridgePoint;
    Probe->LastProgress=FPlatformTime::Seconds();Probe->FurthestX=BridgePoint.X;
    Probe->Deadline=FPlatformTime::Seconds()+420;
   }
   const FVector Position=Pawn->GetActorLocation();
   // Stop before unloaded collision. Resume at the same position; never teleport over seams.
   const double AheadX=FMath::Min(Position.X+3000.,1649500.);
   const double East=AheadX/100.;
   const double AheadDeck=East>=13500 && East<=16000 ? H0+(H1-H0)*(East-13500.)/2500.+.25 : AnomaliaArchipelago::Height(East,-9000)+.30;
   FHitResult AheadHit;
   if(!DeckHit(FVector(AheadX,900000,AheadDeck*100+110),AheadHit)){
    Pawn->GetCharacterMovement()->DisableMovement();Probe->BridgePaused=true;return false;
   }
   if(Probe->BridgePaused){Pawn->GetCharacterMovement()->SetMovementMode(MOVE_Walking);Probe->BridgePaused=false;Probe->LastProgress=FPlatformTime::Seconds();}
   FHitResult Underfoot;
   if(!DeckHit(Position,Underfoot) || FMath::Abs(Position.Y-900000)>200){
    AddError(TEXT("Full bridge traversal lost deck collision or left roadway"));return true;
   }
   const int32 Span=FMath::Clamp(FMath::FloorToInt((Position.X/100.-13500.)/50.),0,49);
   if(Position.X>=1350000 && Position.X<=1600000 && Span!=Probe->LastSpan){
    if(Span!=Probe->LastSpan+1){AddError(TEXT("Bridge traversal skipped a span"));return true;}
    Probe->LastSpan=Span;Probe->SpanSamples++;
   }
   if(Position.X>Probe->FurthestX+10){Probe->FurthestX=Position.X;Probe->LastProgress=FPlatformTime::Seconds();}
   if(FPlatformTime::Seconds()-Probe->LastProgress>20){AddError(TEXT("Character blocked during full bridge crossing"));return true;}
   if(Position.X<1649500){Pawn->AddMovementInput(FVector(1,0,0),1.f);return false;}
   TestEqual(TEXT("All 50 bridge spans crossed in sequence"),Probe->SpanSamples,50);
   TestTrue(TEXT("Continuous roads and bridge traversal at least 3490 metres"),Position.X-Probe->Origin.X>=349000);
   TestTrue(TEXT("Character grounded after full crossing"),Pawn->GetCharacterMovement()->IsMovingOnGround());
   AddInfo(FString::Printf(TEXT("Continuous accelerated PIE bridge crossing %.1f metres, %d spans; test speed 25m/s; no vehicle or multiplayer validation"),(Position.X-Probe->Origin.X)/100.,Probe->SpanSamples));
   return true;
  }
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
  // Teleport only the PIE character. Freeze movement until the distant bridge collision streams in.
  Probe->TerrainPassed=true;Probe->Deadline=FPlatformTime::Seconds()+120;
   const double Deck=AnomaliaArchipelago::Height(13005,-9000)+.30;
  Pawn->GetCharacterMovement()->DisableMovement();
  Pawn->SetActorLocation(FVector(1300500,900000,Deck*100+110),false,nullptr,ETeleportType::TeleportPhysics);
  return false;
 }));
 ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
 return true;
}
#endif
