#include "AnomaliaInventoryWidget.h"
#include "AnomaliaInventoryComponent.h"
#include "AnomaliaSurvivor.h"
#include "Vehicles/AnomaliaChaosRoadVehicle.h"
#include "Vehicles/AnomaliaVehicleSurvival.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SafeZone.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/ScrollBox.h"
#include "Components/ScrollBoxSlot.h"
#include "Components/TextBlock.h"
#include "Components/EditableTextBox.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"

void UAnomaliaInventoryActionRelay::Execute()
{
    if (TargetWidget) TargetWidget->PerformAction(Action, StackId, Count, OtherStackId);
}

void UAnomaliaInventoryWidget::InitializeForInventory(UAnomaliaInventoryComponent* InInventory)
{
    if (Inventory) Inventory->OnInventoryUpdated.RemoveDynamic(this, &UAnomaliaInventoryWidget::RefreshInventory);
    Inventory = InInventory;
    CurrentPage=0;
    if (Inventory) Inventory->OnInventoryUpdated.AddDynamic(this, &UAnomaliaInventoryWidget::RefreshInventory);
    RefreshInventory();
}

TSharedRef<SWidget> UAnomaliaInventoryWidget::RebuildWidget()
{
    if(!WidgetTree) WidgetTree=NewObject<UWidgetTree>(this,TEXT("WidgetTree"));
    BuildLayout();
    return Super::RebuildWidget();
}

void UAnomaliaInventoryWidget::NativeConstruct()
{
    Super::NativeConstruct();
    SetIsFocusable(true);
    BuildLayout();
    RefreshInventory();
}

void UAnomaliaInventoryWidget::NativeDestruct()
{
    if (Inventory) Inventory->OnInventoryUpdated.RemoveDynamic(this, &UAnomaliaInventoryWidget::RefreshInventory);
    if(NearbyVehicle)
    {
        NearbyVehicle->CargoInventory->OnInventoryUpdated.RemoveDynamic(this,&UAnomaliaInventoryWidget::RefreshInventory);
        NearbyVehicle->SurvivalSystems->OnServicesUpdated.RemoveDynamic(this,&UAnomaliaInventoryWidget::RefreshInventory);
    }
    Super::NativeDestruct();
}

