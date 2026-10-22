#include "AnomaliaInventoryWidget.h"
#include "AnomaliaInventoryComponent.h"
#include "AnomaliaSurvivor.h"
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
    if (Inventory) Inventory->OnInventoryUpdated.AddDynamic(this, &UAnomaliaInventoryWidget::RefreshInventory);
    RefreshInventory();
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
    Heading->SetFont(FSlateFontInfo(FName("Roboto"), 26, EFontHinting::Default));
    Content->AddChildToVerticalBox(Heading)->SetPadding(FMargin(14.f, 10.f));
    UTextBlock* Hint = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventoryHint"));
    Hint->SetText(FText::FromString(TEXT("Déplacer un objet vers les mains · séparer une pile · fusionner deux piles")));
    Hint->SetColorAndOpacity(FSlateColor(FLinearColor(.72f, .82f, .86f)));
    Content->AddChildToVerticalBox(Hint)->SetPadding(FMargin(14.f, 0.f, 14.f, 10.f));

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

    UScrollBox* Scroll = WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(), TEXT("InventoryScroll"));
    Content->AddChildToVerticalBox(Scroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    ItemList = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("InventoryItems"));
    Scroll->AddChild(ItemList);
}

void UAnomaliaInventoryWidget::RefreshInventory()
{
    if (!ItemList || !WidgetTree) return;
    ActionRelays.Reset();
    ItemList->ClearChildren();
    if (!Inventory)
    {
        UTextBlock* Missing = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        Missing->SetText(FText::FromString(TEXT("Inventaire indisponible.")));
        ItemList->AddChildToVerticalBox(Missing);
        return;
    }

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
    const float Weight = Inventory->GetCurrentWeightKg();
    UTextBlock* WeightText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    WeightText->SetText(FText::FromString(FString::Printf(TEXT("POIDS  %.1f / %.1f KG"), Weight, Inventory->WeightCapacityKg)));
    WeightText->SetColorAndOpacity(FSlateColor(Weight > Inventory->WeightCapacityKg ? FLinearColor(1.f, .3f, .24f) : FLinearColor(.2f, .9f, .75f)));
    ItemList->AddChildToVerticalBox(WeightText)->SetPadding(FMargin(14.f, 10.f));

    for (const FAnomaliaInventoryCompartment& Box : Inventory->Compartments)
    {
        UTextBlock* BoxTitle = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        BoxTitle->SetText(FText::FromString(FString::Printf(TEXT("%s  ·  %d × %d"), *Box.Id.ToString(), Box.Width, Box.Height)));
        BoxTitle->SetColorAndOpacity(FSlateColor(FLinearColor(.32f, .86f, .94f)));
        ItemList->AddChildToVerticalBox(BoxTitle)->SetPadding(FMargin(14.f, 14.f, 8.f, 5.f));
        for (const FAnomaliaInventoryStack& Stack : Inventory->Stacks)
        {
            if (Stack.ContainerId != Box.Id) continue;
            AddStackRow(Stack);
        }
    }
    UTextBlock* HandsTitle = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    HandsTitle->SetText(FText::FromString(TEXT("EN MAIN")));
    HandsTitle->SetColorAndOpacity(FSlateColor(FLinearColor(.32f, .86f, .94f)));
    ItemList->AddChildToVerticalBox(HandsTitle)->SetPadding(FMargin(14.f, 14.f, 8.f, 5.f));
    for (const FAnomaliaInventoryStack& Stack : Inventory->Stacks)
        if (Stack.ContainerId == TEXT("hands")) AddStackRow(Stack);
}

void UAnomaliaInventoryWidget::AddStackRow(const FAnomaliaInventoryStack& Stack)
{
    UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
    ItemList->AddChildToVerticalBox(Row)->SetPadding(FMargin(12.f, 3.f));
    UTextBlock* Label = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Label->SetText(FText::FromString(FString::Printf(TEXT("%s  ×%d   [%s · %d,%d]"), *Stack.ItemId.ToString(), Stack.Count, *Stack.ContainerId.ToString(), Stack.X, Stack.Y)));
    Label->SetColorAndOpacity(FSlateColor(FLinearColor(.91f, .95f, .96f)));
    Row->AddChildToHorizontalBox(Label)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

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
    HandsLabel->SetText(FText::FromString(TEXT("Mains")));
    HandsButton->SetContent(HandsLabel);
    Row->AddChildToHorizontalBox(HandsButton)->SetPadding(FMargin(5.f));
    BindAction(HandsButton, EAnomaliaInventoryAction::MoveToHands, Stack.StackId);

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
        case EAnomaliaInventoryAction::MoveToHands:
            Inventory->RequestMoveStack(StackId, TEXT("hands"), 0, 0, false);
            break;
        case EAnomaliaInventoryAction::SplitHalf:
            Inventory->RequestSplitStack(StackId, Count);
            break;
        case EAnomaliaInventoryAction::Merge:
            Inventory->RequestMergeStacks(StackId, OtherStackId);
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

void UAnomaliaInventoryWidget::CloseInventory()
{
    if (auto* Survivor = Cast<AAnomaliaSurvivor>(GetOwningPlayerPawn()))
        Survivor->CloseInventory();
}

FReply UAnomaliaInventoryWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    if (Event.GetKey() == EKeys::Gamepad_FaceButton_Right || Event.GetKey() == EKeys::Escape)
    {
        CloseInventory();
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(Geometry, Event);
}
