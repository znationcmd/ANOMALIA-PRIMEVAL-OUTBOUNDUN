#include "AnomaliaRefrigeratorWidget.h"
#include "AnomaliaRefrigerator.h"
#include "AnomaliaPowerGenerator.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaInventoryComponent.h"
#include "AnomaliaFoodPreservation.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/ScrollBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"

void UAnomaliaFridgeActionRelay::Execute()
{
    if (Widget) Widget->PerformTransfer(ItemId, bDeposit);
}

void UAnomaliaRefrigeratorWidget::InitializeForFridge(AAnomaliaSurvivor* InPlayer, AAnomaliaRefrigerator* InFridge)
{
    Player = InPlayer;
    Fridge = InFridge;
}

void UAnomaliaRefrigeratorWidget::NativeConstruct()
{
    Super::NativeConstruct();
    if (!WidgetTree) return;

    UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
    WidgetTree->RootWidget = Canvas;
    UBorder* Frame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
    Frame->SetBrushColor(FLinearColor(0.025f, 0.08f, 0.11f, .97f));
    UCanvasPanelSlot* FrameSlot = Canvas->AddChildToCanvas(Frame);
    FrameSlot->SetAnchors(FAnchors(.12f, .08f, .88f, .92f));
    FrameSlot->SetOffsets(FMargin(0.f));

    UVerticalBox* Container = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    Frame->SetContent(Container);
    UTextBlock* Title = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Title->SetText(FText::FromString(TEXT("ANOMALIA'Z  /  REFRIGERATEUR")));
    Title->SetColorAndOpacity(FSlateColor(FLinearColor(.35f, .9f, 1.f)));
    Container->AddChildToVerticalBox(Title)->SetPadding(FMargin(14.f, 12.f));

    PowerStatus = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Container->AddChildToVerticalBox(PowerStatus)->SetPadding(FMargin(14.f, 4.f));

    UButton* FridgeSwitch = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
    FridgeSwitchLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    FridgeSwitch->SetContent(FridgeSwitchLabel);
    FridgeSwitch->OnClicked.AddDynamic(this, &UAnomaliaRefrigeratorWidget::ToggleFridgeRequested);
    Container->AddChildToVerticalBox(FridgeSwitch)->SetPadding(FMargin(14.f, 4.f));
    if (IsValid(Fridge) && IsValid(Fridge->PowerGenerator))
    {
        UButton* GeneratorSwitch = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
        GeneratorSwitchLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        GeneratorSwitch->SetContent(GeneratorSwitchLabel);
        GeneratorSwitch->OnClicked.AddDynamic(this, &UAnomaliaRefrigeratorWidget::ToggleGeneratorRequested);
        Container->AddChildToVerticalBox(GeneratorSwitch)->SetPadding(FMargin(14.f, 4.f));
    }

    UButton* Close = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
    UTextBlock* CloseText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    CloseText->SetText(FText::FromString(TEXT("FERMER")));
    Close->SetContent(CloseText);
    Close->OnClicked.AddDynamic(this, &UAnomaliaRefrigeratorWidget::CloseRequested);
    Container->AddChildToVerticalBox(Close)->SetPadding(FMargin(14.f, 4.f));

    UHorizontalBox* Columns = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
    Container->AddChildToVerticalBox(Columns);
    UScrollBox* PlayerScroll = WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass());
    UScrollBox* FridgeScroll = WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass());
    Columns->AddChildToHorizontalBox(PlayerScroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    Columns->AddChildToHorizontalBox(FridgeScroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    PlayerList = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    StorageList = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    PlayerScroll->AddChild(PlayerList);
    FridgeScroll->AddChild(StorageList);

    if (IsValid(Fridge)) Fridge->OnRefrigeratorUpdated.AddDynamic(this, &UAnomaliaRefrigeratorWidget::RefreshContents);
    if (IsValid(Player) && IsValid(Player->InventoryComponent))
        Player->InventoryComponent->OnInventoryUpdated.AddDynamic(this, &UAnomaliaRefrigeratorWidget::RefreshContents);
    RefreshContents();
}

void UAnomaliaRefrigeratorWidget::NativeDestruct()
{
    if (IsValid(Fridge)) Fridge->OnRefrigeratorUpdated.RemoveDynamic(this, &UAnomaliaRefrigeratorWidget::RefreshContents);
    if (IsValid(Player) && IsValid(Player->InventoryComponent))
        Player->InventoryComponent->OnInventoryUpdated.RemoveDynamic(this, &UAnomaliaRefrigeratorWidget::RefreshContents);
    Super::NativeDestruct();
}

void UAnomaliaRefrigeratorWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    RefreshSeconds += InDeltaTime;
    if (RefreshSeconds >= 1.f)
    {
        RefreshSeconds = 0.f;
        UpdateStatus();
        if (!IsValid(Player) || !IsValid(Fridge) ||
            FVector::DistSquared(Player->GetActorLocation(), Fridge->GetActorLocation()) > FMath::Square(400.f))
            CloseRequested();
    }
}