void UAnomaliaInventoryWidget::BuildLayout()
{
    if (!WidgetTree || RootCanvas) return;
    RootCanvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("InventoryCanvas"));
    auto* Safe = WidgetTree->ConstructWidget<USafeZone>(USafeZone::StaticClass(), TEXT("InventorySafeZone"));
    Safe->SetContent(RootCanvas);
    WidgetTree->RootWidget = Safe;
    UBorder* Frame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("InventoryFrame"));
    Frame->SetBrushColor(FLinearColor(0.012f, 0.035f, 0.055f, 0.96f));
    UCanvasPanelSlot* FrameSlot = RootCanvas->AddChildToCanvas(Frame);
    FrameSlot->SetAnchors(FAnchors(.08f, .06f, .92f, .94f));
    FrameSlot->SetOffsets(FMargin(0.f));
    FrameSlot->SetZOrder(1);

    UVerticalBox* Content = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("InventoryContent"));
    Frame->SetContent(Content);
    CloseButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("InventoryClose"));
    auto* CloseLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    CloseLabel->SetText(FText::FromString(TEXT("Fermer / Retour")));
    CloseButton->SetContent(CloseLabel);
    CloseButton->OnClicked.AddDynamic(this, &UAnomaliaInventoryWidget::CloseInventory);
    Content->AddChildToVerticalBox(CloseButton)->SetPadding(FMargin(14.f, 8.f));
    UTextBlock* Heading = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventoryHeading"));
    Heading->SetText(FText::FromString(TEXT("ANOMALIA  /  INVENTAIRE")));
    Heading->SetColorAndOpacity(FSlateColor(FLinearColor(.32f, .86f, .94f)));
    auto HeadingFont=Heading->GetFont(); HeadingFont.Size=26; Heading->SetFont(HeadingFont);
    Content->AddChildToVerticalBox(Heading)->SetPadding(FMargin(14.f, 10.f));
    UTextBlock* Hint = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventoryHint"));
    Hint->SetText(FText::FromString(TEXT("Manger · boire · soins simples · déplacer vers les mains · séparer et fusionner les piles")));
    Hint->SetColorAndOpacity(FSlateColor(FLinearColor(.72f, .82f, .86f)));
    Content->AddChildToVerticalBox(Hint)->SetPadding(FMargin(14.f, 0.f, 14.f, 10.f));
    UseStatus=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(),TEXT("ItemUseStatus"));
    UseStatus->SetAutoWrapText(true);
    Content->AddChildToVerticalBox(UseStatus)->SetPadding(FMargin(14.f,4.f));

    BankStatus = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("BankStatus"));
    BankStatus->SetAutoWrapText(true);
    Content->AddChildToVerticalBox(BankStatus)->SetPadding(FMargin(14.f, 4.f));
    UHorizontalBox* Transfer = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
    Content->AddChildToVerticalBox(Transfer)->SetPadding(FMargin(14.f, 4.f));
    BankRecipient = WidgetTree->ConstructWidget<UEditableTextBox>(UEditableTextBox::StaticClass(), TEXT("BankRecipient"));
    BankRecipient->SetHintText(FText::FromString(TEXT("Compte destinataire")));
    Transfer->AddChildToHorizontalBox(BankRecipient)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    BankAmount = WidgetTree->ConstructWidget<UEditableTextBox>(UEditableTextBox::StaticClass(), TEXT("BankAmount"));
    BankAmount->SetHintText(FText::FromString(TEXT("Montant EUR : 10,50")));
    Transfer->AddChildToHorizontalBox(BankAmount)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    TransferButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("BankTransfer"));
    UTextBlock* TransferLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    TransferLabel->SetText(FText::FromString(TEXT("Transférer"))); TransferButton->SetContent(TransferLabel);
    TransferButton->OnClicked.AddDynamic(this, &UAnomaliaInventoryWidget::TransferMoney);
    Transfer->AddChildToHorizontalBox(TransferButton);

    auto* Pages=WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(),TEXT("InventoryPages"));
    Content->AddChildToVerticalBox(Pages)->SetPadding(FMargin(14.f,5.f));
    PreviousPageButton=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),TEXT("InventoryPreviousPage"));
    auto* PreviousLabel=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    PreviousLabel->SetText(FText::FromString(TEXT("Page précédente")));PreviousPageButton->SetContent(PreviousLabel);
    PreviousPageButton->OnClicked.AddDynamic(this,&UAnomaliaInventoryWidget::PreviousPage);
    Pages->AddChildToHorizontalBox(PreviousPageButton)->SetPadding(FMargin(5.f));
    PageStatus=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(),TEXT("InventoryPageStatus"));
    Pages->AddChildToHorizontalBox(PageStatus)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    NextPageButton=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),TEXT("InventoryNextPage"));
    auto* NextLabel=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    NextLabel->SetText(FText::FromString(TEXT("Page suivante")));NextPageButton->SetContent(NextLabel);
    NextPageButton->OnClicked.AddDynamic(this,&UAnomaliaInventoryWidget::NextPage);
    Pages->AddChildToHorizontalBox(NextPageButton)->SetPadding(FMargin(5.f));

    UScrollBox* Scroll = WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(), TEXT("InventoryScroll"));
    auto* Columns=WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(),TEXT("InventoryColumns"));
    Content->AddChildToVerticalBox(Columns)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    auto* NearbyScroll=WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(),TEXT("ProximityScroll"));
    Columns->AddChildToHorizontalBox(NearbyScroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    ProximityList=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("VehicleProximity"));NearbyScroll->AddChild(ProximityList);
    Columns->AddChildToHorizontalBox(Scroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    ItemList = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("InventoryItems"));
    Scroll->AddChild(ItemList);
}

