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
#include "../AnomaliaEconomySubsystem.h"
#include "../AnomaliaBankTerminal.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Button.h"
#include "../AnomaliaLootPickup.h"
#include "../AnomaliaInventoryComponent.h"
#include "../AnomaliaInventoryWidget.h"
#include "../AnomaliaStatusWidget.h"
#include "Components/SafeZone.h"
#include "../AnomaliaVitalsComponent.h"
#include "../AnomaliaHomesteadStation.h"
#include "../AnomaliaSessionWidget.h"

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
    struct FProbe { int32 Phase = 0; double Deadline = FPlatformTime::Seconds()+120;
        FName NoteId; int64 Value = 0; double NextAction = 0;
        TWeakObjectPtr<AAnomaliaHomesteadStation> Bed; };
    auto Probe = MakeShared<FProbe>();
    ADD_LATENT_AUTOMATION_COMMAND(FFunctionLatentCommand([this, Probe, Scope]()
    {
        UWorld* World = GEditor ? GEditor->PlayWorld : nullptr;
        if (!World || !World->HasBegunPlay()) return false;
        auto* Mode = World->GetAuthGameMode<AAnomaliaGameMode>();
        auto* PC = UGameplayStatics::GetPlayerController(World, 0);
        auto* Survivor = PC ? Cast<AAnomaliaSurvivor>(PC->GetPawn()) : nullptr;
        if (FPlatformTime::Seconds() > Probe->Deadline)
        {
            FString Detail;
            if (Survivor)
            {
                Detail = FString::Printf(TEXT("position=%s bankAvailable=%d account=%s inventoryUI=%d"),
                    *Survivor->GetActorLocation().ToString(), Survivor->InventoryComponent->bBankingAvailable,
                    *Survivor->InventoryComponent->BankAccountId,
                    Survivor->InventoryWidget && Survivor->InventoryWidget->IsInViewport());
                if (Survivor->InventoryWidget && Survivor->InventoryWidget->WidgetTree)
                    Survivor->InventoryWidget->WidgetTree->ForEachWidget([&](UWidget* Widget)
                    { if (Widget && Widget->GetName().StartsWith(TEXT("Bank"))) Detail += TEXT(" | ")+Widget->GetName(); });
                for (TActorIterator<AAnomaliaBankTerminal> It(World); It; ++It)
                    Detail += TEXT(" terminal=")+It->GetActorLocation().ToString();
            }
            AddError(FString::Printf(TEXT("Loot PIE timeout phase %d: %s"),Probe->Phase,*Detail)); return true;
        }
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
            auto* Items=Survivor->InventoryComponent.Get();FString PolicyError;
            const auto PreviousSettings=Mode->ActiveServerSettings;
            Mode->ActiveServerSettings.bAllowRPSubstances=false;
            Mode->ActiveServerSettings.bAllowTobacco=false;
            Mode->ActiveServerSettings.bAllowAlcohol=false;
            TestTrue(TEXT("Prerequisite tool in isolated policy test"),Items->TryAddItem(TEXT("lighter"),1));
            for(const FName Id:{FName(TEXT("cigarette")),FName(TEXT("vodka")),FName(TEXT("rp_substance_cocaine"))})
            {
                TestTrue(TEXT("Restricted item can be carried"),Items->TryAddItem(Id,1));
                const auto* Stack=Items->Stacks.FindByPredicate([&](const auto& Row){return Row.ItemId==Id;});
                if(Stack) TestFalse(TEXT("Authoritative party policy rejects consumption"),Items->TryUseStack(Stack->StackId,1,Scope,TEXT("local-owner"),PolicyError));
                TestTrue(TEXT("Policy rejection preserves the source item"),Items->TryRemoveItem(Id,1));
            }
            TestTrue(TEXT("Remove isolated policy tool"),Items->TryRemoveItem(TEXT("lighter"),1));
            Mode->ActiveServerSettings=PreviousSettings;
            auto* PolicyMenu=UAnomaliaSessionWidget::Open(PC,false);
            auto* Toggle=PolicyMenu && PolicyMenu->WidgetTree?Cast<UButton>(PolicyMenu->WidgetTree->FindWidget(TEXT("SessionTobacco"))):nullptr;
            if(!TestNotNull(TEXT("Actual solo tobacco policy button exists"),Toggle)) return true;
            Toggle->OnClicked.Broadcast();
            TestEqual(TEXT("Solo policy UI changes authoritative setting"),Mode->ActiveServerSettings.bAllowTobacco,!PreviousSettings.bAllowTobacco);
            FAnomaliaServerSettings Reloaded;FString PolicyLoadError;
            TestTrue(TEXT("Solo policy persisted"),UAnomaliaConfigLibrary::LoadServerSettings(Scope,Reloaded,PolicyLoadError));
            TestEqual(TEXT("Saved policy agrees with UI"),Reloaded.bAllowTobacco,Mode->ActiveServerSettings.bAllowTobacco);
            Toggle->OnClicked.Broadcast();
            if(auto* Play=Cast<UButton>(PolicyMenu->WidgetTree->FindWidget(TEXT("SessionPlay")))) Play->OnClicked.Broadcast();
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
        if (Probe->Phase == 3)
        {
            Input(EKeys::I, IE_Released);
            if (Survivor->InventoryWidget && Survivor->InventoryWidget->IsInViewport()) return false;
            TestEqual(TEXT("Opening and closing UI preserves the item"), Units, 1);
            Survivor->SetActorLocation(FVector(200,-140,100),false,nullptr,ETeleportType::TeleportPhysics);
            auto* HUD=Survivor->StatusWidget.Get();
            if (!HUD || !HUD->WidgetTree) return false;
            HUD->SetTouchControlsEnabled(true);
            TestNotNull(TEXT("HUD respects screen safe areas"),Cast<USafeZone>(HUD->WidgetTree->RootWidget));
            auto* Touch=Cast<UButton>(HUD->WidgetTree->FindWidget(FName(TEXT("TouchInteract"))));
            if (!TestNotNull(TEXT("Real touch interaction button exists"),Touch)) return true;
            Touch->OnClicked.Broadcast(); Probe->Phase=4; return false;
        }
        if (Probe->Phase == 4)
        {
            Input(EKeys::E,IE_Released);
            if (Units < 2) return false;
            for (const auto& Stack : Survivor->InventoryComponent->Stacks)
                if (Stack.ItemId.ToString().StartsWith(TEXT("eur_note_"))) Probe->NoteId=Stack.ItemId;
            const auto* Economy=World->GetSubsystem<UAnomaliaEconomySubsystem>();
            Probe->Value=Economy ? Economy->GetDenomination(Probe->NoteId) : 0;
            if (!TestTrue(TEXT("Actual world RP note is a fixed denomination"),Probe->Value>0)) return true;
            Survivor->SetActorLocation(FVector(350,0,100),false,nullptr,ETeleportType::TeleportPhysics);
            Input(EKeys::Gamepad_Special_Right,IE_Pressed); Probe->Phase=5; return false;
        }
        auto FindButton=[Survivor](const FString& Prefix)->UButton*
        {
            UButton* Found=nullptr;
            if (Survivor->InventoryWidget && Survivor->InventoryWidget->WidgetTree)
                Survivor->InventoryWidget->WidgetTree->ForEachWidget([&](UWidget* Widget)
                { if (Widget && (Widget->GetName()==Prefix || Widget->GetName().StartsWith(Prefix+TEXT("_")))) Found=Cast<UButton>(Widget); });
            return Found;
        };
        if (Probe->Phase == 5)
        {
            Input(EKeys::Gamepad_Special_Right,IE_Released);
            if (!Survivor->InventoryComponent->bBankingAvailable) return false;
            const auto* Stack=Survivor->InventoryComponent->Stacks.FindByPredicate([&](const auto& Row) { return Row.ItemId==Probe->NoteId; });
            UButton* Deposit=Stack ? FindButton(FString::Printf(TEXT("BankDeposit_%d_action"),Stack->StackId)) : nullptr;
            if (!Deposit) return false;
            TestNotNull(TEXT("Gamepad inventory opens a safe-zone panel"),Cast<USafeZone>(Survivor->InventoryWidget->WidgetTree->RootWidget));
            Deposit->OnClicked.Broadcast(); Probe->Phase=6; Probe->NextAction=FPlatformTime::Seconds()+.25; return false;
        }
        if (Probe->Phase == 6)
        {
            if (Survivor->InventoryComponent->BankBalanceCents!=Probe->Value || FPlatformTime::Seconds()<Probe->NextAction) return false;
            TestEqual(TEXT("Actual bank UI deposit removes the physical note"),Units,1);
            UButton* Withdraw=FindButton(TEXT("BankWithdraw_")+Probe->NoteId.ToString()+TEXT("_action"));
            if (!Withdraw) return false;
            Withdraw->OnClicked.Broadcast(); Probe->Phase=7; return false;
        }
        if (Probe->Phase==7)
        {
            if (Survivor->InventoryComponent->BankBalanceCents!=0 || Units!=2) return false;
            TestEqual(TEXT("Actual bank UI withdrawal restores exactly one note"),Units,2);
            // Same real UMG panel, isolated storage fixture; never mutate the player's saved loot.
            AActor* PagingOwner=World->SpawnActor<AActor>();
            auto* Paging=NewObject<UAnomaliaInventoryComponent>(PagingOwner);
            PagingOwner->AddInstanceComponent(Paging);Paging->RegisterComponent();Paging->Compartments.Reset();
            TestTrue(TEXT("Prepare real paged cargo"),Paging->ConfigureCompartment(TEXT("cargo"),20,25));
            if(TestTrue(TEXT("Prepare rectangular rotation item"),Paging->TryAddItem(TEXT("wood"),1)))
            {
                const int32 WoodId=Paging->Stacks[0].StackId;
                Survivor->InventoryWidget->InitializeForInventory(Paging);
                auto* Rotate=FindButton(FString::Printf(TEXT("RotateStack_%d_action"),WoodId));
                if(TestNotNull(TEXT("Real UMG rotation button exists"),Rotate))Rotate->OnClicked.Broadcast();
                TestTrue(TEXT("Actual rotation button changes authoritative rectangle"),Paging->Stacks[0].bRotated);
                TestEqual(TEXT("Rotation preserves occupied area"),Paging->GetUsedCells(TEXT("cargo")),3);
                TestTrue(TEXT("Seed stacks for real pagination"),Paging->TryAddItem(TEXT("ammo"),40));
                while(Paging->Stacks.Num()<41)
                {
                    const auto* Source=Paging->Stacks.FindByPredicate([](const auto& S){return S.ItemId==TEXT("ammo") && S.Count>1;});
                    int32 NewId=0;
                    if(!Source || !Paging->TrySplitStack(Source->StackId,1,NewId)){AddError(TEXT("Cannot prepare real pagination fixture"));break;}
                }
                TestEqual(TEXT("41 real stacks form two pages"),Survivor->InventoryWidget->GetPageCount(),2);
                auto CountRows=[Survivor]()
                {
                    int32 Rows=0;
                    Survivor->InventoryWidget->WidgetTree->ForEachWidget([&](UWidget* W){if(W && W->GetName().StartsWith(TEXT("InventoryStack_")))++Rows;});
                    return Rows;
                };
                TestEqual(TEXT("UMG constructs at most 32 stored rows on page one"),CountRows(),32);
                if(auto* Next=FindButton(TEXT("InventoryNextPage")))Next->OnClicked.Broadcast();
                TestEqual(TEXT("Actual Next button selects second page"),Survivor->InventoryWidget->GetCurrentPage(),1);
                TestEqual(TEXT("Last page displays remaining real stacks"),CountRows(),9);
                if(auto* Previous=FindButton(TEXT("InventoryPreviousPage")))Previous->OnClicked.Broadcast();
                TestEqual(TEXT("Actual Previous button returns without moving items"),Survivor->InventoryWidget->GetCurrentPage(),0);
                int32 PagingUnits=0;for(const auto& S:Paging->Stacks)PagingUnits+=S.Count;
                TestEqual(TEXT("Page navigation never mutates item quantities"),PagingUnits,41);
            }
            Survivor->InventoryWidget->InitializeForInventory(Survivor->InventoryComponent);
            PagingOwner->Destroy();
            auto* Close=FindButton(TEXT("InventoryClose"));
            if (!TestNotNull(TEXT("Touch/controller inventory close button exists"),Close)) return true;
            Close->OnClicked.Broadcast();
            TestNull(TEXT("Close button restores gameplay and clears the panel"),Survivor->InventoryWidget.Get());
            TestFalse(TEXT("Closing inventory restores movement"),PC->IsMoveInputIgnored());
            TestFalse(TEXT("Closing inventory restores look"),PC->IsLookInputIgnored());
            Survivor->RestoreFatigue(85.f);
            Survivor->VitalsComponent->RestoreVitals(42.f,34.f);
            Probe->NextAction=FPlatformTime::Seconds()+.4; Probe->Phase=8; return false;
        }
        if (Probe->Phase==8)
        {
            Input(EKeys::I,IE_Released);
            if (FPlatformTime::Seconds()<Probe->NextAction) return false;
            auto* HUD=Survivor->StatusWidget.Get();
            if (!HUD || !HUD->IsInViewport()) { AddError(TEXT("Native status HUD is missing")); return true; }
            // Explicit refresh also runs under NullRHI, where Slate may skip visual widget ticks.
            HUD->RefreshFromSurvivor();
            TestTrue(TEXT("Native fatigue HUD reads the actual replicated survivor value"),HUD->GetVitalText(TEXT("fatigue")).ToString().Contains(TEXT("85")));
            TestTrue(TEXT("Native temperature HUD includes Celsius"),HUD->GetVitalText(TEXT("temperature")).ToString().Contains(TEXT("°C")));
            TestTrue(TEXT("Actual low body temperature activates hypothermia"),HUD->GetConditionText().ToString().Contains(TEXT("Hypothermie")));
            for (const FName Id : {FName(TEXT("health")),FName(TEXT("thirst")),FName(TEXT("hunger")),FName(TEXT("stamina")),FName(TEXT("fatigue")),FName(TEXT("temperature")),FName(TEXT("blood"))})
                TestFalse(TEXT("Permanent native vital label exists"),HUD->GetVitalText(Id).IsEmpty());
            Survivor->RestoreFatigue(0.f); Survivor->VitalsComponent->RestoreVitals(100.f,37.f);
            HUD->RefreshFromSurvivor();
            TestTrue(TEXT("Recovered native warnings disappear while permanent vitals stay"),HUD->GetConditionText().IsEmpty());
            auto* Bed=World->SpawnActor<AAnomaliaHomesteadStation>(Survivor->GetActorLocation()+FVector(120,0,-40),FRotator::ZeroRotator);
            if (!Bed) { AddError(TEXT("Cannot create isolated sleep test bed")); return true; }
            Probe->Bed=Bed;
            Survivor->RestoreFatigue(96.f);
            Input(EKeys::R,IE_Pressed); Probe->Phase=9; return false;
        }
        Input(EKeys::R,IE_Released);
        if (Probe->Phase==9)
        {
            if (!TestTrue(TEXT("Actual rest input starts a thirty-second server-owned sleep"),Survivor->bSleeping && Survivor->SleepRemainingSeconds>29.f)) return true;
            Probe->Phase=10; return false;
        }
        if (Survivor->bSleeping) return false;
        TestTrue(TEXT("Timed sleep wakes the real player fully rested"),Survivor->Fatigue<.05f && Survivor->VitalsComponent->Stamina>99.f);
        if (Probe->Bed.IsValid()) Probe->Bed->Destroy();
        return true;
    }));
    ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
    return true;
}
#endif
