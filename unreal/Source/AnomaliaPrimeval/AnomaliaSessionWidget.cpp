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
#include "Components/WidgetSwitcher.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "JsonObjectConverter.h"
#include "AnomaliaModResolver.h"
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
    // A narrow navigation rail keeps the actual 3D scene visible at the right.
    auto* Frame=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass()); Frame->SetBrushColor(FLinearColor(.012,.016,.014,.88)); Frame->SetPadding(FMargin(24));
    auto* FrameSlot=Canvas->AddChildToCanvas(Frame); FrameSlot->SetAnchors(FAnchors(.04,.06,.40,.94)); FrameSlot->SetOffsets(FMargin(0));
    auto* Scroll=WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass()); Frame->SetContent(Scroll);
    auto* Rows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass()); Scroll->AddChild(Rows);
    auto Label=[&](const TCHAR* Text) { auto* L=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass()); L->SetText(FText::FromString(Text)); auto Font=L->GetFont(); Font.Size=16; L->SetFont(Font); L->SetAutoWrapText(true); Rows->AddChildToVerticalBox(L)->SetPadding(FMargin(0,6)); return L; };
    auto* Title=Label(TEXT("ANOMALIA")); auto TitleFont=Title->GetFont(); TitleFont.Size=36; Title->SetFont(TitleFont);
    Title->SetColorAndOpacity(FSlateColor(FLinearColor(.90,.87,.76,1)));
    Label(TEXT("PRIMEVAL OUTBOUNDUN"));
    Label(bMainMenu?TEXT("SURVIVRE · EXPLORER · CONSTRUIRE"):TEXT("PARTIE EN PAUSE"));
    auto Button=[&](const TCHAR* Name,const TCHAR* Text) {
        auto* Size=WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass()); Size->SetMinDesiredHeight(44);
        Rows->AddChildToVerticalBox(Size)->SetPadding(FMargin(0,4));
        auto* B=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),FName(Name)); Size->SetContent(B);
        B->SetBackgroundColor(FLinearColor(.08,.10,.085,1));
        auto* L=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass()); L->SetText(FText::FromString(Text));
        auto Font=L->GetFont(); Font.Size=18; L->SetFont(Font); B->SetContent(L); return B;
    };
    PlayButton=Button(TEXT("SessionPlay"),bMainMenu?TEXT("Jouer"):TEXT("Reprendre")); PlayButton->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::Play);
    HomeButton=Button(TEXT("SessionHome"),TEXT("Survivant")); HomeButton->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::ShowHome);
    OptionsButton=Button(TEXT("SessionOptions"),TEXT("Options")); OptionsButton->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::ShowOptions);
    ModsButton=Button(TEXT("SessionMods"),TEXT("Mods")); ModsButton->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::ShowMods);
    Button(TEXT("SessionSaveQuit"),TEXT("Sauvegarder et quitter"))->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::SaveAndQuit);
    Button(TEXT("SessionQuit"),TEXT("Quitter sans nouvelle sauvegarde"))->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::Quit);
    Feedback=Label(TEXT("Sauvegarde automatique toutes les 2 minutes."));

    auto* Details=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass()); Details->SetPadding(FMargin(24));
    Details->SetBrushColor(FLinearColor(.012,.016,.014,.80));
    auto* DetailsSlot=Canvas->AddChildToCanvas(Details); DetailsSlot->SetAnchors(FAnchors(.44,.48,.96,.94)); DetailsSlot->SetOffsets(FMargin(0));
    auto* PageScroll=WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass()); Details->SetContent(PageScroll);
    Pages=WidgetTree->ConstructWidget<UWidgetSwitcher>(UWidgetSwitcher::StaticClass(),TEXT("SessionPages")); PageScroll->AddChild(Pages);
    Rows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass()); Pages->AddChild(Rows);
    Label(TEXT("VOTRE SURVIVANT"));
    Label(TEXT("Jouer reprend votre personnage et votre inventaire dans la zone jouable.\nLes sauvegardes existantes sont conservées."));
    Label(TEXT("COMMANDES\nZ/W : avancer · Q/A/D : direction · souris : regard\nMaj : courir · E : interagir/entrer/sortir · I : inventaire\nEspace : sauter · R : dormir près du lit · V : caméra\nÉchap : pause · manette : sticks, A/Croix, X/Carré\nMenu : inventaire · View/Share : pause"));
    Label(TEXT("Version de développement · carte et contenu en construction"));
    Rows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass()); Pages->AddChild(Rows);
    Label(TEXT("OPTIONS DE LA PARTIE"));
    auto* Q=Button(TEXT("SessionQuality"),TEXT("Qualité : choisir un préréglage")); QualityLabel=Cast<UTextBlock>(Q->GetContent()); Q->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::ChangeQuality);
    Button(TEXT("SessionSave"),TEXT("Sauvegarder"))->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::Save);
    auto* Substances=Button(TEXT("SessionRPSubstances"),TEXT("Substances RP"));
    auto* Tobacco=Button(TEXT("SessionTobacco"),TEXT("Tabac"));
    auto* Alcohol=Button(TEXT("SessionAlcohol"),TEXT("Alcool"));
    ItemPolicyLabels={Cast<UTextBlock>(Substances->GetContent()),Cast<UTextBlock>(Tobacco->GetContent()),Cast<UTextBlock>(Alcohol->GetContent())};
    Substances->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::ToggleSubstances);
    Tobacco->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::ToggleTobacco);
    Alcohol->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::ToggleAlcohol);
    RefreshItemPolicyLabels();
    Rows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass()); Pages->AddChild(Rows);
    Label(TEXT("MODS LOCAUX"));
    Label(TEXT("Consultez les manifestes locaux et ouvrez leur dossier.\nLe téléchargement et l’activation de paquets tiers ne sont pas encore disponibles. Les mods DayZ ne sont pas compatibles avec Unreal Engine."));
    Button(TEXT("SessionRefreshMods"),TEXT("Actualiser la liste"))->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::RefreshMods);
    Button(TEXT("SessionOpenModsFolder"),TEXT("Ouvrir le dossier Mods"))->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::OpenModsFolder);
    ModRows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("SessionModRows")); Rows->AddChildToVerticalBox(ModRows);
    SelectPage(0);
}
void UAnomaliaSessionWidget::SelectPage(int32 Index)
{
    if(!Pages || Index<0 || Index>=Pages->GetChildrenCount()) return;
    Pages->SetActiveWidgetIndex(Index);
    UButton* Navigation[]={HomeButton.Get(),OptionsButton.Get(),ModsButton.Get()};
    for(int32 I=0;I<3;++I) if(Navigation[I]) Navigation[I]->SetBackgroundColor(I==Index?FLinearColor(.35,.32,.21,1):FLinearColor(.08,.10,.085,1));
}
void UAnomaliaSessionWidget::ShowHome() { SelectPage(0); }
void UAnomaliaSessionWidget::ShowOptions() { SelectPage(1); }
void UAnomaliaSessionWidget::ShowMods() { RefreshMods(); SelectPage(2); }
void UAnomaliaSessionWidget::RefreshMods()
{
    if(!ModRows) return;
    ModRows->ClearChildren();
    const FString Root=FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("Mods")));
    auto AddRow=[&](const FString& Text) {
        auto* Row=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass()); Row->SetText(FText::FromString(Text)); Row->SetAutoWrapText(true);
        ModRows->AddChildToVerticalBox(Row)->SetPadding(FMargin(0,8));
    };
    AddRow(Root);
    TArray<FString> Folders; IFileManager::Get().FindFiles(Folders,*(Root/TEXT("*")),false,true); Folders.Sort();
    int32 Count=0;
    for(const FString& Folder:Folders)
    {
        const FString File=FPaths::Combine(Root,Folder,TEXT("manifest.json"));
        if(!IFileManager::Get().FileExists(*File)) continue;
        if(++Count>200) { AddRow(TEXT("Liste limitée à 200 manifestes.")); break; }
        FString Json,Error; FAnomaliaModManifest Manifest;
        const int64 Bytes=IFileManager::Get().FileSize(*File);
        if(Bytes<0 || Bytes>256*1024 || !FFileHelper::LoadFileToString(Json,*File) ||
           !FJsonObjectConverter::JsonObjectStringToUStruct(Json,&Manifest,0,0))
        { AddRow(Folder+TEXT(" — manifeste illisible")); continue; }
        if(!UAnomaliaModResolver::ValidateModManifest(Manifest,Error))
        { AddRow(Folder+TEXT(" — déclaration rejetée : ")+Error); continue; }
        // Manifest validation does not authenticate a package or mount it into the game.
        AddRow(Manifest.Id+TEXT(" · ")+Manifest.Version+TEXT("\nManifeste reconnu · paquet non vérifié · inactif"));
    }
    if(Count==0) AddRow(TEXT("Aucun manifeste local. Aucun mod tiers activé."));
}
void UAnomaliaSessionWidget::OpenModsFolder()
{
    const FString Root=FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("Mods")));
    if(IFileManager::Get().MakeDirectory(*Root,true)) FPlatformProcess::ExploreFolder(*Root);
    else if(Feedback) Feedback->SetText(FText::FromString(TEXT("Impossible d’ouvrir le dossier Mods.")));
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
void UAnomaliaSessionWidget::ToggleSubstances() { ToggleItemPolicy(0); }
void UAnomaliaSessionWidget::ToggleTobacco() { ToggleItemPolicy(1); }
void UAnomaliaSessionWidget::ToggleAlcohol() { ToggleItemPolicy(2); }
void UAnomaliaSessionWidget::RefreshItemPolicyLabels()
{
    const auto* Mode=GetWorld()?GetWorld()->GetAuthGameMode<AAnomaliaGameMode>():nullptr;
    if(!Mode || ItemPolicyLabels.Num()!=3) return;
    const bool Enabled[]={Mode->ActiveServerSettings.bAllowRPSubstances,Mode->ActiveServerSettings.bAllowTobacco,Mode->ActiveServerSettings.bAllowAlcohol};
    const TCHAR* Names[]={TEXT("Substances RP"),TEXT("Tabac"),TEXT("Alcool")};
    for(int32 Index=0;Index<3;++Index) if(ItemPolicyLabels[Index])
        ItemPolicyLabels[Index]->SetText(FText::FromString(FString(Names[Index])+(Enabled[Index]?TEXT(" : autorisé"):TEXT(" : interdit"))));
}
void UAnomaliaSessionWidget::ToggleItemPolicy(int32 Index)
{
    auto* Mode=GetWorld()?GetWorld()->GetAuthGameMode<AAnomaliaGameMode>():nullptr;
    if(!Mode || GetWorld()->GetNetMode()!=NM_Standalone || Index<0 || Index>2) return;
    auto Candidate=Mode->ActiveServerSettings;
    bool* Flags[]={&Candidate.bAllowRPSubstances,&Candidate.bAllowTobacco,&Candidate.bAllowAlcohol};
    *Flags[Index]=!*Flags[Index];FString Error;
    const bool Saved=UAnomaliaConfigLibrary::SaveServerSettings(Mode->ServerId,Candidate,Error);
    if(Saved) Mode->ActiveServerSettings=Candidate;
    RefreshItemPolicyLabels();
    if(Feedback) Feedback->SetText(FText::FromString(Saved?TEXT("Règle appliquée et enregistrée pour cette partie."):Error));
}
FReply UAnomaliaSessionWidget::NativeOnKeyDown(const FGeometry& Geometry,const FKeyEvent& Event)
{
    if(Event.GetKey()==EKeys::Escape || Event.GetKey()==EKeys::Gamepad_FaceButton_Right)
    {
        if(Pages && Pages->GetActiveWidgetIndex()!=0)
        { ShowHome(); if(HomeButton) HomeButton->SetUserFocus(GetOwningPlayer()); }
        else Play();
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(Geometry,Event);
}