void UAnomaliaInventoryWidget::RefreshInventory()
{
    if (!ItemList || !WidgetTree) return;
    const auto* Previous=FocusedAction();const bool HadFocus=Previous!=nullptr;
    const auto PreviousAction=Previous?Previous->Action:EAnomaliaInventoryAction::Stow;
    const int32 PreviousStack=Previous?Previous->StackId:0,PreviousOther=Previous?Previous->OtherStackId:0;
    ActionRelays.Reset();
    ItemList->ClearChildren();
    if (!Inventory)
    {
        UTextBlock* Missing = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        Missing->SetText(FText::FromString(TEXT("Inventaire indisponible.")));
        ItemList->AddChildToVerticalBox(Missing);
        return;
    }

    if(UseStatus) UseStatus->SetText(FText::FromString(Inventory->UseMessage));
    if (BankStatus)
        BankStatus->SetText(FText::FromString(FString::Printf(TEXT("BANQUE RP · Compte %s · %lld,%02lld EUR\n%s %s"),
            *Inventory->BankAccountId, static_cast<long long>(Inventory->BankBalanceCents/100),
            static_cast<long long>(Inventory->BankBalanceCents%100),
            Inventory->bBankingAvailable ? TEXT("Terminal à portée.") : TEXT("Approchez-vous d’un terminal bancaire."), *Inventory->BankMessage)));
    if (TransferButton) TransferButton->SetIsEnabled(Inventory->bBankingAvailable);
    if (Inventory->bBankingAvailable)
    {
        UHorizontalBox* Withdrawals = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
        ItemList->AddChildToVerticalBox(Withdrawals)->SetPadding(FMargin(12.f, 3.f));
        for (int32 Euros : {5,10,20,50,100,200,500})
        {
            UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), MakeUniqueObjectName(WidgetTree, UButton::StaticClass(), FName(*FString::Printf(TEXT("BankWithdraw_eur_note_%d_action"), Euros))));
            UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
            Text->SetText(FText::FromString(FString::Printf(TEXT("Retirer %d EUR"), Euros))); Button->SetContent(Text);
            Button->SetIsEnabled(Inventory->BankBalanceCents >= Euros*100);
            Withdrawals->AddChildToHorizontalBox(Button)->SetPadding(FMargin(3.f));
            BindAction(Button, EAnomaliaInventoryAction::WithdrawNote, 0, Euros);
        }
    }
    RefreshVehicleProximity();
    auto* PersonalTarget=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
    auto* PersonalLabel=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());PersonalLabel->SetText(FText::FromString(TEXT("INVENTAIRE PERSONNEL — déposer ici")));PersonalTarget->SetContent(PersonalLabel);ItemList->AddChildToVerticalBox(PersonalTarget);
    BindAction(PersonalTarget,EAnomaliaInventoryAction::Stow,0);
    const float Weight = Inventory->GetCurrentWeightKg();
    int32 StoredStacks=0;
    for(const auto& Stack:Inventory->Stacks)if(Stack.ContainerId!=TEXT("hands"))++StoredStacks;
    PageCount=FMath::Max(1,FMath::DivideAndRoundUp(StoredStacks,ItemsPerPage));
    CurrentPage=FMath::Clamp(CurrentPage,0,PageCount-1);
    if(PageStatus)PageStatus->SetText(FText::FromString(FString::Printf(TEXT("Page %d / %d · %d piles · LB/RB"),CurrentPage+1,PageCount,StoredStacks)));
    if(PreviousPageButton)PreviousPageButton->SetIsEnabled(CurrentPage>0);
    if(NextPageButton)NextPageButton->SetIsEnabled(CurrentPage+1<PageCount);
    UTextBlock* WeightText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    WeightText->SetText(FText::FromString(FString::Printf(TEXT("POIDS  %.1f / %.1f KG"), Weight, Inventory->WeightCapacityKg)));
    WeightText->SetColorAndOpacity(FSlateColor(Weight > Inventory->WeightCapacityKg ? FLinearColor(1.f, .3f, .24f) : FLinearColor(.2f, .9f, .75f)));
    ItemList->AddChildToVerticalBox(WeightText)->SetPadding(FMargin(14.f, 10.f));

    int32 StoredIndex=0;
    for (const FAnomaliaInventoryCompartment& Box : Inventory->Compartments)
    {
        UTextBlock* BoxTitle = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        BoxTitle->SetText(FText::FromString(FString::Printf(TEXT("%s  ·  %d × %d · %d / %d cases"), *Box.Id.ToString(), Box.Width, Box.Height,
            Inventory->GetUsedCells(Box.Id),Box.Width*Box.Height)));
        BoxTitle->SetColorAndOpacity(FSlateColor(FLinearColor(.32f, .86f, .94f)));
        if(Box.bRecoveryOnly) BoxTitle->SetText(FText::FromString(TEXT("RÉCUPÉRATION — retrait uniquement · objets conservés après migration")));
        ItemList->AddChildToVerticalBox(BoxTitle)->SetPadding(FMargin(14.f, 14.f, 8.f, 5.f));
        for (const FAnomaliaInventoryStack& Stack : Inventory->Stacks)
        {
            if (Stack.ContainerId != Box.Id) continue;
            const int32 Index=StoredIndex++;
            if(Index<CurrentPage*ItemsPerPage || Index>=(CurrentPage+1)*ItemsPerPage)continue;
            AddStackRow(Stack);
        }
    }
    UTextBlock* HandsTitle = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    HandsTitle->SetText(FText::FromString(TEXT("EN MAIN")));
    HandsTitle->SetColorAndOpacity(FSlateColor(FLinearColor(.32f, .86f, .94f)));
    ItemList->AddChildToVerticalBox(HandsTitle)->SetPadding(FMargin(14.f, 14.f, 8.f, 5.f));
    for (const FAnomaliaInventoryStack& Stack : Inventory->Stacks)
        if (Stack.ContainerId == TEXT("hands")) AddStackRow(Stack);
    if(HadFocus && GetOwningPlayer())
    {
        UButton* Fallback=nullptr;
        for(const auto& Relay:ActionRelays)
        {
            if(Relay->Action==EAnomaliaInventoryAction::Stow&&Relay->StackId==0)Fallback=Relay->Button;
            if(Relay->Action==PreviousAction&&Relay->StackId==PreviousStack&&Relay->OtherStackId==PreviousOther)
            {Relay->Button->SetUserFocus(GetOwningPlayer());return;}
        }
        if(Fallback)Fallback->SetUserFocus(GetOwningPlayer());
    }
}

