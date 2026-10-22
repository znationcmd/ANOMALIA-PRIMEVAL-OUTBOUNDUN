#include "AnomaliaStatusWidget.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaVitalsComponent.h"
#include "AnomaliaItemEffectsComponent.h"
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
#include "GameFramework/PlayerInput.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"
#include "HAL/PlatformTime.h"
#include <initializer_list>

UAnomaliaTouchButton::UAnomaliaTouchButton(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer)
{
    InitIsFocusable(false);
}

void UAnomaliaStatusWidget::InitializeForSurvivor(AAnomaliaSurvivor* InSurvivor)
{
    Survivor = InSurvivor;
    RefreshFromSurvivor();
}

TSharedRef<SWidget> UAnomaliaStatusWidget::RebuildWidget()
{
    if(!WidgetTree) WidgetTree=NewObject<UWidgetTree>(this,TEXT("WidgetTree"));
    BuildLayout();
    return Super::RebuildWidget();
}

void UAnomaliaStatusWidget::NativeConstruct()
{
    Super::NativeConstruct();
    SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    ForceVolatile(true); // Smooth gauges and restrained critical pulses follow live survival values.
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
    Frame->SetBrushColor(FLinearColor::Transparent);
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
                         FName(TEXT("stamina")),FName(TEXT("fatigue")),FName(TEXT("temperature")),FName(TEXT("blood"))})
    {
        auto* Label = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*(TEXT("Vital_")+Id.ToString())));
        auto LabelFont=Label->GetFont(); LabelFont.Size=16; Label->SetFont(LabelFont);
        Rows->AddChildToVerticalBox(Label)->SetPadding(FMargin(0.f,2.f));
        VitalLabels.Add(Id,Label);
        // Keep diagnostic values available to automation; visible HUD uses original vector icons.
        Label->SetVisibility(ESlateVisibility::Collapsed);
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
        auto* Result=WidgetTree->ConstructWidget<UAnomaliaTouchButton>(UAnomaliaTouchButton::StaticClass(),FName(Name));
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
    if(const auto* Effects=Target->ItemEffectsComponent.Get())
    {
        const auto& State=Effects->State;
        Set(TEXT("blood"),TEXT("Sang"),State.Blood,State.Blood<35);
        if(State.Bleeding>0) Active.Add(TEXT("Saignement"));
        if(State.Pain>10) Active.Add(TEXT("Douleur"));
        if(State.Infection>10) Active.Add(TEXT("Infection fictive"));
        if(State.Poison>10) Active.Add(TEXT("Intoxication toxique"));
        if(State.Intoxication>1) Active.Add(FString::Printf(TEXT("Effets RP : %.0f %%"),State.Intoxication));
        if(State.Dependence>40) Active.Add(TEXT("Dépendance RP"));
    }
    if (Target->bSleeping) Active.Add(FString::Printf(TEXT("Sommeil · %.0f s"),FMath::CeilToFloat(Target->SleepRemainingSeconds)));
    else if (Target->Fatigue>=70.f) Active.Add(TEXT("Épuisé"));
    else if (Target->Fatigue>=35.f) Active.Add(TEXT("Fatigué"));
    if (Vitals && Vitals->BodyTemperatureC<35.f) Active.Add(TEXT("Hypothermie"));
    if (Vitals && Vitals->BodyTemperatureC>39.f) Active.Add(TEXT("Hyperthermie"));
    if (Conditions)
    {
        Conditions->SetText(FText::FromString(FString::Join(Active,TEXT(" · "))));
        Conditions->SetVisibility(ESlateVisibility::Collapsed);
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

int32 UAnomaliaStatusWidget::NativePaint(const FPaintArgs& Args,const FGeometry& Geometry,const FSlateRect& CullingRect,
    FSlateWindowElementList& Elements,int32 LayerId,const FWidgetStyle& Style,bool ParentEnabled) const
{
    const int32 Base=Super::NativePaint(Args,Geometry,CullingRect,Elements,LayerId,Style,ParentEnabled);
    const auto* S=Survivor.Get();if(!S)return Base;
    struct FIcon{FName Id;float Fill;int32 Severity;};TArray<FIcon> Icons;
    auto Vital=[&](FName Id,float Value){Icons.Add({Id,FMath::Clamp(Value/100.f,0.f,1.f),Value<25?2:Value<50?1:0});};
    Vital(TEXT("health"),S->Health);
    const auto* Effects=S->ItemEffectsComponent.Get();
    if(Effects)Vital(TEXT("blood"),Effects->State.Blood);
    Vital(TEXT("hunger"),S->Hunger);Vital(TEXT("thirst"),S->Thirst);
    if(const auto* V=S->VitalsComponent.Get())
    {
        Vital(TEXT("stamina"),V->Stamina);
        const float T=V->BodyTemperatureC;
        Icons.Add({TEXT("temperature"),FMath::Clamp((T-30.f)/14.f,0.f,1.f),T<35||T>39?2:T<36||T>38?1:0});
    }
    Icons.Add({TEXT("fatigue"),1.f-FMath::Clamp(S->Fatigue/100.f,0.f,1.f),S->Fatigue>=90?2:S->Fatigue>=70?1:0});
    if(Effects)
    {
        if(Effects->State.Bleeding>0)Icons.Add({TEXT("bleeding"),1.f,2});
        if(Effects->State.Pain>10)Icons.Add({TEXT("injury"),1.f,Effects->State.Pain>65?2:1});
        if(Effects->State.Infection>10||Effects->State.Poison>10)Icons.Add({TEXT("illness"),1.f,FMath::Max(Effects->State.Infection,Effects->State.Poison)>65?2:1});
    }
    const FVector2D Area=Geometry.GetLocalSize();
    const float Spacing=FMath::Min(48.f,static_cast<float>((Area.X-48.f)/FMath::Max(1,Icons.Num())));
    const float Left=FMath::Max(24.f,static_cast<float>(Area.X)-32.f-Icons.Num()*Spacing);
    const float Top=FMath::Max(12.f,static_cast<float>(Area.Y)-90.f);
    for(int32 Index=0;Index<Icons.Num();++Index)
    {
        const auto& Icon=Icons[Index];
        FLinearColor Color=Icon.Severity==2?FLinearColor(.95f,.13f,.1f):Icon.Severity==1?FLinearColor(1.f,.76f,.15f):FLinearColor(.96f,.96f,.94f);
        if(Icon.Severity==2)Color.A=.7f+.3f*FMath::Abs(FMath::Sin(FPlatformTime::Seconds()*2.));
        const FVector2D Origin(Left+Index*Spacing,Top);
        auto Path=[&](std::initializer_list<FVector2D> Points)
        {
            TArray<FVector2f> Scaled;for(const auto& P:Points)Scaled.Add(FVector2f(Origin+P*32.));
            FSlateDrawElement::MakeLines(Elements,Base+1,Geometry.ToPaintGeometry(),Scaled,ESlateDrawEffect::None,Color,true,2.f);
        };
        auto Arc=[&](FVector2D Center,float Radius,float Start,float End)
        {
            TArray<FVector2f> Points;for(int32 J=0;J<=28;++J){const float Angle=FMath::Lerp(Start,End,J/28.f);Points.Add(FVector2f(Origin+(Center+FVector2D(FMath::Cos(Angle),FMath::Sin(Angle))*Radius)*32.));}
            FSlateDrawElement::MakeLines(Elements,Base+1,Geometry.ToPaintGeometry(),Points,ESlateDrawEffect::None,Color,true,2.f);
        };
        if(Icon.Id==TEXT("health"))Path({{.35,.12},{.65,.12},{.65,.35},{.88,.35},{.88,.65},{.65,.65},{.65,.88},{.35,.88},{.35,.65},{.12,.65},{.12,.35},{.35,.35},{.35,.12}});
        else if(Icon.Id==TEXT("blood")||Icon.Id==TEXT("bleeding"))
        {Path({{.5,.08},{.23,.46},{.17,.65},{.23,.83},{.4,.92},{.6,.92},{.77,.83},{.83,.65},{.77,.46},{.5,.08}});if(Icon.Id==TEXT("bleeding"))Path({{.5,.45},{.5,.69},{.51,.69}});}
        else if(Icon.Id==TEXT("hunger"))
        {Arc({.55,.5},.29,0,2*PI);Path({{.06,.1},{.06,.43},{.23,.43},{.23,.1}});Path({{.145,.12},{.145,.9}});Path({{.94,.1},{.88,.48},{.94,.48},{.94,.9}});}
        else if(Icon.Id==TEXT("thirst"))Path({{.4,.1},{.6,.1},{.6,.25},{.74,.4},{.74,.88},{.26,.88},{.26,.4},{.4,.25},{.4,.1}});
        else if(Icon.Id==TEXT("stamina"))Path({{.57,.08},{.21,.56},{.47,.56},{.37,.94},{.82,.39},{.56,.39},{.57,.08}});
        else if(Icon.Id==TEXT("temperature"))
        {Arc({.5,.74},.17,-.6,3.75);Path({{.4,.59},{.4,.13},{.6,.13},{.6,.59}});Path({{.5,.3},{.5,.76}});Path({{.7,.25},{.87,.25}});Path({{.7,.4},{.82,.4}});}
        else if(Icon.Id==TEXT("fatigue"))
        {Arc({.49,.5},.36,.2,5.05);Path({{.63,.16},{.47,.35},{.5,.57},{.67,.7},{.84,.58}});}
        else if(Icon.Id==TEXT("injury"))
        {Path({{.15,.34},{.34,.15},{.87,.68},{.68,.87},{.15,.34}});Path({{.34,.68},{.68,.34}});Path({{.28,.65},{.65,.28}});}
        else
        {Arc({.5,.5},.23,0,2*PI);for(int32 J=0;J<8;++J){const float A=J*PI/4;Path({{.5+FMath::Cos(A)*.24,.5+FMath::Sin(A)*.24},{.5+FMath::Cos(A)*.42,.5+FMath::Sin(A)*.42}});}}
        const FSlateBrush* White=FCoreStyle::Get().GetBrush(TEXT("WhiteBrush"));
        FSlateDrawElement::MakeBox(Elements,Base+1,Geometry.ToPaintGeometry(FVector2f(28,3),FSlateLayoutTransform(FVector2f(Origin.X+2,Origin.Y+38))),White,ESlateDrawEffect::None,FLinearColor(.15,.15,.15,.7));
        FSlateDrawElement::MakeBox(Elements,Base+2,Geometry.ToPaintGeometry(FVector2f(28*Icon.Fill,3),FSlateLayoutTransform(FVector2f(Origin.X+2,Origin.Y+38))),White,ESlateDrawEffect::None,Color);
    }
    return Base+2;
}
