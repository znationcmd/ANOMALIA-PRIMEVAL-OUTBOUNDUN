#include "AnomaliaPowerUtilityWidget.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaPowerGenerator.h"
#include "AnomaliaBatteryCharger.h"
#include "AnomaliaWorkLight.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"

void UAnomaliaPowerUtilityWidget::InitializeForDevice(AAnomaliaSurvivor* InPlayer, AActor* InDevice)
{
    Player = InPlayer;
    Device = InDevice;
}

void UAnomaliaPowerUtilityWidget::NativeConstruct()
{
    Super::NativeConstruct();
    if (!WidgetTree) return;
    UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
    WidgetTree->RootWidget = Canvas;
    UBorder* Frame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
    Frame->SetBrushColor(FLinearColor(.025f, .065f, .08f, .97f));
    UCanvasPanelSlot* Slot = Canvas->AddChildToCanvas(Frame);
    Slot->SetAnchors(FAnchors(.23f, .2f, .77f, .8f));
    Slot->SetOffsets(FMargin(0.f));
    UVerticalBox* Content = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    Frame->SetContent(Content);

    UTextBlock* Title = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Title->SetText(FText::FromString(TEXT("ANOMALIA'Z  /  INSTALLATION ELECTRIQUE")));
    Title->SetColorAndOpacity(FSlateColor(FLinearColor(.35f, .92f, .98f)));
    Content->AddChildToVerticalBox(Title)->SetPadding(FMargin(16.f, 14.f));
    StatusText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    StatusText->SetAutoWrapText(true);
    Content->AddChildToVerticalBox(StatusText)->SetPadding(FMargin(16.f, 10.f));

    auto MakeAction = [&](const TCHAR* Name, UTextBlock*& Text, UButton*& Button)
    {
        Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), FName(Name));
        Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        Button->SetContent(Text);
        Content->AddChildToVerticalBox(Button)->SetPadding(FMargin(16.f, 6.f));
    };
    UButton* Primary = nullptr;
    UTextBlock* PrimaryText = nullptr;
    MakeAction(TEXT("PowerPrimary"), PrimaryText, Primary);
    PrimaryLabel = PrimaryText;
    Primary->OnClicked.AddDynamic(this, &UAnomaliaPowerUtilityWidget::ExecutePrimary);
    UTextBlock* SecondaryText = nullptr;
    UButton* Secondary = nullptr;
    MakeAction(TEXT("PowerSecondary"), SecondaryText, Secondary);
    SecondaryLabel = SecondaryText;
    SecondaryButton = Secondary;
    Secondary->OnClicked.AddDynamic(this, &UAnomaliaPowerUtilityWidget::ExecuteSecondary);
    UTextBlock* TertiaryText = nullptr;
    UButton* Tertiary = nullptr;
    MakeAction(TEXT("PowerTertiary"), TertiaryText, Tertiary);
    TertiaryLabel = TertiaryText;
    TertiaryButton = Tertiary;
    Tertiary->OnClicked.AddDynamic(this, &UAnomaliaPowerUtilityWidget::ExecuteTertiary);
    UButton* Close = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
    UTextBlock* CloseLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    CloseLabel->SetText(FText::FromString(TEXT("FERMER")));
    Close->SetContent(CloseLabel);
    Close->OnClicked.AddDynamic(this, &UAnomaliaPowerUtilityWidget::CloseRequested);
    Content->AddChildToVerticalBox(Close)->SetPadding(FMargin(16.f, 10.f));
    Refresh();
}

void UAnomaliaPowerUtilityWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    RefreshElapsed += InDeltaTime;
    if (RefreshElapsed >= .5f)
    {
        RefreshElapsed = 0.f;
        Refresh();
        if (!IsValid(Player) || !IsValid(Device) ||
            FVector::DistSquared(Player->GetActorLocation(), Device->GetActorLocation()) > FMath::Square(400.f))
            CloseRequested();
    }
}