void UAnomaliaInventoryWidget::AddStackRow(const FAnomaliaInventoryStack& Stack)
{
    UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(),
        MakeUniqueObjectName(WidgetTree,UHorizontalBox::StaticClass(),FName(*FString::Printf(TEXT("InventoryStack_%d_row"),Stack.StackId))));
    ItemList->AddChildToVerticalBox(Row)->SetPadding(FMargin(12.f, 3.f));
    UTextBlock* Label = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    const FIntPoint Size=Inventory->GetItemSize(Stack.ItemId,Stack.bRotated);
    Label->SetText(FText::FromString(FString::Printf(TEXT("%s  ×%d · %d×%d cases [%s · %d,%d]"), *Inventory->GetItemDisplayName(Stack.ItemId), Stack.Count,Size.X,Size.Y, *Stack.ContainerId.ToString(), Stack.X, Stack.Y)));
    Label->SetColorAndOpacity(FSlateColor(FLinearColor(.91f, .95f, .96f)));
    Row->AddChildToHorizontalBox(Label)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

    const FString UseLabel=Inventory->GetUseActionLabel(Stack.ItemId);
    if(!UseLabel.IsEmpty())
    {
        auto* UseButton=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),
            MakeUniqueObjectName(WidgetTree,UButton::StaticClass(),FName(*FString::Printf(TEXT("UseStack_%d_action"),Stack.StackId))));
        auto* UseText=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        UseText->SetText(FText::FromString(UseLabel));UseButton->SetContent(UseText);
        UseButton->SetIsEnabled(!Inventory->IsPersistenceLocked());
        Row->AddChildToHorizontalBox(UseButton)->SetPadding(FMargin(5.f));
        BindAction(UseButton,EAnomaliaInventoryAction::Use,Stack.StackId,Stack.Count);
    }

    if (Inventory && Inventory->bBankingAvailable && Stack.ItemId.ToString().StartsWith(TEXT("eur_note_")))
    {
        UButton* Deposit = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), MakeUniqueObjectName(WidgetTree, UButton::StaticClass(), FName(*FString::Printf(TEXT("BankDeposit_%d_action"), Stack.StackId))));
        UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        Text->SetText(FText::FromString(TEXT("Déposer 1 billet"))); Deposit->SetContent(Text);
        Row->AddChildToHorizontalBox(Deposit)->SetPadding(FMargin(5.f));
        BindAction(Deposit, EAnomaliaInventoryAction::DepositNote, Stack.StackId);
    }
    UButton* HandsButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
    UTextBlock* HandsLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    if(NearbyVehicle && NearbyVehicle->SurvivalSystems->HasOpenPanel(TEXT("trunk")) && !NearbyVehicle->SurvivalSystems->State.bLocked)
    {
        auto* Deposit=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
        auto* Text=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Text->SetText(FText::FromString(TEXT("Déposer au coffre")));Deposit->SetContent(Text);Row->AddChildToHorizontalBox(Deposit);
        BindAction(Deposit,EAnomaliaInventoryAction::VehicleService,Stack.StackId,Stack.Count,static_cast<int32>(EAnomaliaVehicleServiceAction::Deposit));
    }
    const bool bHeld = Stack.ContainerId == TEXT("hands");
    HandsLabel->SetText(FText::FromString(bHeld ? TEXT("Ranger") : TEXT("Mains")));
    HandsButton->SetContent(HandsLabel);
    Row->AddChildToHorizontalBox(HandsButton)->SetPadding(FMargin(5.f));
    BindAction(HandsButton, bHeld ? EAnomaliaInventoryAction::Stow : EAnomaliaInventoryAction::MoveToHands, Stack.StackId);

    if(!bHeld && Size.X!=Size.Y)
    {
        auto* RotateButton=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),
            MakeUniqueObjectName(WidgetTree,UButton::StaticClass(),FName(*FString::Printf(TEXT("RotateStack_%d_action"),Stack.StackId))));
        auto* RotateLabel=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        RotateLabel->SetText(FText::FromString(TEXT("Tourner 90°")));RotateButton->SetContent(RotateLabel);
        RotateButton->SetIsEnabled(!Inventory->IsPersistenceLocked());
        Row->AddChildToHorizontalBox(RotateButton)->SetPadding(FMargin(5.f));
        BindAction(RotateButton,EAnomaliaInventoryAction::Rotate,Stack.StackId);
    }

    if (Stack.Count > 1)
    {
        UButton* SplitButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
        UTextBlock* SplitLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        SplitLabel->SetText(FText::FromString(TEXT("½ pile")));
        SplitButton->SetContent(SplitLabel);
        Row->AddChildToHorizontalBox(SplitButton)->SetPadding(FMargin(5.f));
        BindAction(SplitButton, EAnomaliaInventoryAction::SplitHalf, Stack.StackId, Stack.Count / 2);
    }

    const FAnomaliaInventoryStack* Matching = Inventory->Stacks.FindByPredicate([&](const FAnomaliaInventoryStack& Other)
    {
        return Other.ItemId == Stack.ItemId && Other.StackId != Stack.StackId && Other.ContainerId != TEXT("hands") && Stack.ContainerId != TEXT("hands");
    });
    if (Matching)
    {
        UButton* MergeButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
        UTextBlock* MergeLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        MergeLabel->SetText(FText::FromString(TEXT("Fusionner")));
        MergeButton->SetContent(MergeLabel);
        Row->AddChildToHorizontalBox(MergeButton)->SetPadding(FMargin(5.f));
        BindAction(MergeButton, EAnomaliaInventoryAction::Merge, Stack.StackId, 0, Matching->StackId);
    }
}

