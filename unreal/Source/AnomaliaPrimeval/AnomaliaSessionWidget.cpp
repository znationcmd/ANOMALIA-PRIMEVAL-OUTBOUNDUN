#include "AnomaliaSessionWidget.h"
#include "AnomaliaGameMode.h"
#include "AnomaliaSurvivor.h"
#include "AnomaliaStatusWidget.h"
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
#include "Components/Image.h"
#include "Components/ScaleBox.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/ComboBoxString.h"
#include "Components/EditableTextBox.h"
#include "Components/Spacer.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Styling/SlateTypes.h"

#include "Engine/Texture2D.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "JsonObjectConverter.h"
#include "AnomaliaModResolver.h"
#include "HAL/PlatformMisc.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonReader.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
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
    if(MainMenu) if(auto* S=Cast<AAnomaliaSurvivor>(PC->GetPawn())) if(S->StatusWidget)
    {
        Menu->HiddenStatusWidget=S->StatusWidget;Menu->PreviousStatusVisibility=S->StatusWidget->GetVisibility();
        S->StatusWidget->SetVisibility(ESlateVisibility::Hidden);
    }
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
    bStartupIntro=bMainMenu && MenuArtwork;
    if(bStartupIntro)
    {
        IntroStarted=FPlatformTime::Seconds(); MenuArtwork->SetRenderOpacity(0.f);
        if(NavigationFrame) NavigationFrame->SetVisibility(ESlateVisibility::Hidden);
    }
    auto* PC=GetOwningPlayer();
    if(bMainMenu && !MenuArtwork && PC && GetWorld() && GetWorld()->GetMapName().EndsWith(TEXT("ANOMALIA_Playable_v1")))
    {
        for(TActorIterator<AActor> It(GetWorld());It;++It)
        {
            if(!It->ActorHasTag(TEXT("ANOMALIA_ProgressArt_v1"))) continue;
            const auto* Mesh=It->FindComponentByClass<UStaticMeshComponent>();
            if(!Mesh || !Mesh->GetStaticMesh() || !Mesh->GetStaticMesh()->GetPathName().Contains(TEXT("/country_house_scan/"))) continue;
            FVector Center,Extent; It->GetActorBounds(false,Center,Extent);
            const double Distance=FMath::Max(1800.,Extent.Size2D()*1.6);
            const FVector Eye=Center+FVector(Distance,-Distance,FMath::Max(180.,Extent.Z*.4));
            FActorSpawnParameters Params; Params.ObjectFlags|=RF_Transient;
            MenuCamera=GetWorld()->SpawnActor<ACameraActor>(ACameraActor::StaticClass(),Eye,(Center-Eye).Rotation(),Params);
            if(MenuCamera)
            {
                MenuCamera->GetCameraComponent()->SetFieldOfView(60.f);
                PreviousViewTarget=PC->GetViewTarget(); PC->SetViewTarget(MenuCamera);
                if(PC->PlayerCameraManager) PC->PlayerCameraManager->UpdateCamera(0.f);
            }
            break;
        }
    }
}
void UAnomaliaSessionWidget::NativeDestruct()
{
    if(HiddenStatusWidget) { HiddenStatusWidget->SetVisibility(PreviousStatusVisibility);HiddenStatusWidget=nullptr; }
    if(MenuCamera)
    {
        if(auto* PC=GetOwningPlayer()) if(PreviousViewTarget.IsValid()) PC->SetViewTarget(PreviousViewTarget.Get());
        MenuCamera->Destroy(); MenuCamera=nullptr; PreviousViewTarget.Reset();
    }
    Super::NativeDestruct();
}
void UAnomaliaSessionWidget::NativeTick(const FGeometry& Geometry,float DeltaTime)
{
    Super::NativeTick(Geometry,DeltaTime);
    if(!bStartupIntro || !MenuArtwork) return;
    const float Elapsed=static_cast<float>(FPlatformTime::Seconds()-IntroStarted);
    const float Progress=FMath::Clamp(Elapsed/4.5f,0.f,1.f);
    MenuArtwork->SetRenderOpacity(FMath::Clamp(Elapsed/1.2f,0.f,1.f));
    MenuArtwork->SetRenderScale(FVector2D(.97f+.03f*Progress));
    if(Elapsed>=4.5f) FinishIntro();
}
void UAnomaliaSessionWidget::FinishIntro()
{
    bStartupIntro=false;
    if(MenuArtwork) { MenuArtwork->SetRenderOpacity(1.f);MenuArtwork->SetRenderScale(FVector2D(1.f,1.f)); }
    if(NavigationFrame) NavigationFrame->SetVisibility(ESlateVisibility::Visible);
}
FReply UAnomaliaSessionWidget::NativeOnMouseButtonDown(const FGeometry& Geometry,const FPointerEvent& Event)
{
    if(bStartupIntro) { FinishIntro();return FReply::Handled(); }
    return Super::NativeOnMouseButtonDown(Geometry,Event);
}
void UAnomaliaSessionWidget::BuildLayout()
{
    if(!WidgetTree || WidgetTree->RootWidget) return;
    auto* Safe=WidgetTree->ConstructWidget<USafeZone>(USafeZone::StaticClass()); WidgetTree->RootWidget=Safe;
    auto* Canvas=WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass()); Safe->SetContent(Canvas);
    if(bMainMenu)
    {
        auto* Texture=LoadObject<UTexture2D>(nullptr,TEXT("/Game/Anomalia/Branding/T_MenuBackdrop.T_MenuBackdrop"),nullptr,LOAD_NoWarn);
        if(Texture)
        {
            auto* Matte=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());Matte->SetBrushColor(FLinearColor::Black);Matte->SetPadding(FMargin(0));
            auto* BackdropCanvasSlot=Canvas->AddChildToCanvas(Matte);BackdropCanvasSlot->SetAnchors(FAnchors(0,0,1,1));BackdropCanvasSlot->SetOffsets(FMargin(0));
            auto* Fit=WidgetTree->ConstructWidget<UScaleBox>(UScaleBox::StaticClass());Fit->SetStretch(EStretch::ScaleToFit);Matte->SetContent(Fit);
            MenuArtwork=WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(),TEXT("SessionMenuArtwork"));
            MenuArtwork->SetBrushFromTexture(Texture,true);MenuArtwork->SetRenderTransformPivot(FVector2D(.5f,.5f));Fit->SetContent(MenuArtwork);
        }
    }
    // A narrow navigation rail keeps the actual 3D scene visible at the right.
    auto* Frame=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(),TEXT("SessionNavigation"));NavigationFrame=Frame; Frame->SetBrushColor(FLinearColor(.012f,.016f,.014f,.82f)); Frame->SetPadding(FMargin(20));
    auto* FrameSlot=Canvas->AddChildToCanvas(Frame); FrameSlot->SetAnchors(FAnchors(.035f,.12f,.31f,.77f)); FrameSlot->SetOffsets(FMargin(0));
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
    Button(TEXT("SessionWorldEditor"),TEXT("Éditeur de carte UE5"))->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::OpenWorldEditor);
    Button(TEXT("SessionSaveQuit"),TEXT("Sauvegarder et quitter"))->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::SaveAndQuit);
    Button(TEXT("SessionQuit"),TEXT("Quitter sans nouvelle sauvegarde"))->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::Quit);
    Feedback=Label(TEXT("Sauvegarde automatique toutes les 2 minutes."));

    auto* Details=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(),TEXT("SessionDetailsFrame"));DetailsFrame=Details; Details->SetPadding(FMargin(24));
    Details->SetBrushColor(FLinearColor(.012,.016,.014,.80));
    auto* DetailsSlot=Canvas->AddChildToCanvas(Details); DetailsSlot->SetAnchors(FAnchors(.44,.48,.96,.94)); DetailsSlot->SetOffsets(FMargin(0));
    auto* DetailRows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());Details->SetContent(DetailRows);Rows=DetailRows;
    Button(TEXT("SessionClosePage"),TEXT("Retour au menu"))->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::ClosePage);
    auto* PageScroll=WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass());DetailRows->AddChildToVerticalBox(PageScroll);
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
    // Dedicated full-screen native UMG Workshop, NOT the web/Electron demo.
    // The standard local-mods page is retained internally for compatibility.
    WorkshopFrame=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(),TEXT("WorkshopFullScreen"));
    WorkshopFrame->SetBrushColor(FLinearColor(.023f,.018f,.031f,.98f));
    WorkshopFrame->SetPadding(FMargin(18));
    auto* WS=Canvas->AddChildToCanvas(WorkshopFrame);
    WS->SetAnchors(FAnchors(.025f,.035f,.975f,.965f));
    WS->SetOffsets(FMargin(0));
    auto* Layout=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    WorkshopFrame->SetContent(Layout);
    auto WSText=[&](UVerticalBox* Parent,const FString& Value,int32 Size,const FLinearColor& Color)
    {
        auto* Text=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        Text->SetText(FText::FromString(Value));Text->SetAutoWrapText(true);
        auto Font=Text->GetFont();Font.Size=Size;Text->SetFont(Font);
        Text->SetColorAndOpacity(FSlateColor(Color));
        Parent->AddChildToVerticalBox(Text)->SetPadding(FMargin(4,5));
        return Text;
    };
    auto WSButton=[&](UHorizontalBox* Parent,const TCHAR* Id,const FString& Value)
    {
        auto* Btn=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),FName(Id));
        Btn->SetBackgroundColor(FLinearColor(.46f,.11f,.075f,1.f));
        auto* Txt=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        Txt->SetText(FText::FromString(Value));Txt->SetColorAndOpacity(FSlateColor(FLinearColor(.99f,.84f,.76f)));
        auto Font=Txt->GetFont();Font.Size=14;Txt->SetFont(Font);Btn->SetContent(Txt);
        Parent->AddChildToHorizontalBox(Btn)->SetPadding(FMargin(4,4));
        return Btn;
    };
    // Red metallic navigation strip and an always-functional in-game back button.
    auto* Top=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
    Top->SetBrushColor(FLinearColor(.13f,.046f,.06f,1.f));
    Top->SetPadding(FMargin(16,9));
    Layout->AddChildToVerticalBox(Top)->SetPadding(FMargin(0,0,0,10));
    auto* TopRow=WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());Top->SetContent(TopRow);
    auto* TopTitle=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    TopTitle->SetText(FText::FromString(TEXT("✦  ANOMALIA    WORKSHOP")));
    auto TF=TopTitle->GetFont();TF.Size=26;TopTitle->SetFont(TF);
    TopTitle->SetColorAndOpacity(FSlateColor(FLinearColor(.99f,.77f,.62f)));
    auto* TitleSlot=TopRow->AddChildToHorizontalBox(TopTitle);
    TitleSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    WSButton(TopRow,TEXT("WorkshopReturn"),TEXT("← Retour au jeu"))->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::CloseWorkshop);

    auto* Hero=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
    Hero->SetBrushColor(FLinearColor(.085f,.04f,.058f,.98f));Hero->SetPadding(FMargin(18,11));
    Layout->AddChildToVerticalBox(Hero)->SetPadding(FMargin(0,0,0,12));
    auto* HeroLayout=WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());Hero->SetContent(HeroLayout);
    auto* HeroLeft=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    HeroLayout->AddChildToHorizontalBox(HeroLeft)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    WSText(HeroLeft,TEXT("SURVIVRE  ·  CRÉER  ·  PARTAGER"),13,FLinearColor(.99f,.57f,.43f));
    WSText(HeroLeft,TEXT("ANOMALIA WORKSHOP"),32,FLinearColor(1.f,.82f,.67f));
    WSText(HeroLeft,TEXT("Découvrez vos créations, véhicules, bâtiments et objets depuis le jeu."),15,FLinearColor(.86f,.70f,.65f));
    WSText(HeroLeft,TEXT("Catalogue local réel · extensions Unreal compatibles uniquement"),11,FLinearColor(.97f,.55f,.43f));
    if(auto* Art=LoadObject<UTexture2D>(nullptr,TEXT("/Game/Anomalia/Branding/T_MenuBackdrop.T_MenuBackdrop"),nullptr,LOAD_NoWarn))
    {
        auto* Image=WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
        Image->SetBrushFromTexture(Art,true);
        Image->SetColorAndOpacity(FLinearColor(1.f,.55f,.48f,.85f));
        HeroLayout->AddChildToHorizontalBox(Image)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    }

    auto* Actions=WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
    Layout->AddChildToVerticalBox(Actions)->SetPadding(FMargin(0,0,0,12));
    WSButton(Actions,TEXT("WorkshopOpenTools"),TEXT("ANOMALIA Tools ↗"))->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::OpenWorkshopTools);
    WSButton(Actions,TEXT("WorkshopOpenHosting"),TEXT("CMD Hosting ↗"))->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::OpenWorkshopHosting);
    WSButton(Actions,TEXT("WorkshopRefresh"),TEXT("↻ Actualiser les mods"))->OnClicked.AddDynamic(this,&UAnomaliaSessionWidget::RefreshWorkshop);
    auto* Filters=WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
    Layout->AddChildToVerticalBox(Filters)->SetPadding(FMargin(0,0,0,8));
    WorkshopSearch=WidgetTree->ConstructWidget<UEditableTextBox>(UEditableTextBox::StaticClass(),TEXT("WorkshopSearch"));
    WorkshopSearch->SetHintText(FText::FromString(TEXT("Rechercher un mod dans le Workshop...")));
    Filters->AddChildToHorizontalBox(WorkshopSearch)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    WorkshopCategory=WidgetTree->ConstructWidget<UComboBoxString>(UComboBoxString::StaticClass(),TEXT("WorkshopCategory"));
    for(const TCHAR* Category:{TEXT("Tous"),TEXT("Véhicules"),TEXT("Armes"),TEXT("Bâtiments"),TEXT("Créatures"),TEXT("Survie"),TEXT("Cartes"),TEXT("Vêtements"),TEXT("Outils"),TEXT("Autres")})
        WorkshopCategory->AddOption(Category);
    WorkshopCategory->SetSelectedOption(TEXT("Tous"));
    Filters->AddChildToHorizontalBox(WorkshopCategory)->SetPadding(FMargin(12,0,0,0));
    WorkshopSearch->OnTextChanged.AddDynamic(this,&UAnomaliaSessionWidget::WorkshopSearchChanged);
    WorkshopCategory->OnSelectionChanged.AddDynamic(this,&UAnomaliaSessionWidget::WorkshopCategoryChanged);
    WorkshopStatus=WSText(Layout,TEXT("Recherche de mods locaux..."),12,FLinearColor(.96f,.65f,.48f));
    auto* Listing=WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(),TEXT("WorkshopListScroll"));
    Layout->AddChildToVerticalBox(Listing)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    WorkshopCards=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("WorkshopCards"));
    Listing->AddChild(WorkshopCards);
    auto* Footer=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
    Footer->SetBrushColor(FLinearColor(.14f,.052f,.055f,1.f));Footer->SetPadding(FMargin(9,5));
    Layout->AddChildToVerticalBox(Footer);
    auto* Disclaimer=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Disclaimer->SetAutoWrapText(true);
    Disclaimer->SetText(FText::FromString(TEXT("Atelier ANOMALIA : les manifestes et créations réels sont visibles. Installation, téléchargement et chargement UE5 automatiques : pas encore connectés.")));
    Disclaimer->SetColorAndOpacity(FSlateColor(FLinearColor(.94f,.66f,.57f)));
    Footer->SetContent(Disclaimer);
    WorkshopFrame->SetVisibility(ESlateVisibility::Collapsed);
    SelectPage(0);
    ClosePage();
}
void UAnomaliaSessionWidget::SelectPage(int32 Index)
{
    if(!Pages || Index<0 || Index>=Pages->GetChildrenCount()) return;
    Pages->SetActiveWidgetIndex(Index);
    if(WorkshopFrame) WorkshopFrame->SetVisibility(ESlateVisibility::Collapsed);
    FinishIntro();if(DetailsFrame)DetailsFrame->SetVisibility(ESlateVisibility::Visible);
    UButton* PageButtons[]={HomeButton.Get(),OptionsButton.Get(),ModsButton.Get()};
    for(int32 I=0;I<3;++I) if(PageButtons[I]) PageButtons[I]->SetBackgroundColor(I==Index?FLinearColor(.35f,.32f,.21f,1.f):FLinearColor(.08f,.10f,.085f,1.f));
}
void UAnomaliaSessionWidget::ClosePage() { if(DetailsFrame)DetailsFrame->SetVisibility(ESlateVisibility::Collapsed); }
void UAnomaliaSessionWidget::ShowHome() { SelectPage(0); }
void UAnomaliaSessionWidget::ShowOptions() { SelectPage(1); }
void UAnomaliaSessionWidget::ShowMods()
{
    // Preserve the original page index for gamepad/menu navigation and tests.
    RefreshMods(); SelectPage(2);
    if(DetailsFrame) DetailsFrame->SetVisibility(ESlateVisibility::Collapsed);
    if(WorkshopFrame) WorkshopFrame->SetVisibility(ESlateVisibility::Visible);
    RefreshWorkshop();
}
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
void UAnomaliaSessionWidget::CloseWorkshop()
{
    if(WorkshopFrame) WorkshopFrame->SetVisibility(ESlateVisibility::Collapsed);
    if(DetailsFrame) DetailsFrame->SetVisibility(ESlateVisibility::Collapsed);
    if(ModsButton) ModsButton->SetUserFocus(GetOwningPlayer());
}
void UAnomaliaSessionWidget::WorkshopSearchChanged(const FText&)
{
    if(WorkshopFrame && WorkshopFrame->GetVisibility()==ESlateVisibility::Visible) RefreshWorkshop();
}
void UAnomaliaSessionWidget::WorkshopCategoryChanged(FString,ESelectInfo::Type)
{
    if(WorkshopFrame && WorkshopFrame->GetVisibility()==ESlateVisibility::Visible) RefreshWorkshop();
}
void UAnomaliaSessionWidget::OpenWorkshopTools()
{
#if PLATFORM_WINDOWS
    // Secondary action only. The actual Workshop UI runs inside UE5.
    FPlatformProcess::LaunchURL(TEXT("anomalia-tools://workshop"),nullptr,nullptr);
    if(WorkshopStatus) WorkshopStatus->SetText(FText::FromString(TEXT("Ouverture d’ANOMALIA Tools demandée (si installé sur Windows).")));
#else
    if(WorkshopStatus) WorkshopStatus->SetText(FText::FromString(TEXT("ANOMALIA Tools est disponible pour Windows.")));
#endif
}
void UAnomaliaSessionWidget::OpenWorkshopHosting()
{
    FPlatformProcess::LaunchURL(TEXT("https://cmd-hosting-web-production.up.railway.app/#cmdMods"),nullptr,nullptr);
    if(WorkshopStatus) WorkshopStatus->SetText(FText::FromString(TEXT("Page CMD Hosting ouverte dans votre navigateur. Installation serveur non disponible.")));
}
void UAnomaliaSessionWidget::RefreshWorkshop()
{
    if(!WorkshopCards || !WorkshopStatus || !WidgetTree) return;
    WorkshopCards->ClearChildren();
    const FString Search=WorkshopSearch?WorkshopSearch->GetText().ToString().TrimStartAndEnd():TEXT("");
    const FString Filter=WorkshopCategory?WorkshopCategory->GetSelectedOption():TEXT("Tous");
    int32 Total=0,Visible=0;
    auto Row=[&](const FString& Title,const FString& Details,bool Accent)
    {
        auto* Card=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
        Card->SetBrushColor(Accent?FLinearColor(.24f,.075f,.065f,.98f):FLinearColor(.075f,.067f,.092f,.98f));
        Card->SetPadding(FMargin(14,11));
        WorkshopCards->AddChildToVerticalBox(Card)->SetPadding(FMargin(3,4));
        auto* Contents=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
        Card->SetContent(Contents);
        for(const TPair<FString,int32>& Line:{TPair<FString,int32>(Title,18),TPair<FString,int32>(Details,12)})
        {
            auto* Text=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
            Text->SetText(FText::FromString(Line.Key));Text->SetAutoWrapText(true);
            auto Font=Text->GetFont();Font.Size=Line.Value;Text->SetFont(Font);
            Text->SetColorAndOpacity(FSlateColor(Line.Value==18?FLinearColor(1.f,.84f,.72f):FLinearColor(.8f,.67f,.65f)));
            Contents->AddChildToVerticalBox(Text)->SetPadding(FMargin(0,3));
        }
    };
    auto Matches=[&](const FString& Category,const FString& Name,const FString& Description)
    {
        return (Filter.IsEmpty() || Filter==TEXT("Tous") || Filter.Equals(Category,ESearchCase::IgnoreCase)) &&
            (Search.IsEmpty() || Name.Contains(Search,ESearchCase::IgnoreCase) || Category.Contains(Search,ESearchCase::IgnoreCase) ||
                Description.Contains(Search,ESearchCase::IgnoreCase));
    };
    // ANOMALIA Tools stores its real projects in Electron userData/private-workspaces.
    // Never parse raw C++ mods or execute anything while displaying this catalogue.
#if PLATFORM_WINDOWS
    const FString AppData=FPlatformMisc::GetEnvironmentVariable(TEXT("APPDATA"));
    const TArray<FString> Workspaces={
        FPaths::Combine(AppData,TEXT("ANOMALIA Tools"),TEXT("private-workspaces")),
        FPaths::Combine(AppData,TEXT("anomalia-tools"),TEXT("private-workspaces"))
    };
    for(const FString& Workspace:Workspaces)
    {
        if(AppData.IsEmpty() || !IFileManager::Get().DirectoryExists(*Workspace)) continue;
        TArray<FString> Folders;IFileManager::Get().FindFiles(Folders,*(Workspace/TEXT("*")),false,true);
        Folders.Sort();int32 Scanned=0;
        for(const FString& Folder:Folders)
        {
            if(++Scanned>500 || Total>=200) break;
            // ANOMALIA Tools project IDs are user slugs plus UUID suffix, not fixed prefixes.
            if(Folder.Len()<2 || Folder.Len()>100 || Folder==TEXT("_workshop")) continue;
            bool ValidFolder=true;
            for(const TCHAR C:Folder) if(!((C>=TEXT('a') && C<=TEXT('z')) ||
                (C>=TEXT('0') && C<=TEXT('9')) || C==TEXT('-'))) { ValidFolder=false;break; }
            if(!ValidFolder) continue;
            const FString File=FPaths::Combine(Workspace,Folder,TEXT("Config/workshop.json"));
            const int64 Size=IFileManager::Get().FileSize(*File);
            if(Size<=0 || Size>64*1024) continue;
            FString Data;if(!FFileHelper::LoadFileToString(Data,*File)) continue;
            TSharedPtr<FJsonObject> Json;
            if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Data),Json) || !Json.IsValid()) continue;
            FString Schema,Id,Name,Category,Description,Version;
            if(!Json->TryGetStringField(TEXT("schema"),Schema) || Schema!=TEXT("anomalia-workshop-entry") ||
                !Json->TryGetStringField(TEXT("projectId"),Id) || Id!=Folder ||
                !Json->TryGetStringField(TEXT("title"),Name) || Name.IsEmpty()) continue;
            Json->TryGetStringField(TEXT("category"),Category);
            Json->TryGetStringField(TEXT("description"),Description);
            Json->TryGetStringField(TEXT("modVersion"),Version);
            Name=Name.Left(90);Category=Category.Left(35);Description=Description.Left(180);
            ++Total;
            if(!Matches(Category,Name,Description)) continue;
            ++Visible;
            Row(Name+TEXT("   ·   ")+Category+TEXT("   v")+Version.Left(32),
                Description+TEXT("\nCréation ANOMALIA Tools · plugin UE5 non activé dans le jeu"),true);
        }
        break;
    }
