#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"
#include "Editor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerInput.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "../AnomaliaGameMode.h"
#include "../AnomaliaSurvivor.h"
#include "../AnomaliaLootSubsystem.h"
#include "../AnomaliaLootPickup.h"
#include "../AnomaliaInventoryComponent.h"
#include "../AnomaliaInventoryWidget.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAnomaliaLootPIETest, "Anomalia.Loot.PIE",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAnomaliaLootPIETest::RunTest(const FString& Parameters)
{
    FString Scope;
    if (!FParse::Value(FCommandLine::Get(), TEXT("AnomaliaAutomationServerId="), Scope) || !Scope.StartsWith(TEXT("loot-pie-")))
    { AddError(TEXT("Explicit isolated loot-pie test scope is required; no player saves were touched")); return false; }
    if (!AutomationOpenMap(TEXT("/Game/Maps/ANOMALIA_LootReview_v1")))
    { AddError(TEXT("Real loot review map is missing")); return false; }
    ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
    struct FProbe { int32 Phase = 0; double Deadline = FPlatformTime::Seconds()+120; };
    auto Probe = MakeShared<FProbe>();
    ADD_LATENT_AUTOMATION_COMMAND(FFunctionLatentCommand([this, Probe, Scope]()
    {
        if (FPlatformTime::Seconds() > Probe->Deadline)
        { AddError(FString::Printf(TEXT("Loot PIE timeout in phase %d"), Probe->Phase)); return true; }
        UWorld* World = GEditor ? GEditor->PlayWorld : nullptr;
        if (!World || !World->HasBegunPlay()) return false;
        auto* Mode = World->GetAuthGameMode<AAnomaliaGameMode>();
        auto* PC = UGameplayStatics::GetPlayerController(World, 0);
        auto* Survivor = PC ? Cast<AAnomaliaSurvivor>(PC->GetPawn()) : nullptr;
        if (!Mode || !PC || !Survivor) return false;
        if (Mode->ServerId != Scope)
        { AddError(TEXT("Refusing PIE interaction in a non-isolated save scope")); return true; }
        auto Input = [PC](FKey Key, EInputEvent Event)
        { PC->InputKey(FInputKeyParams(Key, Event, Event == IE_Pressed ? 1.0 : 0.0, false, FInputDeviceId::CreateFromInternalId(0))); };
        int32 Units = 0;
        for (const auto& Stack : Survivor->InventoryComponent->Stacks) Units += Stack.Count;
        if (Probe->Phase == 0)
        {
            auto* Loot = World->GetSubsystem<UAnomaliaLootSubsystem>();
            if (!Loot || !Loot->IsReady()) return false;
            AAnomaliaLootPickup* Food = nullptr;
            for (TActorIterator<AAnomaliaLootPickup> It(World); It; ++It)
                if (It->SpawnId == TEXT("review-house-food")) { Food = *It; break; }
            if (!Food) return false;
            TestEqual(TEXT("Fresh isolated player inventory"), Units, 0);
            Survivor->SetActorLocation(FVector(70, 0, 100), false, nullptr, ETeleportType::TeleportPhysics);
            Input(EKeys::E, IE_Pressed);
            Probe->Phase = 1;
            return false;
        }
        if (Probe->Phase == 1)
        {
            Input(EKeys::E, IE_Released);
            if (Units == 0) return false;
            TestEqual(TEXT("Actual Interact key adds exactly one world item"), Units, 1);
            FString Error;
            AActor* Owner = World->SpawnActor<AActor>();
            auto* Check = NewObject<UAnomaliaInventoryComponent>(Owner);
            Owner->AddInstanceComponent(Check); Check->RegisterComponent();
            TestTrue(TEXT("PIE interaction saved through existing native profile loader"),
                Check->LoadInventoryFromPlayerProfile(Scope, TEXT("local-owner"), Error));
            int32 SavedUnits = 0;
            for (const auto& Stack : Check->Stacks) SavedUnits += Stack.Count;
            TestEqual(TEXT("Durable inventory matches the live result"), SavedUnits, 1);
            Owner->Destroy();
            Input(EKeys::I, IE_Pressed);
            Probe->Phase = 2;
            return false;
        }
        if (Probe->Phase == 2)
        {
            Input(EKeys::I, IE_Released);
            if (!Survivor->InventoryWidget || !Survivor->InventoryWidget->IsInViewport()) return false;
            TestTrue(TEXT("Inventory key opens the real native UMG screen after pickup"), true);
            Input(EKeys::I, IE_Pressed);
            Probe->Phase = 3;
            return false;
        }
        Input(EKeys::I, IE_Released);
        if (Survivor->InventoryWidget && Survivor->InventoryWidget->IsInViewport()) return false;
        TestEqual(TEXT("Opening and closing UI does not consume or duplicate the item"), Units, 1);
        return true;
    }));
    ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
    return true;
}
#endif