void UAnomaliaInventoryWidget::BindAction(UButton* Button, EAnomaliaInventoryAction Action, int32 StackId, int32 Count, int32 OtherStackId)
{
    if (!Button) return;
    UAnomaliaInventoryActionRelay* Relay = NewObject<UAnomaliaInventoryActionRelay>(this);
    Relay->TargetWidget = this;
    Relay->Button=Button;
    Relay->Action = Action;
    Relay->StackId = StackId;
    Relay->Count = Count;
    Relay->OtherStackId = OtherStackId;
    ActionRelays.Add(Relay);
    Button->OnClicked.AddDynamic(Relay, &UAnomaliaInventoryActionRelay::Execute);
}

void UAnomaliaInventoryWidget::PerformAction(EAnomaliaInventoryAction Action, int32 StackId, int32 Count, int32 OtherStackId)
{
    if (!Inventory) return;
    switch (Action)
    {
        case EAnomaliaInventoryAction::VehicleService:
            if(OtherStackId==int32(EAnomaliaVehicleServiceAction::Deposit) && StackId==0)
            {
                const auto* Held=Inventory->Stacks.FindByPredicate([](const auto& Stack){return Stack.ContainerId==TEXT("hands");});
                if(!Held)break;StackId=Held->StackId;Count=Held->Count;
            }
            if(auto* User=Cast<AAnomaliaSurvivor>(GetOwningPlayerPawn()))
                User->RequestVehicleService(NearbyVehicle,static_cast<EAnomaliaVehicleServiceAction>(OtherStackId),StackId,Count);
            break;
        case EAnomaliaInventoryAction::MoveToHands:
            Inventory->RequestMoveStack(StackId, TEXT("hands"), 0, 0, false);
            FocusFirstAction();
            break;
        case EAnomaliaInventoryAction::Stow:
            Inventory->RequestStowStack(StackId);
            FocusFirstAction();
            break;
        case EAnomaliaInventoryAction::Rotate:
        {
            const auto* Stack=Inventory->Stacks.FindByPredicate([&](const auto& S){return S.StackId==StackId;});
            if(Stack)Inventory->RequestMoveStack(StackId,Stack->ContainerId,Stack->X,Stack->Y,!Stack->bRotated);
            FocusFirstAction();
            break;
        }
        case EAnomaliaInventoryAction::SplitHalf:
            Inventory->RequestSplitStack(StackId, Count);
            break;
        case EAnomaliaInventoryAction::Merge:
            Inventory->RequestMergeStacks(StackId, OtherStackId);
            break;
        case EAnomaliaInventoryAction::Use:
            Inventory->RequestUseStack(StackId,Count);
            FocusFirstAction();
            break;
        case EAnomaliaInventoryAction::DepositNote:
        {
            const auto* Stack = Inventory->Stacks.FindByPredicate([&](const auto& Row) { return Row.StackId == StackId; });
            if (Stack) Inventory->RequestBankOperation(EAnomaliaBankAction::Deposit, Stack->ItemId);
            break;
        }
        case EAnomaliaInventoryAction::WithdrawNote:
            Inventory->RequestBankOperation(EAnomaliaBankAction::Withdraw, FName(*FString::Printf(TEXT("eur_note_%d"), Count)));
            break;
        default:
            break;
    }
}

