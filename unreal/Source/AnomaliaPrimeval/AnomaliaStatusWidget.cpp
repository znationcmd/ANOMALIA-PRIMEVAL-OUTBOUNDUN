#include "AnomaliaStatusWidget.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaVitalsComponent.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"

void UAnomaliaStatusWidget::InitializeForSurvivor(AAnomaliaSurvivor* InSurvivor)
{
    Survivor = InSurvivor;
    RefreshFromSurvivor();
}

void UAnomaliaStatusWidget::NativeConstruct()
{
    Super::NativeConstruct();
    SetVisibility(ESlateVisibility::HitTestInvisible);
    BuildLayout();
    RefreshFromSurvivor();
}

void UAnomaliaStatusWidget::BuildLayout()
{
    if (!WidgetTree || WidgetTree->RootWidget) return;
    auto* Root = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("StatusCanvas"));
    WidgetTree->RootWidget = Root;
    auto* Frame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("StatusFrame"));
    Frame->SetBrushColor(FLinearColor(.012f,.025f,.035f,.88f));
    Frame->SetPadding(FMargin(12.f,8.f));
    auto* Slot = Root->AddChildToCanvas(Frame);
    Slot->SetAnchors(FAnchors(.98f,.98f));
    Slot->SetAlignment(FVector2D(1.f,1.f));
    Slot->SetAutoSize(true);
    auto* Rows = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("StatusRows"));
    Frame->SetContent(Rows);
    for (const FName Id : {FName(TEXT("health")),FName(TEXT("thirst")),FName(TEXT("hunger")),
                         FName(TEXT("stamina")),FName(TEXT("fatigue")),FName(TEXT("temperature"))})
    {
        auto* Label = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*(TEXT("Vital_")+Id.ToString())));
        Label->SetFont(FSlateFontInfo(FName("Roboto"),16,EFontHinting::Default));
        Rows->AddChildToVerticalBox(Label)->SetPadding(FMargin(0.f,2.f));
        VitalLabels.Add(Id,Label);
    }
    Conditions = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(),TEXT("ActiveConditions"));
    Conditions->SetAutoWrapText(true);
    Conditions->SetWrapTextAt(300.f);
    Conditions->SetColorAndOpacity(FSlateColor(FLinearColor(1.f,.67f,.25f)));
    Rows->AddChildToVerticalBox(Conditions)->SetPadding(FMargin(0.f,6.f,0.f,0.f));
}

void UAnomaliaStatusWidget::RefreshFromSurvivor()
{
    const auto* Target = Survivor.Get();
    if (!Target) return;
    const auto* Vitals = Target->VitalsComponent.Get();
    auto Set = [this](FName Id, const TCHAR* Label, float Value, bool Critical, bool Temperature=false)
    {
        auto* Entry = VitalLabels.Find(Id);
        if (!Entry || !*Entry) return;
        const FString Text=Temperature ? FString::Printf(TEXT("%s : %.1f °C"),Label,Value)
            : FString::Printf(TEXT("%s : %.0f %%"),Label,Value);
        (*Entry)->SetText(FText::FromString(Text));
        (*Entry)->SetColorAndOpacity(FSlateColor(Critical ? FLinearColor(1.f,.3f,.25f) : FLinearColor(.9f,.95f,.98f)));
    };
    Set(TEXT("health"),TEXT("Santé"),Target->Health,Target->Health<25.f);
    Set(TEXT("thirst"),TEXT("Soif"),Target->Thirst,Target->Thirst<25.f);
    Set(TEXT("hunger"),TEXT("Faim"),Target->Hunger,Target->Hunger<25.f);
    Set(TEXT("fatigue"),TEXT("Fatigue"),Target->Fatigue,Target->Fatigue>=70.f);
    if (Vitals)
    {
        Set(TEXT("stamina"),TEXT("Endurance"),Vitals->Stamina,Vitals->Stamina<15.f);
        Set(TEXT("temperature"),TEXT("Température"),Vitals->BodyTemperatureC,
            Vitals->BodyTemperatureC<35.f || Vitals->BodyTemperatureC>39.f,true);
    }
    TArray<FString> Active;
    if (Target->bSleeping) Active.Add(FString::Printf(TEXT("Sommeil · %.0f s"),FMath::CeilToFloat(Target->SleepRemainingSeconds)));
    else if (Target->Fatigue>=70.f) Active.Add(TEXT("Épuisé"));
    else if (Target->Fatigue>=35.f) Active.Add(TEXT("Fatigué"));
    if (Vitals && Vitals->BodyTemperatureC<35.f) Active.Add(TEXT("Hypothermie"));
    if (Vitals && Vitals->BodyTemperatureC>39.f) Active.Add(TEXT("Hyperthermie"));
    if (Conditions)
    {
        Conditions->SetText(FText::FromString(FString::Join(Active,TEXT(" · "))));
        Conditions->SetVisibility(Active.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
    }
}

void UAnomaliaStatusWidget::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
    Super::NativeTick(Geometry,DeltaTime);
    RefreshElapsed+=DeltaTime;
    if (RefreshElapsed>=.1f) { RefreshElapsed=0.f; RefreshFromSurvivor(); }
}

FText UAnomaliaStatusWidget::GetVitalText(FName Id) const
{
    const auto* Entry = VitalLabels.Find(Id);
    return Entry && *Entry ? (*Entry)->GetText() : FText::GetEmpty();
}

FText UAnomaliaStatusWidget::GetConditionText() const
{
    return Conditions ? Conditions->GetText() : FText::GetEmpty();
}
