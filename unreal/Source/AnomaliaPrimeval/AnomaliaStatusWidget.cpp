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
#include "Components/SafeZone.h"
#include "Components/Button.h"
#include "Components/SizeBox.h"
#include "GameFramework/PlayerController.h"

void UAnomaliaStatusWidget::InitializeForSurvivor(AAnomaliaSurvivor* InSurvivor)
{
    Survivor = InSurvivor;
    RefreshFromSurvivor();
}

void UAnomaliaStatusWidget::NativeConstruct()
{
    Super::NativeConstruct();
    SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    BuildLayout();
#if PLATFORM_ANDROID || PLATFORM_IOS
    SetTouchControlsEnabled(true);
#else
    SetTouchControlsEnabled(false);
#endif
    RefreshFromSurvivor();
}

void UAnomaliaStatusWidget::BuildLayout()
{
    if (!WidgetTree || WidgetTree->RootWidget) return;
    auto* Root = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("StatusCanvas"));
    auto* Safe=WidgetTree->ConstructWidget<USafeZone>(USafeZone::StaticClass(),TEXT("StatusSafeZone"));
    Safe->SetContent(Root);
    WidgetTree->RootWidget = Safe;
    auto* Frame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("StatusFrame"));
    Frame->SetBrushColor(FLinearColor(.012f,.025f,.035f,.88f));
    Frame->SetPadding(FMargin(12.f,8.f));
    Frame->SetVisibility(ESlateVisibility::HitTestInvisible);
    auto* FrameSlot = Root->AddChildToCanvas(Frame);
    StatusFrameSlot=FrameSlot;
    FrameSlot->SetAnchors(FAnchors(.98f,.98f));
    FrameSlot->SetAlignment(FVector2D(1.f,1.f));
    FrameSlot->SetAutoSize(true);
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
    TouchControls=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("TouchControls"));
    auto* TouchSlot=Root->AddChildToCanvas(TouchControls);
    TouchSlot->SetAnchors(FAnchors(.98f,.5f)); TouchSlot->SetAlignment(FVector2D(1.f,.5f)); TouchSlot->SetAutoSize(true);
    auto Button=[&](const TCHAR* Name,const TCHAR* Label)
    {
        auto* Size=WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
        Size->SetWidthOverride(128.f); Size->SetHeightOverride(48.f);
        TouchControls->AddChildToVerticalBox(Size)->SetPadding(FMargin(0.f,3.f));
        auto* Result=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),FName(Name));
        Result->SetIsFocusable(false);
        Size->SetContent(Result);
        auto* Text=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        Text->SetText(FText::FromString(Label)); Result->SetContent(Text);
        return Result;
    };
    Button(TEXT("TouchInteract"),TEXT("Interagir"))->OnClicked.AddDynamic(this,&UAnomaliaStatusWidget::TouchInteract);
    Button(TEXT("TouchInventory"),TEXT("Inventaire"))->OnClicked.AddDynamic(this,&UAnomaliaStatusWidget::TouchInventory);
    Button(TEXT("TouchRest"),TEXT("Repos"))->OnClicked.AddDynamic(this,&UAnomaliaStatusWidget::TouchRest);
    auto* JumpButton=Button(TEXT("TouchJump"),TEXT("Sauter"));
    JumpButton->OnPressed.AddDynamic(this,&UAnomaliaStatusWidget::TouchJumpPressed);
    JumpButton->OnReleased.AddDynamic(this,&UAnomaliaStatusWidget::TouchJumpReleased);
    auto* SprintButton=Button(TEXT("TouchSprint"),TEXT("Courir"));
    SprintButton->OnPressed.AddDynamic(this,&UAnomaliaStatusWidget::TouchSprintPressed);
    SprintButton->OnReleased.AddDynamic(this,&UAnomaliaStatusWidget::TouchSprintReleased);
}

void UAnomaliaStatusWidget::SetTouchControlsEnabled(bool Enabled)
{
    if (TouchControls) TouchControls->SetVisibility(Enabled ? ESlateVisibility::SelfHitTestInvisible : ESlateVisibility::Collapsed);
    if (StatusFrameSlot)
    {
        StatusFrameSlot->SetAnchors(Enabled ? FAnchors(.02f,.02f) : FAnchors(.98f,.98f));
        StatusFrameSlot->SetAlignment(Enabled ? FVector2D(0.f,0.f) : FVector2D(1.f,1.f));
    }
}

void UAnomaliaStatusWidget::SendLocalInput(FKey Key,EInputEvent Event)
{
    auto* PC=GetOwningPlayer();
    if (!PC || !PC->IsLocalController()) return;
    // Route through the same input bindings and server RPC checks as physical keys.
    PC->InputKey(FInputKeyParams(Key,Event,Event==IE_Pressed ? 1.0 : 0.0,false,FInputDeviceId::CreateFromInternalId(0)));
}
void UAnomaliaStatusWidget::TouchInteract() { SendLocalInput(EKeys::E,IE_Pressed); SendLocalInput(EKeys::E,IE_Released); }
void UAnomaliaStatusWidget::TouchInventory() { SendLocalInput(EKeys::I,IE_Pressed); SendLocalInput(EKeys::I,IE_Released); }
void UAnomaliaStatusWidget::TouchRest() { SendLocalInput(EKeys::R,IE_Pressed); SendLocalInput(EKeys::R,IE_Released); }
void UAnomaliaStatusWidget::TouchJumpPressed() { SendLocalInput(EKeys::SpaceBar,IE_Pressed); }
void UAnomaliaStatusWidget::TouchJumpReleased() { SendLocalInput(EKeys::SpaceBar,IE_Released); }
void UAnomaliaStatusWidget::TouchSprintPressed() { SendLocalInput(EKeys::LeftShift,IE_Pressed); }
void UAnomaliaStatusWidget::TouchSprintReleased() { SendLocalInput(EKeys::LeftShift,IE_Released); }
void UAnomaliaStatusWidget::NativeDestruct()
{
    TouchJumpReleased(); TouchSprintReleased();
    Super::NativeDestruct();
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