void UAnomaliaPowerUtilityWidget::Refresh()
{
    if (!IsValid(Device) || !StatusText || !PrimaryLabel || !SecondaryButton || !TertiaryButton) return;
    if (const AAnomaliaPowerGenerator* Generator = Cast<AAnomaliaPowerGenerator>(Device))
    {
        StatusText->SetText(FText::FromString(FString::Printf(
            TEXT("GENERATEUR PORTABLE\n%s\nCarburant : %.1f / 30.0 L\nBranchement : 15 m\nDeplacer uniquement a l'arret."),
            Generator->bRunning ? TEXT("EN MARCHE") : TEXT("A L'ARRET"), Generator->FuelLitres)));
        PrimaryLabel->SetText(FText::FromString(Generator->bRunning ? TEXT("ARRETER") : TEXT("DEMARRER")));
        SecondaryLabel->SetText(FText::FromString(TEXT("REMPLIR : 1 JERRICAN (5 L)")));
        TertiaryLabel->SetText(FText::FromString(
            Generator->Carrier == Player ? TEXT("POSER AU SOL") : TEXT("PORTER LE GENERATEUR")));
        SecondaryButton->SetVisibility(ESlateVisibility::Visible);
        TertiaryButton->SetVisibility(ESlateVisibility::Visible);
    }
    else if (const AAnomaliaBatteryCharger* Charger = Cast<AAnomaliaBatteryCharger>(Device))
    {
        StatusText->SetText(FText::FromString(FString::Printf(
            TEXT("CHARGEUR DE BATTERIE 12 V\n%s\nBatterie : %s\nCharge : %.0f %%"),
            Charger->bCharging ? TEXT("CHARGE EN COURS") : TEXT("EN ATTENTE / SANS COURANT"),
            Charger->bHasBattery ? TEXT("INSEREE") : TEXT("ABSENTE"),
            Charger->BatteryCharge01 * 100.f)));
        PrimaryLabel->SetText(FText::FromString(Charger->bSwitchedOn ? TEXT("ETEINDRE") : TEXT("ALLUMER")));
        SecondaryLabel->SetText(FText::FromString(TEXT("INSERER BATTERIE DEPUIS INVENTAIRE")));
        TertiaryLabel->SetText(FText::FromString(TEXT("RECUPERER LA BATTERIE")));
        SecondaryButton->SetVisibility(ESlateVisibility::Visible);
        TertiaryButton->SetVisibility(ESlateVisibility::Visible);
    }
    else if (const AAnomaliaWorkLight* Light = Cast<AAnomaliaWorkLight>(Device))
    {
        StatusText->SetText(FText::FromString(FString::Printf(
            TEXT("PROJECTEUR DE CHANTIER\n%s\nElectricite requise."),
            Light->bIsLit ? TEXT("ECLAIRAGE ACTIF") : TEXT("ETEINT / SANS COURANT"))));
        PrimaryLabel->SetText(FText::FromString(Light->bSwitchedOn ? TEXT("ETEINDRE") : TEXT("ALLUMER")));
        SecondaryButton->SetVisibility(ESlateVisibility::Collapsed);
        TertiaryButton->SetVisibility(ESlateVisibility::Collapsed);
    }
}

void UAnomaliaPowerUtilityWidget::ExecutePrimary()
{
    if (!IsValid(Player) || !IsValid(Device)) return;
    if (AAnomaliaPowerGenerator* G = Cast<AAnomaliaPowerGenerator>(Device))
        Player->RequestSetGeneratorRunning(G, !G->bRunning);
    else if (AAnomaliaBatteryCharger* C = Cast<AAnomaliaBatteryCharger>(Device))
        Player->RequestSetChargerOn(C, !C->bSwitchedOn);
    else if (AAnomaliaWorkLight* L = Cast<AAnomaliaWorkLight>(Device))
        Player->RequestSetWorkLightOn(L, !L->bSwitchedOn);
}

void UAnomaliaPowerUtilityWidget::ExecuteSecondary()
{
    if (!IsValid(Player) || !IsValid(Device)) return;
    if (AAnomaliaPowerGenerator* G = Cast<AAnomaliaPowerGenerator>(Device))
        Player->RequestRefuelGenerator(G);
    else if (AAnomaliaBatteryCharger* C = Cast<AAnomaliaBatteryCharger>(Device))
        Player->RequestInsertBattery(C);
}

void UAnomaliaPowerUtilityWidget::ExecuteTertiary()
{
    if (!IsValid(Player) || !IsValid(Device)) return;
    if (AAnomaliaPowerGenerator* G = Cast<AAnomaliaPowerGenerator>(Device))
    {
        if (G->Carrier == Player) Player->RequestPlaceGenerator(G);
        else Player->RequestPickupGenerator(G);
    }
    else if (AAnomaliaBatteryCharger* C = Cast<AAnomaliaBatteryCharger>(Device))
        Player->RequestRemoveBattery(C);
}

void UAnomaliaPowerUtilityWidget::CloseRequested()
{
    if (IsValid(Player)) Player->ClosePowerUtilityInterface();
}