void UAnomaliaInventoryWidget::TransferMoney()
{
    if (!Inventory || !BankRecipient || !BankAmount || !BankStatus) return;
    FString Input = BankAmount->GetText().ToString().TrimStartAndEnd().Replace(TEXT(","), TEXT("."));
    FString Whole, Fraction;
    if (!Input.Split(TEXT("."), &Whole, &Fraction)) Whole = Input;
    const auto Digits = [](const FString& Text)
    { for (TCHAR C : Text) if (C < '0' || C > '9') return false; return true; };
    if (Whole.IsEmpty() || Whole.Len() > 10 || Fraction.Len() > 2 || !Digits(Whole) || !Digits(Fraction))
    { BankStatus->SetText(FText::FromString(TEXT("Montant invalide : utilisez un nombre positif, avec deux décimales au maximum."))); return; }
    if (Fraction.Len() == 1) Fraction += TEXT("0");
    const int64 Amount = FCString::Atoi64(*Whole)*100 + (Fraction.IsEmpty() ? 0 : FCString::Atoi64(*Fraction));
    Inventory->RequestBankOperation(EAnomaliaBankAction::Transfer, NAME_None, BankRecipient->GetText().ToString().TrimStartAndEnd(), Amount);
}

void UAnomaliaInventoryWidget::FocusFirstAction()
{
    if (CloseButton && GetOwningPlayer()) CloseButton->SetUserFocus(GetOwningPlayer());
}

void UAnomaliaInventoryWidget::PreviousPage()
{
    if(CurrentPage<=0)return;
    --CurrentPage;RefreshInventory();
    if(PreviousPageButton && PreviousPageButton->GetIsEnabled() && GetOwningPlayer())PreviousPageButton->SetUserFocus(GetOwningPlayer());
    else FocusFirstAction();
}
void UAnomaliaInventoryWidget::NextPage()
{
    if(CurrentPage+1>=PageCount)return;
    ++CurrentPage;RefreshInventory();
    if(NextPageButton && NextPageButton->GetIsEnabled() && GetOwningPlayer())NextPageButton->SetUserFocus(GetOwningPlayer());
    else FocusFirstAction();
}

void UAnomaliaInventoryWidget::CloseInventory()
{
    if (auto* Survivor = Cast<AAnomaliaSurvivor>(GetOwningPlayerPawn()))
        Survivor->CloseInventory();
}

FReply UAnomaliaInventoryWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    if(Event.GetKey()==EKeys::PageUp || Event.GetKey()==EKeys::Gamepad_LeftShoulder)
    { PreviousPage();return FReply::Handled(); }
    if(Event.GetKey()==EKeys::PageDown || Event.GetKey()==EKeys::Gamepad_RightShoulder)
    { NextPage();return FReply::Handled(); }
    if (Event.GetKey() == EKeys::Gamepad_FaceButton_Right || Event.GetKey() == EKeys::Gamepad_Special_Left || Event.GetKey() == EKeys::Escape)
    {
        CloseInventory();
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(Geometry, Event);
}