#endif
    // Preserve the original local Saved/Mods manifests, clearly marked as unmounted.
    const FString Root=FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("Mods"));
    TArray<FString> Folders;IFileManager::Get().FindFiles(Folders,*(Root/TEXT("*")),false,true);Folders.Sort();
    int32 Checked=0;
    for(const FString& Folder:Folders)
    {
        if(++Checked>200 || Total>=400) break;
        const FString File=FPaths::Combine(Root,Folder,TEXT("manifest.json"));
        const int64 Size=IFileManager::Get().FileSize(*File);
        if(Size<=0 || Size>256*1024) continue;
        FString Json,Error;FAnomaliaModManifest Manifest;
        if(!FFileHelper::LoadFileToString(Json,*File) ||
            !FJsonObjectConverter::JsonObjectStringToUStruct(Json,&Manifest,0,0) ||
            !UAnomaliaModResolver::ValidateModManifest(Manifest,Error))continue;
        ++Total;
        const FString Category=TEXT("Autres");
        if(!Matches(Category,Manifest.Id,FString()))continue;
        ++Visible;
        Row(Manifest.Id+TEXT("  ·  v")+Manifest.Version,
            TEXT("Manifeste reconnu · paquet non authentifié · aucun mod chargé"),false);
    }
    WorkshopStatus->SetText(FText::FromString(FString::Printf(TEXT("WORKSHOP ANOMALIA    %d création(s) trouvée(s)  ·  %d affichée(s)  ·  Chargement UE5 non connecté"),
        Total,Visible)));
    if(Visible==0)
        Row(TEXT("Aucun mod disponible dans cette catégorie"),
            TEXT("Le Workshop est intégré au jeu. Créez un mod avec ANOMALIA Tools et publiez-le dans votre bibliothèque locale.\nAucun téléchargement ni installation automatique n’est simulé."),false);
}

