#include "AnomaliaSessionWidget.h"
#include "AnomaliaGameMode.h"
#include "AnomaliaSurvivor.h"
#include "Blueprint/WidgetTree.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Components/SafeZone.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Border.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Components/SizeBox.h"
#include "Components/ScrollBox.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "AnomaliaPerformanceLibrary.h"

UAnomaliaSessionWidget* UAnomaliaSessionWidget::Open(APlayerController* PC,bool MainMenu)
{
    if(!PC || !PC->IsLocalController() || PC->GetNetMode()!=NM_Standalone) return nullptr;
    TArray<UUserWidget*> Existing; UWidgetBlueprintLibrary::GetAllWidgetsOfClass(PC,Existing,StaticClass(),false);
    for(auto* Widget:Existing) if(Widget && Widget->IsInViewport()) return Cast<UAnomaliaSessionWidget>(Widget);
    if(auto* S=Cast<AAnomaliaSurvivor>(PC->GetPawn())) S->CloseInventory();
    auto* Menu=CreateWidget<UAnomaliaSessionWidget>(PC,StaticClass()); if(!Menu) return nullptr;
    Menu->bMainMenu=MainMenu; Menu->AddToViewport(100);
    UGameplayStatics::SetGamePaused(PC,true);
    FInputModeUIOnly Mode; Mode.SetWidgetToFocus(Menu->TakeWidget()); Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    PC->SetInputMode(Mode); PC->bShowMouseCursor=true;
    if(Menu->PlayButton) Menu->PlayButton->SetUserFocus(PC);
    return Menu;
}
TSharedRef<SWidget> UAnomaliaSessionWidget::RebuildWidget()
{
    if(!WidgetTree) WidgetTree=NewObject<UWidgetTree>(this,TEXT("WidgetTree"));
    BuildLayout();
    return Super::RebuildWidget();
}

void UAnomaliaSessionWidget::NativeConstruct()
{
    Super::NativeConstruct(); SetIsFocusable(true);
}
void UAnomaliaSessionWidget::BuildLayout()
{
    if(!WidgetTree || WidgetTree->RootWidget) return;
    auto* Safe=WidgetTree->ConstructWidget<USafeZone>(USafeZone::StaticClass()); WidgetTree->RootWidget=Safe;
    auto* Canvas=WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass()); Safe->SetContent(Canvas);
    auto* Frame=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass()); Frame->SetBrushColor(FLinearColor(.015,.025,.035,.94)); Frame->SetPadding(FMargin(24));
    auto* FrameSlot=Canvas->AddChildToCanvas(Frame); FrameSlot->SetAnchors(FAnchors(.05,.08,.55,.92)); FrameSlot->SetOffsets(FMargin(0));
    auto* Scroll=WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass()); Frame->SetContent(Scroll);
    auto* Rows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass()); Scroll->AddChild(Rows);
    auto Label=[&](const TCHAR* Text) { auto* L=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass()); L->SetText(FText::FromString(Text)); auto Font=L->GetFont(); Font.Size=16; L->SetFont(Font); L->SetAutoWrapText(true); Rows->AddChildToVerticalBox(L)->SetPadding(FMargin(0,6)); return L; };
    Label(TEXT("ANOMALIA\nPRIMEVAL OUTBOUNDUN"));
    Label(TEXT("VERSION DE TEST WINDOWS · zone initiale\nGraphismes et conduite encore provisoires"));
    auto Button=[&](const TCHAR* Name,const TCHAR* Text) {
        auto* Size=WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass()); Size->SetMinDesiredHeight(44);
        Rows->AddChildToVerticalBox(Size)->SetPadding(FMargin(0,4));
        auto* B=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),FName(Name)); Size->SetContent(B);
        auto* L=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass()); L->SetText(FText::FromString(Text)); B->SetContent(L); return B;
    };
    PlayButton=Button(TEXT("SessionPlay"),bMainMenu?TEXT("Jouer"):TEXT("Reprendre")); PlayButton->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::Play);
    auto* Q=Button(TEXT("SessionQuality"),TEXT("Qualité : choisir un préréglage")); QualityLabel=Cast<UTextBlock>(Q->GetContent()); Q->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::ChangeQuality);
    Button(TEXT("SessionSave"),TEXT("Sauvegarder"))->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::Save);
    Button(TEXT("SessionSaveQuit"),TEXT("Sauvegarder et quitter"))->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::SaveAndQuit);
    Button(TEXT("SessionQuit"),TEXT("Quitter sans nouvelle sauvegarde"))->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::Quit);
    Label(TEXT("COMMANDES\nZ/W : avancer · Q/A/D : direction · souris : regard\nMaj : courir · E : interagir/entrer/sortir · I : inventaire\nEspace : sauter · R : dormir près du lit · V : caméra\nÉchap : pause · manette : sticks, A/Croix, X/Carré\nMenu : inventaire · View/Share : pause"));
    Feedback=Label(TEXT("Sauvegarde automatique toutes les 2 minutes.\nAucune partie existante n’est effacée."));
}
void UAnomaliaSessionWidget::Play()
{
    auto* PC=GetOwningPlayer(); if(!PC) return;
    RemoveFromParent(); UGameplayStatics::SetGamePaused(PC,false); PC->SetInputMode(FInputModeGameOnly()); PC->bShowMouseCursor=false;
}
void UAnomaliaSessionWidget::ChangeQuality()
{
    Quality=(Quality+1)%3;
    const TArray<FString> Profiles={TEXT("Performance_Fallback"),TEXT("PC_Medium"),TEXT("PC_High")};
    const TCHAR* Names[]={TEXT("faible"),TEXT("moyenne"),TEXT("élevée")};
    const bool OK=UAnomaliaPerformanceLibrary::ApplyGraphicsPreset(Profiles[Quality]);
    if(QualityLabel) QualityLabel->SetText(FText::FromString(FString(TEXT("Qualité : "))+Names[Quality]+TEXT(" (changer)")));
    if(Feedback) Feedback->SetText(FText::FromString(OK?TEXT("Réglages graphiques locaux appliqués."):TEXT("Impossible d’appliquer ces réglages.")));
}
void UAnomaliaSessionWidget::Save()
{
    auto* Mode=GetWorld()?GetWorld()->GetAuthGameMode<AAnomaliaGameMode>():nullptr;
    const bool OK=Mode && Mode->SaveLocalGame();
    if(Feedback) Feedback->SetText(FText::FromString(OK?TEXT("Personnage et inventaire sauvegardés."):TEXT("Sauvegarde non confirmée : opération en cours ou erreur de stockage.")));
}
void UAnomaliaSessionWidget::SaveAndQuit()
{
    auto* Mode=GetWorld()?GetWorld()->GetAuthGameMode<AAnomaliaGameMode>():nullptr;
    if(Mode && Mode->SaveLocalGame()) Quit();
    else if(Feedback) Feedback->SetText(FText::FromString(TEXT("Sauvegarde non confirmée. La partie reste ouverte.")));
}
void UAnomaliaSessionWidget::Quit() { UKismetSystemLibrary::QuitGame(this,GetOwningPlayer(),EQuitPreference::Quit,false); }
FReply UAnomaliaSessionWidget::NativeOnKeyDown(const FGeometry& Geometry,const FKeyEvent& Event)
{
    if(Event.GetKey()==EKeys::Escape || Event.GetKey()==EKeys::Gamepad_FaceButton_Right) { Play(); return FReply::Handled(); }
    return Super::NativeOnKeyDown(Geometry,Event);
}
