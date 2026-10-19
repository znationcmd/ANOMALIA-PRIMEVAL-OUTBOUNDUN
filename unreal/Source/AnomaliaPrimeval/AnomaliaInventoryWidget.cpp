#include "AnomaliaInventoryWidget.h"
#include "AnomaliaInventoryComponent.h"
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
    WidgetTree->RootWidget = RootCanvas;
    UBorder* Frame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("InventoryFrame"));
    Frame->SetBrushColor(FLinearColor(0.012f, 0.035f, 0.055f, 0.96f));
    UCanvasPanelSlot* FrameSlot = RootCanvas->AddChildToCanvas(Frame);
    FrameSlot->SetAnchors(FAnchors(.08f, .06f, .92f, .94f));
    FrameSlot->SetOffsets(FMargin(0.f));
    FrameSlot->SetZOrder(1);

    UVerticalBox* Content = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("InventoryContent"));
    Frame->SetContent(Content);
    UTextBlock* Heading = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventoryHeading"));
    Heading->SetText(FText::FromString(TEXT("ANOMALIA  /  INVENTAIRE")));
    Heading->SetColorAndOpacity(FSlateColor(FLinearColor(.32f, .86f, .94f)));
    Heading->SetFont(FSlateFontInfo(FName("Roboto"), 26, EFontHinting::Default));
    Content->AddChildToVerticalBox(Heading)->SetPadding(FMargin(14.f, 10.f));
    UTextBlock* Hint = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventoryHint"));
    Hint->SetText(FText::FromString(TEXT("Déplacer un objet vers les mains · séparer une pile · fusionner deux piles")));
    Hint->SetColorAndOpacity(FSlateColor(FLinearColor(.72f, .82f, .86f)));
    Content->AddChildToVerticalBox(Hint)->SetPadding(FMargin(14.f, 0.f, 14.f, 10.f));

    UScrollBox* Scroll = WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(), TEXT("InventoryScroll"));
    Content->AddChildToVerticalBox(Scroll);
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
        default:
            break;
    }
}