void UAnomaliaRefrigeratorWidget::UpdateStatus()
{
    if (!PowerStatus || !IsValid(Fridge)) return;
    if (FridgeSwitchLabel) FridgeSwitchLabel->SetText(FText::FromString(Fridge->bSwitchedOn ? TEXT("ETEINDRE LE FRIGO") : TEXT("ALLUMER LE FRIGO")));
    if (GeneratorSwitchLabel && IsValid(Fridge->PowerGenerator))
        GeneratorSwitchLabel->SetText(FText::FromString(Fridge->PowerGenerator->bRunning ? TEXT("ARRETER LE GENERATEUR (a moins de 3 m)") : TEXT("DEMARRER LE GENERATEUR (a moins de 3 m)")));
    const FString Status = Fridge->bCoolingActive ? TEXT("REFROIDISSEMENT ACTIF") :
        Fridge->bSwitchedOn ? TEXT("AUCUNE ALIMENTATION ELECTRIQUE") : TEXT("APPAREIL ETEINT");
    PowerStatus->SetText(FText::FromString(FString::Printf(
        TEXT("%s  |  %.1f C  |  %d/%d objets  |  La nourriture se degrade plus lentement a froid"),
        *Status, Fridge->InternalTemperatureC, Fridge->GetUsedCapacity(), Fridge->GetMaxCapacity())));
    PowerStatus->SetColorAndOpacity(FSlateColor(
        Fridge->bCoolingActive ? FLinearColor(.2f, .92f, .78f) : FLinearColor(1.f, .63f, .32f)));
}

void UAnomaliaRefrigeratorWidget::RefreshContents()
{
    if (!WidgetTree || !PlayerList || !StorageList) return;
    Relays.Reset();
    PlayerList->ClearChildren();
    StorageList->ClearChildren();
    UpdateStatus();

    UTextBlock* PlayerHeading = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    PlayerHeading->SetText(FText::FromString(TEXT("MON INVENTAIRE  /  DEPOSER 1")));
    PlayerList->AddChildToVerticalBox(PlayerHeading)->SetPadding(FMargin(12.f));
    UTextBlock* FridgeHeading = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    FridgeHeading->SetText(FText::FromString(TEXT("FRIGO  /  RETIRER 1")));
    StorageList->AddChildToVerticalBox(FridgeHeading)->SetPadding(FMargin(12.f));

    if (IsValid(Player) && IsValid(Player->InventoryComponent))
    {
        TMap<FName, int32> CountById;
        TMap<FName, float> FreshnessSum;
        for (const FAnomaliaInventoryStack& Stack : Player->InventoryComponent->Stacks)
        {
            const bool bFood = AnomaliaFoodPreservation::IsPerishable(Stack.ItemId) ||
                Stack.ItemId == TEXT("water") || Stack.ItemId == TEXT("food");
            if (!bFood) continue;
            CountById.FindOrAdd(Stack.ItemId) += Stack.Count;
            FreshnessSum.FindOrAdd(Stack.ItemId) += Stack.Freshness01 * Stack.Count;
        }
        for (const auto& Pair : CountById)
            AddRow(PlayerList, Pair.Key, Pair.Value,
                FreshnessSum.FindRef(Pair.Key) / FMath::Max(1, Pair.Value), true);
    }
    if (IsValid(Fridge))
        for (const FAnomaliaRefrigeratorItem& Item : Fridge->Contents)
            AddRow(StorageList, Item.ItemId, Item.Count, Item.Freshness01, false);
}

void UAnomaliaRefrigeratorWidget::AddRow(UVerticalBox* List, FName ItemId, int32 Count,
    float Freshness01, bool bDeposit)
{
    UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
    List->AddChildToVerticalBox(Row)->SetPadding(FMargin(10.f, 4.f));
    UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Text->SetText(FText::FromString(FString::Printf(TEXT("%s x%d  /  %d%% frais"),
        *ItemId.ToString(), Count, FMath::RoundToInt(Freshness01 * 100.f))));
    Text->SetColorAndOpacity(FSlateColor(Freshness01 > .2f ?
        FLinearColor(.86f, .93f, .96f) : FLinearColor(1.f, .35f, .25f)));
    Row->AddChildToHorizontalBox(Text)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
    UTextBlock* ButtonLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    ButtonLabel->SetText(FText::FromString(bDeposit ? TEXT("+1") : TEXT("-1")));
    Button->SetContent(ButtonLabel);
    Row->AddChildToHorizontalBox(Button)->SetPadding(FMargin(4.f));
    UAnomaliaFridgeActionRelay* Relay = NewObject<UAnomaliaFridgeActionRelay>(this);
    Relay->Widget = this;
    Relay->ItemId = ItemId;
    Relay->bDeposit = bDeposit;
    Relays.Add(Relay);
    Button->OnClicked.AddDynamic(Relay, &UAnomaliaFridgeActionRelay::Execute);
}

void UAnomaliaRefrigeratorWidget::PerformTransfer(FName ItemId, bool bDeposit)
{
    if (!IsValid(Player) || !IsValid(Fridge)) return;
    if (bDeposit) Player->RequestDepositToFridge(Fridge, ItemId, 1);
    else Player->RequestWithdrawFromFridge(Fridge, ItemId, 1);
}

void UAnomaliaRefrigeratorWidget::ToggleFridgeRequested()
{
    if (IsValid(Player) && IsValid(Fridge)) Player->RequestSetFridgeOn(Fridge, !Fridge->bSwitchedOn);
}

void UAnomaliaRefrigeratorWidget::ToggleGeneratorRequested()
{
    if (IsValid(Player) && IsValid(Fridge) && IsValid(Fridge->PowerGenerator))
        Player->RequestSetGeneratorRunning(Fridge->PowerGenerator, !Fridge->PowerGenerator->bRunning);
}

void UAnomaliaRefrigeratorWidget::CloseRequested()
{
    if (IsValid(Player)) Player->CloseFridgeInterface();
}