void UAnomaliaSessionWidget::OpenModsFolder()
{
    const FString Root=FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("Mods")));
    if(IFileManager::Get().MakeDirectory(*Root,true)) FPlatformProcess::ExploreFolder(*Root);
    else if(Feedback) Feedback->SetText(FText::FromString(TEXT("Impossible d’ouvrir le dossier Mods.")));
}
void UAnomaliaSessionWidget::OpenWorldEditor()
{
#if PLATFORM_WINDOWS
    const FString Root=FPaths::Combine(FPlatformMisc::GetEnvironmentVariable(TEXT("LOCALAPPDATA")),TEXT("CMD/ANOMALIA-UE5"));
    FString OwnerJson,ActiveJson,Product,State; TSharedPtr<FJsonObject> Owner,Active;
    const bool Valid=FFileHelper::LoadFileToString(OwnerJson,*(Root/TEXT("owner.json"))) &&
        FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(OwnerJson),Owner) && Owner.IsValid() &&
        Owner->TryGetStringField(TEXT("product"),Product) && Product==TEXT("ANOMALIA-UE5-EDITOR-v1") &&
        FFileHelper::LoadFileToString(ActiveJson,*(Root/TEXT("active.json"))) &&
        FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(ActiveJson),Active) && Active.IsValid() &&
        Active->TryGetStringField(TEXT("state"),State) && State==TEXT("VALIDATED_EDITOR_PROJECT_INSTALLED");
    const FString Launcher=Root/TEXT("bootstrap/Launch-AnomaliaUE5.vbs");
    if(Valid && FPaths::FileExists(Launcher) && FPlatformProcess::LaunchFileInDefaultExternalApplication(*Launcher))
    { if(Feedback) Feedback->SetText(FText::FromString(TEXT("Ouverture du projet synchronisé dans Unreal Editor. Votre partie reste en pause."))); return; }
#endif
    if(Feedback) Feedback->SetText(FText::FromString(TEXT("Le projet Unreal synchronisé n’est pas disponible. Attendez la fin de la mise à jour de l’éditeur.")));
}
void UAnomaliaSessionWidget::Play()
{
    FinishIntro();
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
    if(bStartupIntro) { FinishIntro();return FReply::Handled(); }
    if(Event.GetKey()==EKeys::Escape || Event.GetKey()==EKeys::Gamepad_FaceButton_Right)
    {
        if(DetailsFrame && DetailsFrame->GetVisibility()!=ESlateVisibility::Collapsed)
        { ClosePage(); if(HomeButton) HomeButton->SetUserFocus(GetOwningPlayer()); }
        else if(!bMainMenu) Play();
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(Geometry,Event);
}