void UAnomaliaInventoryWidget::AddVehicleButton(const FString& Label,int32 ServiceAction,int32 StackId,int32 Count)
{
 auto* Button=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
 auto* Text=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Text->SetText(FText::FromString(Label));Text->SetAutoWrapText(true);Button->SetContent(Text);
 ProximityList->AddChildToVerticalBox(Button)->SetPadding(FMargin(8.f,4.f));
 BindAction(Button,EAnomaliaInventoryAction::VehicleService,StackId,Count,ServiceAction);
}
void UAnomaliaInventoryWidget::RefreshVehicleProximity()
{
 if(!ProximityList||!GetWorld())return;ProximityList->ClearChildren();
 auto* User=Cast<AAnomaliaSurvivor>(GetOwningPlayerPawn());AAnomaliaChaosRoadVehicle* Nearest=nullptr;double Distance=FMath::Square(200.f);
 if(User)for(TActorIterator<AAnomaliaChaosRoadVehicle> It(GetWorld());It;++It)
 {
  auto* Vehicle=*It;if(!Vehicle->SurvivalSystems->bEnabled)continue;
  const double Candidate=Vehicle->Body->Bounds.GetBox().ComputeSquaredDistanceToPoint(User->GetActorLocation());
  if(Candidate<Distance){Distance=Candidate;Nearest=Vehicle;}
 }
 if(NearbyVehicle!=Nearest)
 {
  if(NearbyVehicle){NearbyVehicle->CargoInventory->OnInventoryUpdated.RemoveDynamic(this,&UAnomaliaInventoryWidget::RefreshInventory);NearbyVehicle->SurvivalSystems->OnServicesUpdated.RemoveDynamic(this,&UAnomaliaInventoryWidget::RefreshInventory);}
  NearbyVehicle=Nearest;
  if(NearbyVehicle){NearbyVehicle->CargoInventory->OnInventoryUpdated.AddDynamic(this,&UAnomaliaInventoryWidget::RefreshInventory);NearbyVehicle->SurvivalSystems->OnServicesUpdated.AddDynamic(this,&UAnomaliaInventoryWidget::RefreshInventory);}
 }
 auto Label=[&](const FString& Value){auto* Text=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Text->SetText(FText::FromString(Value));Text->SetAutoWrapText(true);ProximityList->AddChildToVerticalBox(Text)->SetPadding(FMargin(10.f,6.f));};
 Label(TEXT("PROXIMITÉ / VÉHICULE"));
 if(!NearbyVehicle){Label(TEXT("Approchez du véhicule puis ouvrez son coffre ou son capot."));return;}
 const auto* Systems=NearbyVehicle->SurvivalSystems.Get();const auto& State=Systems->State;
 Label(State.bLocked?TEXT("Véhicule verrouillé — clé correspondante requise."):TEXT("Véhicule déverrouillé"));
 if(!Systems->bReady){Label(TEXT("Chargement de la sauvegarde du véhicule…"));return;}
 using Action=EAnomaliaVehicleServiceAction;
 if(!State.bKeyIssued)AddVehicleButton(TEXT("Récupérer la clé d’origine"),int32(Action::TakeInitialKey));
 AddVehicleButton(State.bLocked?TEXT("Déverrouiller avec ma clé"):TEXT("Verrouiller avec ma clé"),int32(Action::ToggleLock));
 if(State.bLocked)return;
 auto Piece=[&](const TCHAR* Name,bool Present,Action Install,Action Remove){AddVehicleButton(FString(Name)+(Present?TEXT(" · retirer"):TEXT(" · emplacement vide : installer")),int32(Present?Remove:Install));};
 if(Systems->HasOpenPanel(TEXT("hood")))
 {
  Label(TEXT("CAPOT — PIÈCES FONCTIONNELLES"));Piece(TEXT("Radiateur"),State.bRadiator,Action::InstallRadiator,Action::RemoveRadiator);
  Piece(TEXT("Bougie d’allumage"),State.bSparkPlug,Action::InstallSparkPlug,Action::RemoveSparkPlug);
  AddVehicleButton(FString::Printf(TEXT("Liquide de refroidissement : %.0f %% · remplir avec de l’eau"),State.Coolant*100),int32(Action::FillCoolant));
 }
 else Label(TEXT("Ouvrez le capot pour accéder au radiateur et à l’allumage."));
 if(Systems->HasOpenPanel(Systems->BatteryAccessPanel))Piece(TEXT("Batterie"),State.bBattery,Action::InstallBattery,Action::RemoveBattery);
 if(!Systems->HasOpenPanel(TEXT("trunk"))){Label(TEXT("Ouvrez la malle pour accéder à la cargaison."));return;}
 const auto* Cargo=NearbyVehicle->CargoInventory.Get();int32 Cells=0;for(const auto& Box:Cargo->Compartments)Cells+=Box.Width*Box.Height;
 Label(FString::Printf(TEXT("COFFRE · %d cases · %.1f / %.1f kg"),Cells,Cargo->GetCurrentWeightKg(),Cargo->WeightCapacityKg));
 AddVehicleButton(TEXT("Cargaison — déposer ici (maintenir Croix) / objet en mains (Carré)"),int32(Action::Deposit));
 for(const auto& Stack:Cargo->Stacks)
  AddVehicleButton(FString::Printf(TEXT("%s ×%d · prendre (Croix), mains (Carré)"),*Cargo->GetItemDisplayName(Stack.ItemId),Stack.Count),int32(Action::Withdraw),Stack.StackId,Stack.Count);
}
UAnomaliaInventoryActionRelay* UAnomaliaInventoryWidget::FocusedAction() const
{for(const auto& Relay:ActionRelays)if(Relay&&Relay->Button&&Relay->Button->HasUserFocus(GetOwningPlayer()))return Relay.Get();return nullptr;}
FReply UAnomaliaInventoryWidget::NativeOnPreviewKeyDown(const FGeometry& Geometry,const FKeyEvent& Event)
{
 auto* Focus=FocusedAction();const auto Key=Event.GetKey();
 if(Key==EKeys::Gamepad_FaceButton_Left&&Focus)
 {
  if(Focus->Action==EAnomaliaInventoryAction::VehicleService)
  {
   auto Action=static_cast<EAnomaliaVehicleServiceAction>(Focus->OtherStackId);
   if(Action==EAnomaliaVehicleServiceAction::Withdraw)Action=EAnomaliaVehicleServiceAction::WithdrawToHands;
   if(Action==EAnomaliaVehicleServiceAction::WithdrawToHands||Action==EAnomaliaVehicleServiceAction::Deposit)
   {PerformAction(EAnomaliaInventoryAction::VehicleService,Focus->StackId,Focus->Count,int32(Action));return FReply::Handled();}
  }
  if(Focus->Action==EAnomaliaInventoryAction::MoveToHands||Focus->Action==EAnomaliaInventoryAction::Stow)
  {
   const auto* Stack=Inventory?Inventory->Stacks.FindByPredicate([&](const auto& S){return S.StackId==Focus->StackId;}):nullptr;
   if(Stack)PerformAction(Stack->ContainerId==TEXT("hands")?EAnomaliaInventoryAction::VehicleService:EAnomaliaInventoryAction::MoveToHands,Stack->StackId,Stack->Count,int32(EAnomaliaVehicleServiceAction::Deposit));
   return FReply::Handled();
  }
 }
 if(Key==EKeys::Gamepad_FaceButton_Bottom)
 {
  if(DraggedStackId)return FReply::Handled();
  if(Focus&&Focus->StackId>0)
  {
   bDraggingFromVehicle=Focus->Action==EAnomaliaInventoryAction::VehicleService&&Focus->OtherStackId==int32(EAnomaliaVehicleServiceAction::Withdraw);
   if(bDraggingFromVehicle){DraggedStackId=Focus->StackId;DraggedCount=Focus->Count;return FReply::Handled();}
   if(Focus->Action==EAnomaliaInventoryAction::MoveToHands||Focus->Action==EAnomaliaInventoryAction::Stow)
   {
    const auto* Stack=Inventory->Stacks.FindByPredicate([&](const auto& S){return S.StackId==Focus->StackId;});
    if(Stack){DraggedStackId=Stack->StackId;DraggedCount=Stack->Count;return FReply::Handled();}
   }
  }
 }
 return Super::NativeOnPreviewKeyDown(Geometry,Event);
}
FReply UAnomaliaInventoryWidget::NativeOnKeyUp(const FGeometry& Geometry,const FKeyEvent& Event)
{
 if(Event.GetKey()!=EKeys::Gamepad_FaceButton_Bottom||!DraggedStackId)return Super::NativeOnKeyUp(Geometry,Event);
 const int32 Stack=DraggedStackId,Count=DraggedCount;DraggedStackId=DraggedCount=0;
 const auto* Focus=FocusedAction();if(!Focus)return FReply::Handled();
 if(bDraggingFromVehicle)
 {
  if(Focus->Action!=EAnomaliaInventoryAction::VehicleService)
   PerformAction(EAnomaliaInventoryAction::VehicleService,Stack,Count,int32(Focus->Action==EAnomaliaInventoryAction::MoveToHands?EAnomaliaVehicleServiceAction::WithdrawToHands:EAnomaliaVehicleServiceAction::Withdraw));
 }
 else if(Focus->Action==EAnomaliaInventoryAction::VehicleService)
 {
  const auto Action=static_cast<EAnomaliaVehicleServiceAction>(Focus->OtherStackId);
  if(Action==EAnomaliaVehicleServiceAction::Deposit||Action==EAnomaliaVehicleServiceAction::Withdraw||Action==EAnomaliaVehicleServiceAction::InstallBattery||Action==EAnomaliaVehicleServiceAction::InstallRadiator||Action==EAnomaliaVehicleServiceAction::InstallSparkPlug)
   PerformAction(EAnomaliaInventoryAction::VehicleService,Stack,Count,int32(Action==EAnomaliaVehicleServiceAction::Withdraw?EAnomaliaVehicleServiceAction::Deposit:Action));
 }
 else if(Focus->Action==EAnomaliaInventoryAction::MoveToHands)PerformAction(EAnomaliaInventoryAction::MoveToHands,Stack,Count,0);
 return FReply::Handled();
}
