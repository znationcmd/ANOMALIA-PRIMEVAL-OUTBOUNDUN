#include "AnomaliaZPrigimaliaSessionWidget.h"
#include "AnomaliaZPrigimaliaGameMode.h"
#include "AnomaliaZPrigimaliaSurvivor.h"
#include "AnomaliaZPrigimaliaStatusWidget.h"
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
#include "Components/UniformGridPanel.h"
#include "Components/UniformGridSlot.h"

#include "Styling/SlateTypes.h"

#include "Engine/Texture2D.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "JsonObjectConverter.h"
#include "AnomaliaZPrigimaliaModResolver.h"
#include "HAL/PlatformMisc.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonReader.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerState.h"
#include "Components/ProgressBar.h"
#include "TimerManager.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "AnomaliaZPrigimaliaPerformanceLibrary.h"

UAnomaliaZPrigimaliaSessionWidget* UAnomaliaZPrigimaliaSessionWidget::Open(APlayerController* PC,bool MainMenu)
{
    if(!PC || !PC->IsLocalController() || (MainMenu && PC->GetNetMode()!=NM_Standalone)) return nullptr;
    TArray<UUserWidget*> Existing; UWidgetBlueprintLibrary::GetAllWidgetsOfClass(PC,Existing,StaticClass(),false);
    for(auto* Widget:Existing) if(Widget && Widget->IsInViewport()) return Cast<UAnomaliaZPrigimaliaSessionWidget>(Widget);
    if(auto* S=Cast<AAnomaliaZPrigimaliaSurvivor>(PC->GetPawn())) S->CloseInventory();
    auto* Menu=CreateWidget<UAnomaliaZPrigimaliaSessionWidget>(PC,StaticClass()); if(!Menu) return nullptr;
    Menu->bMainMenu=MainMenu; Menu->AddToViewport(100);
    if(MainMenu) if(auto* S=Cast<AAnomaliaZPrigimaliaSurvivor>(PC->GetPawn())) if(S->StatusWidget)
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
TSharedRef<SWidget> UAnomaliaZPrigimaliaSessionWidget::RebuildWidget()
{
    if(!WidgetTree) WidgetTree=NewObject<UWidgetTree>(this,TEXT("WidgetTree"));
    BuildLayout();
    return Super::RebuildWidget();
}

void UAnomaliaZPrigimaliaSessionWidget::NativeConstruct()
{
    Super::NativeConstruct(); SetIsFocusable(true);
    bStartupIntro=bMainMenu && MenuArtwork && StartupArtworkFrame;
    if(bStartupIntro)
    {
        // The poster belongs to boot only, never to the interactive menu.
        StartupArtworkFrame->SetVisibility(ESlateVisibility::Visible);
        MenuArtwork->SetVisibility(ESlateVisibility::Visible);
        IntroStarted=FPlatformTime::Seconds(); MenuArtwork->SetRenderOpacity(0.f);
        if(NavigationFrame) NavigationFrame->SetVisibility(ESlateVisibility::Hidden);
    }
    auto* PC=GetOwningPlayer();
    if(bMainMenu && PC && GetWorld() && GetWorld()->GetMapName().EndsWith(TEXT("ANOMALIA_Playable_v1")) && Cast<AAnomaliaZPrigimaliaSurvivor>(PC->GetPawn()))
    {
        // Frame the ACTUAL restored survivor in the ACTUAL world, at the
        // last saved location. Never teleport or replace player appearance.
        auto* Survivor=Cast<AAnomaliaZPrigimaliaSurvivor>(PC->GetPawn());
        const FVector Center=Survivor->GetActorLocation()+FVector(0,0,100);
        const FVector Eye=Center+Survivor->GetActorForwardVector()*285.f+Survivor->GetActorRightVector()*140.f+FVector(0,0,60);
        FActorSpawnParameters Params; Params.ObjectFlags|=RF_Transient;
        MenuCamera=GetWorld()->SpawnActor<ACameraActor>(ACameraActor::StaticClass(),Eye,(Center-Eye).Rotation(),Params);
        if(MenuCamera)
        {
            MenuCamera->GetCameraComponent()->SetFieldOfView(63.f);
            PreviousViewTarget=PC->GetViewTarget(); PC->SetViewTarget(MenuCamera);
            if(PC->PlayerCameraManager) PC->PlayerCameraManager->UpdateCamera(0.f);
        }
    }
}
void UAnomaliaZPrigimaliaSessionWidget::NativeDestruct()
{
    if(HiddenStatusWidget) { HiddenStatusWidget->SetVisibility(PreviousStatusVisibility);HiddenStatusWidget=nullptr; }
    if(MenuCamera)
    {
        if(auto* PC=GetOwningPlayer()) if(PreviousViewTarget.IsValid()) PC->SetViewTarget(PreviousViewTarget.Get());
        MenuCamera->Destroy(); MenuCamera=nullptr; PreviousViewTarget.Reset();
    }
    Super::NativeDestruct();
}
void UAnomaliaZPrigimaliaSessionWidget::NativeTick(const FGeometry& Geometry,float DeltaTime)
{
    Super::NativeTick(Geometry,DeltaTime);
    if(!bStartupIntro || !MenuArtwork) return;
    const float Elapsed=static_cast<float>(FPlatformTime::Seconds()-IntroStarted);
    const float Progress=FMath::Clamp(Elapsed/4.5f,0.f,1.f);
    MenuArtwork->SetRenderOpacity(FMath::Clamp(Elapsed/1.2f,0.f,1.f));
    MenuArtwork->SetRenderScale(FVector2D(.97f+.03f*Progress));
    if(Elapsed>=4.5f) FinishIntro();
}
void UAnomaliaZPrigimaliaSessionWidget::FinishIntro()
{
    bStartupIntro=false;
    // Collapse the *entire* splash frame, including its black matte: otherwise
    // it becomes a permanent wallpaper hiding the actual 3D menu scene.
    if(StartupArtworkFrame) StartupArtworkFrame->SetVisibility(ESlateVisibility::Collapsed);
    if(MenuArtwork) { MenuArtwork->SetRenderOpacity(0.f);MenuArtwork->SetVisibility(ESlateVisibility::Collapsed); }
    if(NavigationFrame) NavigationFrame->SetVisibility(ESlateVisibility::Visible);
}
FReply UAnomaliaZPrigimaliaSessionWidget::NativeOnMouseButtonDown(const FGeometry& Geometry,const FPointerEvent& Event)
{
    if(bStartupIntro) { FinishIntro();return FReply::Handled(); }
    return Super::NativeOnMouseButtonDown(Geometry,Event);
}
void UAnomaliaZPrigimaliaSessionWidget::BuildPremiumWorkshop(UCanvasPanel* Canvas)
{
    if(!Canvas || !WidgetTree) return;
    // Dedicated native MODS screen: real widgets and actions, not an image.
    // The WorkForge brand lives inside Mods; the external Tools app is separate.
    const FLinearColor Black(.007f,.010f,.015f,.995f);
    const FLinearColor Surface(.020f,.029f,.042f,.98f);
    const FLinearColor Panel(.025f,.034f,.047f,.98f);
    const FLinearColor Hot(1.f,.14f,.065f,1.f);
    const FLinearColor Gold(1.f,.76f,.58f,1.f);
    const FLinearColor Soft(.87f,.89f,.91f,1.f);
    const FLinearColor Cyan(.22f,.86f,.75f,1.f);
    auto* Logo=LoadObject<UTexture2D>(nullptr,TEXT("/Game/AnomaliaZPrigimalia/Branding/T_WorkshopLogo.T_WorkshopLogo"),nullptr,LOAD_NoWarn);
    auto* Backdrop=LoadObject<UTexture2D>(nullptr,TEXT("/Game/AnomaliaZPrigimalia/WorkForge/Artwork/T_WFHero.T_WFHero"),nullptr,LOAD_NoWarn);
    if(!Backdrop) Backdrop=LoadObject<UTexture2D>(nullptr,TEXT("/Game/AnomaliaZPrigimalia/Branding/T_MenuBackdrop.T_MenuBackdrop"),nullptr,LOAD_NoWarn);
    // The nine artwork textures are ordinary UI assets. Each category remains
    // a separate real UButton with a bound filtering callback.
    TArray<UTexture2D*> CategoryArt;
    for(int32 ArtIndex=0;ArtIndex<9;ArtIndex++)
    {
        const FString Name=FString::Printf(TEXT("T_WFCategory%d"),ArtIndex);
        const FString Path=FString::Printf(TEXT("/Game/AnomaliaZPrigimalia/WorkForge/Artwork/%s.%s"),*Name,*Name);
        CategoryArt.Add(LoadObject<UTexture2D>(nullptr,*Path,nullptr,LOAD_NoWarn));
    }

    auto Label=[&](const FString& Value,int32 FontSize,const FLinearColor& Color)
    {
        auto* Text=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        Text->SetText(FText::FromString(Value));
        Text->SetAutoWrapText(true);
        auto Font=Text->GetFont();Font.Size=FontSize;Text->SetFont(Font);
        Text->SetColorAndOpacity(FSlateColor(Color));
        return Text;
    };
    auto Box=[&](const FLinearColor& Color,float InnerPadding)
    {
        auto* Border=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
        Border->SetBrushColor(Color);Border->SetPadding(FMargin(InnerPadding));
        return Border;
    };
    auto Vertical=[&]()
    {
        return WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    };
    auto Horizontal=[&]()
    {
        return WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
    };
    auto AddLabel=[&](UVerticalBox* Root,const FString& Text,int32 Size,const FLinearColor& Color,float Pad=4.f)
    {
        auto* Widget=Label(Text,Size,Color);
        Root->AddChildToVerticalBox(Widget)->SetPadding(FMargin(4.f,Pad));
        return Widget;
    };
    auto Action=[&](UHorizontalBox* Parent,const TCHAR* Id,const FString& Title)
    {
        auto* B=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),FName(Id));
        B->SetBackgroundColor(FLinearColor(.72f,.032f,.018f,1.f));
        auto* Caption=Label(Title,13,FLinearColor::White);
        B->SetContent(Caption);
        auto* Slot=Parent->AddChildToHorizontalBox(B);
        Slot->SetPadding(FMargin(5,6));
        return B;
    };
    auto Picture=[&](UHorizontalBox* Parent,UTexture2D* Texture,const FVector2D Size)
    {
        if(!Texture) return;
        auto* SizeBox=WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
        SizeBox->SetWidthOverride(Size.X);SizeBox->SetHeightOverride(Size.Y);
        auto* I=WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
        I->SetBrushFromTexture(Texture,true);
        SizeBox->SetContent(I);
        Parent->AddChildToHorizontalBox(SizeBox)->SetPadding(FMargin(4));
    };

    WorkshopFrame=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(),TEXT("WorkshopFullScreen"));
    WorkshopFrame->SetBrushColor(Black);WorkshopFrame->SetPadding(FMargin(0));
    auto* Anchor=Canvas->AddChildToCanvas(WorkshopFrame);
    Anchor->SetAnchors(FAnchors(.015f,.012f,.985f,.985f));
    Anchor->SetOffsets(FMargin(0.f));
    auto* Root=Vertical();
    WorkshopFrame->SetContent(Root);

    // Persistent top nav, matched to the user's launcher-style reference.
    auto* Header=Box(FLinearColor(.022f,.018f,.025f,.995f),8);
    Root->AddChildToVerticalBox(Header)->SetPadding(FMargin(0,0,0,3));
    auto* HeaderRow=Horizontal();Header->SetContent(HeaderRow);
    Picture(HeaderRow,Logo,FVector2D(64,64));
    auto* Titles=Vertical();
    auto* TitleSlot=HeaderRow->AddChildToHorizontalBox(Titles);
    TitleSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    AddLabel(Titles,TEXT("A N O M A L I A"),22,FLinearColor::White,0);
    AddLabel(Titles,TEXT("W O R K F O R G E   |   M O D S   &   C R É A T I O N S"),9,Hot,0);
    WorkshopSearch=WidgetTree->ConstructWidget<UEditableTextBox>(UEditableTextBox::StaticClass(),TEXT("WorkshopSearch"));
    WorkshopSearch->SetHintText(FText::FromString(TEXT("Rechercher un mod, un créateur, une catégorie...")));
    WorkshopSearch->SetMinDesiredWidth(285.f);
    WorkshopSearch->OnTextChanged.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopSearchChanged);
    auto* SearchSlot=HeaderRow->AddChildToHorizontalBox(WorkshopSearch);
    SearchSlot->SetVerticalAlignment(VAlign_Center); SearchSlot->SetPadding(FMargin(8,0));
    Action(HeaderRow,TEXT("WorkshopRefresh"),TEXT("Actualiser"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::RefreshWorkshop);
    Action(HeaderRow,TEXT("WorkshopPlay"),TEXT("▶  JOUER"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::Play);
    Action(HeaderRow,TEXT("WorkshopReturn"),TEXT("←  Retour"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::CloseWorkshop);

    // Main viewport with genuine 3-column layout.
    auto* Columns=Horizontal();
    auto* BodySlot=Root->AddChildToVerticalBox(Columns);
    BodySlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

    // Left rail, compact and scrollable, no fake interactive items.
    auto* LeftWidth=WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
    LeftWidth->SetWidthOverride(188.f);
    Columns->AddChildToHorizontalBox(LeftWidth);
    auto* Left=Box(FLinearColor(.011f,.016f,.023f,.99f),10);
    LeftWidth->SetContent(Left);
    auto* LeftContent=Vertical();Left->SetContent(LeftContent);
    AddLabel(LeftContent,TEXT("ANOMALIA  •  MODS"),15,FLinearColor::White,10);
    AddLabel(LeftContent,TEXT("━━━━━━━━━━━━━━━━━━"),11,Hot,0);
    // Native navigation controls, not decorative dead labels.
    auto NavButton=[&](const TCHAR* Id,const FString& Caption)
    {
        auto* Button=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),FName(Id));
        const bool bActive=Caption.Contains(TEXT("MODS  •"));
        Button->SetBackgroundColor(bActive?
            FLinearColor(.77f,.055f,.027f,1.f):FLinearColor(.035f,.043f,.058f,.98f));
        Button->SetContent(Label(Caption,13,bActive?FLinearColor::White:Soft));
        LeftContent->AddChildToVerticalBox(Button)->SetPadding(FMargin(2,5));
        return Button;
    };
    NavButton(TEXT("WFNavHome"),TEXT("⌂   Accueil"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::CloseWorkshop);
    NavButton(TEXT("WFNavForge"),TEXT("✦   WorkForge"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopShowCatalogue);
    NavButton(TEXT("WFNavMods"),TEXT("▦   MODS  •  catalogue"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopShowCatalogue);
    NavButton(TEXT("WFNavCreations"),TEXT("✎   Créations"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::OpenWorkshopTools);
    NavButton(TEXT("WFNavCollections"),TEXT("▧   Collections"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopShowCollections);
    NavButton(TEXT("WFNavCategories"),TEXT("▤   Catégories"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopShowCategories);
    NavButton(TEXT("WFNavServers"),TEXT("☷   Serveurs"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::OpenWorkshopHosting);
    NavButton(TEXT("WFNavMyMods"),TEXT("▣   Mes mods"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopShowMyMods);
    NavButton(TEXT("WFNavDownloads"),TEXT("↓   Téléchargements"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopShowDownloads);
    NavButton(TEXT("WFNavCommunity"),TEXT("☏   Communauté"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopShowCommunity);
    NavButton(TEXT("WFNavSettings"),TEXT("⚙   Paramètres"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopShowSettings);
    AddLabel(LeftContent,TEXT("━━━━━━━━━━━━━━━━━━"),11,Hot,12);
    if(Logo)
    {
        auto* LogoImage=WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
        LogoImage->SetBrushFromTexture(Logo,true);
        LogoImage->SetDesiredSizeOverride(FVector2D(148,148));
        LeftContent->AddChildToVerticalBox(LogoImage)->SetPadding(FMargin(0,8));
    }
    AddLabel(LeftContent,TEXT("SURVIVRE\nMODIFIER\nEXPLORER\nENSEMBLE"),10,Soft,8);

    // Center scroll holds cinematic hero, category cards, and actual mod records.
    auto* CenterScroll=WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(),TEXT("WorkshopMainScroll"));
    Columns->AddChildToHorizontalBox(CenterScroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    auto* Center=Vertical();CenterScroll->AddChild(Center);
    auto* Hero=Box(FLinearColor(.042f,.022f,.029f,.99f),4);
    Center->AddChildToVerticalBox(Hero)->SetPadding(FMargin(12,10,9,7));
    auto* HeroWrap=WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());Hero->SetContent(HeroWrap);
    if(Backdrop)
    {
        auto* Background=WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(),TEXT("WorkshopHeroBackdrop"));
        Background->SetBrushFromTexture(Backdrop,true);
        Background->SetDesiredSizeOverride(FVector2D(780.f,250.f));
        Background->SetColorAndOpacity(FLinearColor(1.f,1.f,1.f,.83f));
        HeroWrap->AddChildToOverlay(Background);
    }
    auto* HeroText=Vertical();
    HeroWrap->AddChildToOverlay(HeroText)->SetPadding(FMargin(16,12));
    AddLabel(HeroText,TEXT("ANOMALIA"),44,FLinearColor::White,0);
    AddLabel(HeroText,TEXT("W O R K F O R G E"),29,FLinearColor(1.f,.28f,.15f),0);
    AddLabel(HeroText,TEXT("M O D S   &   C R É A T I O N S"),12,Soft,1);
    AddLabel(HeroText,TEXT("Explorez les mods et créations pour ANOMALIA’Z PRIGIMALIA."),14,FLinearColor::White,10);
    AddLabel(HeroText,TEXT("Catalogue local réel  •  Recherche  •  Catégories  •  Collections"),12,Gold,2);
    // This stats ribbon deliberately uses LIVE local counts, never numbers
    // copied from the visual mockup or invented remote community ratings.
    auto* Stats=Horizontal();
    HeroText->AddChildToVerticalBox(Stats)->SetPadding(FMargin(0,10,0,4));
    auto StatBlock=[&](const FString& Initial,const FString& Caption,UTextBlock*& Out)
    {
        auto* Column=Vertical();
        Stats->AddChildToHorizontalBox(Column)->SetPadding(FMargin(0,0,24,0));
        Out=AddLabel(Column,Initial,20,FLinearColor(1.f,.53f,.34f),0);
        AddLabel(Column,Caption,11,FLinearColor::White,0);
    };
    UTextBlock* ModsCount=nullptr;
    UTextBlock* CreatorsCount=nullptr;
    StatBlock(TEXT("0"),TEXT("Mods locaux"),ModsCount);
    StatBlock(TEXT("0"),TEXT("Créations locales"),CreatorsCount);
    WorkshopCountLabel=ModsCount;
    WorkshopCreatorsLabel=CreatorsCount;
    auto* Offline=Vertical();
    Stats->AddChildToHorizontalBox(Offline);
    AddLabel(Offline,TEXT("LOCAL"),20,Cyan,0);
    AddLabel(Offline,TEXT("Catalogue hors ligne"),11,FLinearColor::White,0);

    auto* CategoriesTitle=Label(TEXT("EXPLORER PAR CATÉGORIE"),17,FLinearColor::White);
    Center->AddChildToVerticalBox(CategoriesTitle)->SetPadding(FMargin(14,11,8,4));
    auto* Grid=WidgetTree->ConstructWidget<UUniformGridPanel>(UUniformGridPanel::StaticClass(),TEXT("WorkshopCategories"));
    Center->AddChildToVerticalBox(Grid)->SetPadding(FMargin(10,3,8,9));
    Grid->SetSlotPadding(FMargin(3,4));
    const TArray<TTuple<FString,FString>> Cats={
      MakeTuple(FString(TEXT("▦  Tous les mods")),FString(TEXT("Tous"))),
      MakeTuple(FString(TEXT("▰  Véhicules")),FString(TEXT("Véhicules"))),
      MakeTuple(FString(TEXT("◆  Créatures")),FString(TEXT("Créatures"))),
      MakeTuple(FString(TEXT("▣  Bâtiments")),FString(TEXT("Bâtiments"))),
      MakeTuple(FString(TEXT("▤  Cartes")),FString(TEXT("Cartes"))),
      MakeTuple(FString(TEXT("⌁  Armes")),FString(TEXT("Armes"))),
      MakeTuple(FString(TEXT("✺  Survie")),FString(TEXT("Survie"))),
      MakeTuple(FString(TEXT("◈  Gameplay")),FString(TEXT("Gameplay"))),
      MakeTuple(FString(TEXT("⚙  Outils")),FString(TEXT("Outils")))
    };
    for(int32 I=0;I<Cats.Num();++I)
    {
        const FString& Title=Cats[I].Get<0>();
        const FString& Key=Cats[I].Get<1>();
        auto* Card=Box(I==0?FLinearColor(.72f,.10f,.032f,.99f):FLinearColor(.055f,.074f,.095f,.99f),2);
        Grid->AddChildToUniformGrid(Card,I/9,I%9);
        auto* CategoryImage=WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
        Card->SetContent(CategoryImage);
        if(CategoryArt.IsValidIndex(I) && CategoryArt[I])
        {
            auto* Art=WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
            Art->SetBrushFromTexture(CategoryArt[I],true);
            Art->SetDesiredSizeOverride(FVector2D(108.f,100.f));
            Art->SetColorAndOpacity(FLinearColor(.92f,.92f,.93f,.9f));
            CategoryImage->AddChildToOverlay(Art);
        }
        auto* B=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),FName(*FString::Printf(TEXT("WorkshopCategoryCard%d"),I)));
        B->SetBackgroundColor(I==0?FLinearColor(.63f,.035f,.012f,.82f):FLinearColor(.018f,.025f,.031f,.72f));
        auto* LabelBox=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
        LabelBox->AddChildToVerticalBox(WidgetTree->ConstructWidget<USpacer>(USpacer::StaticClass()))->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        auto* Txt=Label(Title,12,FLinearColor::White);Txt->SetJustification(ETextJustify::Center);
        LabelBox->AddChildToVerticalBox(Txt)->SetPadding(FMargin(1.f,12.f,1.f,2.f));
        auto* CountLabel=Label(TEXT("0 mods locaux"),10,FLinearColor(.88f,.90f,.93f));
        CountLabel->SetJustification(ETextJustify::Center);
        LabelBox->AddChildToVerticalBox(CountLabel)->SetPadding(FMargin(1.f,0.f,1.f,5.f));
        WorkshopCategoryCountLabels.Add(CountLabel);
        B->SetContent(LabelBox);
        auto* ButtonSlot=CategoryImage->AddChildToOverlay(B);
        ButtonSlot->SetHorizontalAlignment(HAlign_Fill);
        ButtonSlot->SetVerticalAlignment(VAlign_Fill);
        switch(I){
            case 0:B->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterAll);break;
            case 1:B->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterVehicles);break;
            case 2:B->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterCreatures);break;
            case 3:B->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterBuildings);break;
            case 4:B->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterMaps);break;
            case 5:B->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterWeapons);break;
            case 6:B->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterSurvival);break;
            case 7:B->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterGameplay);break;
            case 8:B->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterTools);break;
        }
    }
    auto* ContentHeader=Horizontal();
    Center->AddChildToVerticalBox(ContentHeader)->SetPadding(FMargin(10,7,10,5));
    auto* SectionTitle=Label(TEXT("MODS POPULAIRES  •  CATALOGUE LOCAL"),18,FLinearColor::White);
    ContentHeader->AddChildToHorizontalBox(SectionTitle)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    auto* SearchPanel=Box(Panel,7);
    Center->AddChildToVerticalBox(SearchPanel)->SetPadding(FMargin(10,0,10,7));
    auto* Filters=Horizontal();SearchPanel->SetContent(Filters);
    // The real, live search box is in the top bar, matching the screenshot.
    // Below it the filters and sorting remain selectable with controller/mouse.
    WorkshopCategory=WidgetTree->ConstructWidget<UComboBoxString>(UComboBoxString::StaticClass(),TEXT("WorkshopCategory"));
    for(const TCHAR* Item:{TEXT("Tous"),TEXT("Véhicules"),TEXT("Armes"),TEXT("Bâtiments"),TEXT("Créatures"),TEXT("Survie"),TEXT("Cartes"),TEXT("Gameplay"),TEXT("Vêtements"),TEXT("Outils"),TEXT("Autres")})
        WorkshopCategory->AddOption(Item);
    WorkshopCategory->SetSelectedOption(TEXT("Tous"));
    Filters->AddChildToHorizontalBox(WorkshopCategory)->SetPadding(FMargin(12,0,0,0));
    WorkshopSort=WidgetTree->ConstructWidget<UComboBoxString>(UComboBoxString::StaticClass(),TEXT("WorkshopSort"));
    WorkshopSort->AddOption(TEXT("Récents"));
    WorkshopSort->AddOption(TEXT("Nom A-Z"));
    WorkshopSort->AddOption(TEXT("Catégorie"));
    WorkshopSort->AddOption(TEXT("Version"));
    WorkshopSort->SetSelectedOption(TEXT("Récents"));
    Filters->AddChildToHorizontalBox(WorkshopSort)->SetPadding(FMargin(10,0,0,0));
    WorkshopSort->OnSelectionChanged.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopCategoryChanged);

    WorkshopCategory->OnSelectionChanged.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopCategoryChanged);
    WorkshopStatus=AddLabel(Center,TEXT("Recherche de créations locales..."),12,Cyan,3);
    auto* ContentScroll=WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(),TEXT("WorkshopListScroll"));
    Center->AddChildToVerticalBox(ContentScroll)->SetPadding(FMargin(10,4));
    WorkshopCards=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("WorkshopCards"));
    ContentScroll->AddChild(WorkshopCards);
    auto* Note=Box(FLinearColor(.12f,.050f,.05f,.99f),10);
    Center->AddChildToVerticalBox(Note)->SetPadding(FMargin(10,8,10,13));
    Note->SetContent(Label(TEXT("Catalogue : vrais manifestes locaux uniquement. Installation et téléchargement communautaires indisponibles tant que le service sécurisé n'est pas connecté."),11,Soft));

    // Right rail: honest connection status, community preview and top mods (no invented scores).
    auto* RightSize=WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
    RightSize->SetWidthOverride(255.f);
    Columns->AddChildToHorizontalBox(RightSize);
    auto* RightBg=Box(FLinearColor(.013f,.020f,.029f,.99f),9);RightSize->SetContent(RightBg);
    auto* Right=Vertical();RightBg->SetContent(Right);
    auto* Connection=Box(FLinearColor(.13f,.055f,.052f,.96f),8);
    Right->AddChildToVerticalBox(Connection)->SetPadding(FMargin(0,4,0,11));
    auto* Connected=Vertical();Connection->SetContent(Connected);
    AddLabel(Connected,TEXT("●  ANOMALIA CONNECTÉ"),15,FLinearColor::White,3);
    AddLabel(Connected,TEXT("WorkForge intégré au jeu"),11,Cyan,3);
    AddLabel(Connected,TEXT("━━━━━━━━━━━━━━━━━━"),11,Hot,4);
    AddLabel(Connected,TEXT("Workshop local       ✓ ACTIF"),11,FLinearColor(.48f,.92f,.65f),6);
    AddLabel(Connected,TEXT("Synchronisation      Locale"),11,Soft,6);
    WorkshopInstalledLabel=AddLabel(Connected,TEXT("Manifestes locaux       vérification"),11,Gold,6);
    AddLabel(Connected,TEXT("Communauté           En préparation"),11,Soft,6);
    auto* ToolsRow=Horizontal();Connected->AddChildToVerticalBox(ToolsRow);
    Action(ToolsRow,TEXT("WorkshopOpenTools"),TEXT("ANOMALIA Tools ↗"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::OpenWorkshopTools);
    auto* HostingRow=Horizontal();Connected->AddChildToVerticalBox(HostingRow);
    Action(HostingRow,TEXT("WorkshopOpenHosting"),TEXT("CMD Hosting ↗"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::OpenWorkshopHosting);
    auto* RefreshRow=Horizontal();Connected->AddChildToVerticalBox(RefreshRow);
    Action(RefreshRow,TEXT("WorkshopOpenFolder"),TEXT("Dossier Mods ↗"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopOpenLocalModsFolder);
    auto* ManageRow=Horizontal();Connected->AddChildToVerticalBox(ManageRow);
    Action(ManageRow,TEXT("WorkshopManageMods"),TEXT("Gérer mes mods  →"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopShowMyMods);

    auto* Community=Box(Panel,10);
    Right->AddChildToVerticalBox(Community)->SetPadding(FMargin(0,4,0,10));
    auto* C=Vertical();Community->SetContent(C);
    AddLabel(C,TEXT("COMMUNAUTÉ"),16,Gold,4);
    AddLabel(C,TEXT("Discussions   •   Guides   •   Créations"),11,Soft,5);
    AddLabel(C,TEXT("La communauté sera visible après connexion du catalogue."),11,Soft,8);
    auto* CommunityRow=Horizontal(); C->AddChildToVerticalBox(CommunityRow);
    Action(CommunityRow,TEXT("WorkshopCommunity"),TEXT("État du service"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopShowCommunity);
    auto* Popular=Box(Panel,10);
    Right->AddChildToVerticalBox(Popular)->SetPadding(FMargin(0,4));
    auto* P=Vertical();Popular->SetContent(P);
    AddLabel(P,TEXT("MODS LES MIEUX NOTÉS"),15,Gold,4);
    AddLabel(P,TEXT("Les meilleures notes seront affichées ici à partir d'avis vérifiés, lorsque le service sera relié."),11,Soft,8);
    WorkshopFrame->SetVisibility(ESlateVisibility::Collapsed);
}

// A dedicated, usable native server browser. Unlike the visual references,
// this never invents live public listings: rows come only from bounded local
// configuration. A real server connection requires a validated host:port.
void UAnomaliaZPrigimaliaSessionWidget::BuildServerBrowser(UCanvasPanel* Canvas)
{
    ServerBrowserFrame=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(),TEXT("ServerBrowserFullScreen"));
    ServerBrowserFrame->SetBrushColor(FLinearColor(.009f,.014f,.019f,.91f));
    ServerBrowserFrame->SetPadding(FMargin(26.f));
    auto* BrowserSlot=Canvas->AddChildToCanvas(ServerBrowserFrame);
    BrowserSlot->SetAnchors(FAnchors(.035f,.065f,.965f,.925f)); BrowserSlot->SetOffsets(FMargin(0));
    auto* Root=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    ServerBrowserFrame->SetContent(Root);
    auto Label=[&](UVerticalBox* V,const FString& Text,int32 Size,FLinearColor Color)
    {
        auto* T=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        T->SetText(FText::FromString(Text)); auto Font=T->GetFont();Font.Size=Size;T->SetFont(Font);
        T->SetColorAndOpacity(FSlateColor(Color));T->SetAutoWrapText(true);
        V->AddChildToVerticalBox(T)->SetPadding(FMargin(0,4));return T;
    };
    auto Button=[&](UHorizontalBox* Row,const TCHAR* Name,const TCHAR* Title)
    {
        auto* B=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),FName(Name));
        B->SetBackgroundColor(FLinearColor(.30f,.042f,.040f,.97f));
        auto* T=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        T->SetText(FText::FromString(Title));auto Font=T->GetFont();Font.Size=15;T->SetFont(Font);
        T->SetColorAndOpacity(FSlateColor(FLinearColor::White));B->SetContent(T);
        Row->AddChildToHorizontalBox(B)->SetPadding(FMargin(5,3));return B;
    };
    Label(Root,TEXT("ANOMALIA'Z  |  NAVIGATEUR DE SERVEURS"),27,FLinearColor::White);
    Label(Root,TEXT("Le personnage et le monde de la dernière session restent visibles à l'arrière-plan."),
        12,FLinearColor(.79f,.86f,.89f));
    auto* Tabs=WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
    Root->AddChildToVerticalBox(Tabs);
    Button(Tabs,TEXT("ServerTabFavorite"),TEXT("FAVORIS"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::TabFavoriteServers);
    Button(Tabs,TEXT("ServerTabOfficial"),TEXT("OFFICIEL"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::TabOfficialServers);
    Button(Tabs,TEXT("ServerTabCommunity"),TEXT("COMMUNAUTAIRE"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::TabCommunityServers);
    Button(Tabs,TEXT("ServerBrowserRefresh"),TEXT("ACTUALISER"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::RefreshServerBrowser);
    Button(Tabs,TEXT("ServerBrowserBack"),TEXT("RETOUR"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::CloseServerBrowser);
    auto* Columns=WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
    Root->AddChildToVerticalBox(Columns)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    auto* List=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    Columns->AddChildToHorizontalBox(List)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    Label(List,TEXT("SERVEURS  /  NOM  ·  CARTE  ·  ADRESSE"),17,FLinearColor::White);
    ServerSearch=WidgetTree->ConstructWidget<UEditableTextBox>(UEditableTextBox::StaticClass(),TEXT("ServerBrowserSearch"));
    ServerSearch->SetHintText(FText::FromString(TEXT("Rechercher un serveur ou une carte...")));
    ServerSearch->OnTextChanged.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::ServerSearchChanged);
    List->AddChildToVerticalBox(ServerSearch)->SetPadding(FMargin(0,4,12,8));
    ServerSelect=WidgetTree->ConstructWidget<UComboBoxString>(UComboBoxString::StaticClass(),TEXT("ServerBrowserSelect"));
    ServerSelect->OnSelectionChanged.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::ServerSelectionChanged);
    List->AddChildToVerticalBox(ServerSelect)->SetPadding(FMargin(0,4,12,8));
    auto* Scroll=WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass());
    List->AddChildToVerticalBox(Scroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    ServerResults=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("ServerBrowserResults"));
    Scroll->AddChild(ServerResults);
    auto* FilterPanel=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
    FilterPanel->SetBrushColor(FLinearColor(.02f,.028f,.037f,.97f));
    FilterPanel->SetPadding(FMargin(20));
    Columns->AddChildToHorizontalBox(FilterPanel)->SetPadding(FMargin(12,0,0,0));
    auto* FilterRows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    FilterPanel->SetContent(FilterRows);
    Label(FilterRows,TEXT("FILTRES / DÉTAILS"),20,FLinearColor::White);
    Label(FilterRows,TEXT("Favoris  •  Officiel  •  Communautaire"),12,FLinearColor(.8f,.84f,.9f));
    Label(FilterRows,TEXT("Disponibilité et ping non confirmés sans service de découverte."),12,FLinearColor(.9f,.77f,.6f));
    ServerStatus=Label(FilterRows,TEXT("Aucun serveur vérifié pour cette catégorie."),13,FLinearColor::White);
    auto* Commands=WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
    FilterRows->AddChildToVerticalBox(Commands)->SetPadding(FMargin(0,22,0,0));
    Button(Commands,TEXT("ServerBrowserJoin"),TEXT("REJOINDRE"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::JoinSelectedServer);
    auto* Solo=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),TEXT("ServerBrowserSolo"));
    Solo->SetBackgroundColor(FLinearColor(.70f,.06f,.045f,1.f));
    auto* SoloText=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    SoloText->SetText(FText::FromString(TEXT("CONTINUER EN SOLO")));
    SoloText->SetColorAndOpacity(FSlateColor(FLinearColor::White));
    Solo->SetContent(SoloText); Solo->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::ResumeLocalSession);
    FilterRows->AddChildToVerticalBox(Solo)->SetPadding(FMargin(5,14));
    ServerBrowserFrame->SetVisibility(ESlateVisibility::Collapsed);
}

void UAnomaliaZPrigimaliaSessionWidget::BuildOnlinePlayers(UCanvasPanel* Canvas)
{
    OnlinePlayersFrame=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(),TEXT("PauseOnlinePlayers"));
    OnlinePlayersFrame->SetBrushColor(FLinearColor(.014f,.020f,.027f,.94f));
    OnlinePlayersFrame->SetPadding(FMargin(22));
    auto* PlayersSlot=Canvas->AddChildToCanvas(OnlinePlayersFrame);
    PlayersSlot->SetAnchors(FAnchors(.59f,.07f,.96f,.88f));PlayersSlot->SetOffsets(FMargin(0));
    auto* Rows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    OnlinePlayersFrame->SetContent(Rows);
    auto* Header=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Header->SetText(FText::FromString(TEXT("JOUEURS EN LIGNE")));
    auto Font=Header->GetFont();Font.Size=24;Header->SetFont(Font);
    Rows->AddChildToVerticalBox(Header)->SetPadding(FMargin(0,8));
    OnlinePlayerRows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("PauseOnlinePlayerRows"));
    Rows->AddChildToVerticalBox(OnlinePlayerRows)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    auto* Refresh=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),TEXT("PauseOnlineRefresh"));
    auto* RefreshText=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    RefreshText->SetText(FText::FromString(TEXT("ACTUALISER LES JOUEURS")));
    Refresh->SetContent(RefreshText);
    Refresh->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::RefreshOnlinePlayers);
    Rows->AddChildToVerticalBox(Refresh);
    auto* Return=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),TEXT("PauseOnlineBack"));
    auto* ReturnText=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    ReturnText->SetText(FText::FromString(TEXT("RETOUR À LA PAUSE")));
    Return->SetContent(ReturnText);
    Return->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::CloseOnlinePlayers);
    Rows->AddChildToVerticalBox(Return)->SetPadding(FMargin(0,8));
    OnlinePlayersFrame->SetVisibility(ESlateVisibility::Collapsed);
}

void UAnomaliaZPrigimaliaSessionWidget::BuildTravelLoading(UCanvasPanel* Canvas)
{
    TravelLoadingFrame=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(),TEXT("ServerTravelLoading"));
    TravelLoadingFrame->SetBrushColor(FLinearColor(.015f,.018f,.019f,.94f));
    TravelLoadingFrame->SetPadding(FMargin(40));
    auto* LoadingSlot=Canvas->AddChildToCanvas(TravelLoadingFrame);
    LoadingSlot->SetAnchors(FAnchors(0,0,1,1));LoadingSlot->SetOffsets(FMargin(0));
    auto* Rows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    TravelLoadingFrame->SetContent(Rows);
    auto* Title=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Title->SetText(FText::FromString(TEXT("ANOMALIA'Z PRIGIMALIA  /  CONNEXION AU SERVEUR")));
    auto Font=Title->GetFont();Font.Size=27;Title->SetFont(Font);Rows->AddChildToVerticalBox(Title);
    TravelStatus=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(),TEXT("ServerTravelStatus"));
    TravelStatus->SetText(FText::FromString(TEXT("Préparation de la connexion...")));
    Rows->AddChildToVerticalBox(TravelStatus)->SetPadding(FMargin(0,24));
    auto* Progress=WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(),TEXT("ServerTravelActivity"));
    Progress->SetIsMarquee(true);Rows->AddChildToVerticalBox(Progress)->SetPadding(FMargin(0,18));
    auto* Warning=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Warning->SetText(FText::FromString(TEXT("Connexion en cours. La progression exacte sera fournie par le moteur réseau, pas simulée.")));
    Warning->SetAutoWrapText(true);Rows->AddChildToVerticalBox(Warning)->SetPadding(FMargin(0,10));
    TravelLoadingFrame->SetVisibility(ESlateVisibility::Collapsed);
}

void UAnomaliaZPrigimaliaSessionWidget::BuildLayout()
{
    if(!WidgetTree || WidgetTree->RootWidget) return;
    auto* Safe=WidgetTree->ConstructWidget<USafeZone>(USafeZone::StaticClass()); WidgetTree->RootWidget=Safe;
    auto* Canvas=WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass()); Safe->SetContent(Canvas);
    if(bMainMenu)
    {
        // Dedicated transient startup poster. T_MenuBackdrop remains available
        // to WorkForge only and is not substituted for the game's 3D menu.
        auto* Texture=LoadObject<UTexture2D>(nullptr,TEXT("/Game/AnomaliaZPrigimalia/Branding/T_StartupPoster.T_StartupPoster"),nullptr,LOAD_NoWarn);
        if(Texture)
        {
            auto* Matte=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());StartupArtworkFrame=Matte;Matte->SetBrushColor(FLinearColor::Black);Matte->SetPadding(FMargin(0));
            auto* BackdropCanvasSlot=Canvas->AddChildToCanvas(Matte);BackdropCanvasSlot->SetAnchors(FAnchors(0,0,1,1));BackdropCanvasSlot->SetOffsets(FMargin(0));
            auto* Fit=WidgetTree->ConstructWidget<UScaleBox>(UScaleBox::StaticClass());Fit->SetStretch(EStretch::ScaleToFit);Matte->SetContent(Fit);
            MenuArtwork=WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(),TEXT("SessionMenuArtwork"));
            MenuArtwork->SetBrushFromTexture(Texture,true);MenuArtwork->SetRenderTransformPivot(FVector2D(.5f,.5f));Fit->SetContent(MenuArtwork);
        }
    }
    auto* BuildLabel=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(),TEXT("SessionBuildIdentity"));
    BuildLabel->SetText(FText::FromString(TEXT("Build ")+FString(TEXT(ANOMALIA_BUILD_COMMIT)).Left(12)+TEXT(" · Terrain et forêt v3 · Développement")));
    auto BuildFont=BuildLabel->GetFont();BuildFont.Size=12;BuildLabel->SetFont(BuildFont);
    BuildLabel->SetAutoWrapText(true);BuildLabel->SetColorAndOpacity(FSlateColor(FLinearColor(.9f,.87f,.76f,1)));
    auto* BuildSlot=Canvas->AddChildToCanvas(BuildLabel);BuildSlot->SetAnchors(FAnchors(.035f,.95f,.96f,.99f));BuildSlot->SetOffsets(FMargin(0));
    // A narrow navigation rail keeps the actual 3D scene visible at the right.
    auto* Frame=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(),TEXT("SessionNavigation"));NavigationFrame=Frame; Frame->SetBrushColor(FLinearColor(.012f,.016f,.014f,.82f)); Frame->SetPadding(FMargin(20));
    auto* FrameSlot=Canvas->AddChildToCanvas(Frame); FrameSlot->SetAnchors(FAnchors(.035f,.12f,.31f,.77f)); FrameSlot->SetOffsets(FMargin(0));
    auto* Scroll=WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass()); Frame->SetContent(Scroll);
    auto* Rows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass()); Scroll->AddChild(Rows);
    auto Label=[&](const TCHAR* Text) { auto* L=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass()); L->SetText(FText::FromString(Text)); auto Font=L->GetFont(); Font.Size=16; L->SetFont(Font); L->SetAutoWrapText(true); Rows->AddChildToVerticalBox(L)->SetPadding(FMargin(0,6)); return L; };
    auto* Title=Label(TEXT("ANOMALIA")); auto TitleFont=Title->GetFont(); TitleFont.Size=36; Title->SetFont(TitleFont);
    Title->SetColorAndOpacity(FSlateColor(FLinearColor(.90,.87,.76,1)));
    Label(TEXT("ANOMALIA'Z PRIGIMALIA"));
    Label(bMainMenu?TEXT("SURVIVRE  ·  EXPLORER  ·  CONSTRUIRE"):TEXT("PARTIE EN PAUSE"));
    // Start and in-game pause are intentionally separate navigation contexts.
    auto Button=[&](const TCHAR* Name,const TCHAR* Text) {
        auto* Size=WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass()); Size->SetMinDesiredHeight(44);
        Rows->AddChildToVerticalBox(Size)->SetPadding(FMargin(0,4));
        auto* B=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),FName(Name)); Size->SetContent(B);
        B->SetBackgroundColor(FLinearColor(.08,.10,.085,1));
        auto* L=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass()); L->SetText(FText::FromString(Text));
        auto Font=L->GetFont(); Font.Size=18; L->SetFont(Font); B->SetContent(L); return B;
    };
    PlayButton=Button(TEXT("SessionPlay"),bMainMenu?TEXT("▶  JOUER"):TEXT("CONTINUER"));
    PlayButton->SetBackgroundColor(FLinearColor(.85f,.055f,.035f,1.f));
    PlayButton->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::Play);
    HomeButton=Button(TEXT("SessionHome"),bMainMenu?TEXT("PERSONNALISER / SURVIVANT"):TEXT("SURVIVANT"));
    HomeButton->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::ShowHome);
    OptionsButton=Button(TEXT("SessionOptions"),TEXT("OPTIONS")); OptionsButton->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::ShowOptions);
    if(bMainMenu)
    {
        ModsButton=Button(TEXT("SessionMods"),TEXT("WORKFORGE  •  MODS"));
        ModsButton->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::ShowMods);
        Button(TEXT("SessionWorldEditor"),TEXT("ÉDITEUR DE CARTE UE5"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::OpenWorldEditor);
    }
    else
    {
        Button(TEXT("SessionOnline"),TEXT("EN LIGNE  •  JOUEURS"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::ShowOnlinePlayers);
        Button(TEXT("SessionInvite"),TEXT("INVITER DES AMIS"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::ShowInviteFriends);
    }
    Button(TEXT("SessionSaveQuit"),TEXT("SAUVEGARDER ET QUITTER"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::SaveAndQuit);
    Button(TEXT("SessionQuit"),TEXT("QUITTER"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::Quit);
    Feedback=Label(bMainMenu?TEXT("Dernier survivant et emplacement sauvegardés."):TEXT("Partie mise en pause. Sauvegarde automatique active."));

    auto* Details=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(),TEXT("SessionDetailsFrame"));DetailsFrame=Details; Details->SetPadding(FMargin(24));
    Details->SetBrushColor(FLinearColor(.012,.016,.014,.80));
    auto* DetailsSlot=Canvas->AddChildToCanvas(Details); DetailsSlot->SetAnchors(FAnchors(.44,.48,.96,.94)); DetailsSlot->SetOffsets(FMargin(0));
    auto* DetailRows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());Details->SetContent(DetailRows);Rows=DetailRows;
    Button(TEXT("SessionClosePage"),TEXT("Retour au menu"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::ClosePage);
    auto* PageScroll=WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass());DetailRows->AddChildToVerticalBox(PageScroll);
    Pages=WidgetTree->ConstructWidget<UWidgetSwitcher>(UWidgetSwitcher::StaticClass(),TEXT("SessionPages")); PageScroll->AddChild(Pages);
    Rows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass()); Pages->AddChild(Rows);
    Label(TEXT("VOTRE SURVIVANT"));
    Label(TEXT("Jouer reprend votre personnage et votre inventaire dans la zone jouable.\nLes sauvegardes existantes sont conservées."));
    Label(TEXT("COMMANDES\nZ/W : avancer · Q/A/D : direction · souris : regard\nMaj : courir · E : interagir/entrer/sortir · I : inventaire\nEspace : sauter · R : dormir près du lit · V : caméra\nÉchap : pause · manette : sticks, A/Croix, X/Carré\nMenu : inventaire · View/Share : pause"));
    Label(TEXT("Version de développement · carte et contenu en construction"));
    Rows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass()); Pages->AddChild(Rows);
    Label(TEXT("OPTIONS DE LA PARTIE"));
    auto* Q=Button(TEXT("SessionQuality"),TEXT("Qualité : choisir un préréglage")); QualityLabel=Cast<UTextBlock>(Q->GetContent()); Q->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::ChangeQuality);
    Button(TEXT("SessionSave"),TEXT("Sauvegarder"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::Save);
    auto* Substances=Button(TEXT("SessionRPSubstances"),TEXT("Substances RP"));
    auto* Tobacco=Button(TEXT("SessionTobacco"),TEXT("Tabac"));
    auto* Alcohol=Button(TEXT("SessionAlcohol"),TEXT("Alcool"));
    ItemPolicyLabels={Cast<UTextBlock>(Substances->GetContent()),Cast<UTextBlock>(Tobacco->GetContent()),Cast<UTextBlock>(Alcohol->GetContent())};
    Substances->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::ToggleSubstances);
    Tobacco->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::ToggleTobacco);
    Alcohol->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::ToggleAlcohol);
    RefreshItemPolicyLabels();
    Rows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass()); Pages->AddChild(Rows);
    Label(TEXT("MODS LOCAUX"));
    Label(TEXT("Consultez les manifestes locaux et ouvrez leur dossier.\nLe téléchargement et l’activation de paquets tiers ne sont pas encore disponibles. Les mods DayZ ne sont pas compatibles avec Unreal Engine."));
    Button(TEXT("SessionRefreshMods"),TEXT("Actualiser la liste"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::RefreshMods);
    Button(TEXT("SessionOpenModsFolder"),TEXT("Ouvrir le dossier Mods"))->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::OpenModsFolder);
    ModRows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("SessionModRows")); Rows->AddChildToVerticalBox(ModRows);
    // WorkForge is NEVER constructed in gameplay pause or server browsing.
    if(bMainMenu)
    {
        BuildPremiumWorkshop(Canvas);
        BuildServerBrowser(Canvas);
        BuildTravelLoading(Canvas);
    }
    else BuildOnlinePlayers(Canvas);
    SelectPage(0);
    ClosePage();
}
void UAnomaliaZPrigimaliaSessionWidget::SelectPage(int32 Index)
{
    if(!Pages || Index<0 || Index>=Pages->GetChildrenCount()) return;
    Pages->SetActiveWidgetIndex(Index);
    if(WorkshopFrame) WorkshopFrame->SetVisibility(ESlateVisibility::Collapsed);
    if(ServerBrowserFrame) ServerBrowserFrame->SetVisibility(ESlateVisibility::Collapsed);
    if(OnlinePlayersFrame) OnlinePlayersFrame->SetVisibility(ESlateVisibility::Collapsed);
    FinishIntro();if(DetailsFrame)DetailsFrame->SetVisibility(ESlateVisibility::Visible);
    UButton* PageButtons[]={HomeButton.Get(),OptionsButton.Get(),ModsButton.Get()};
    for(int32 I=0;I<3;++I) if(PageButtons[I]) PageButtons[I]->SetBackgroundColor(I==Index?FLinearColor(.35f,.32f,.21f,1.f):FLinearColor(.08f,.10f,.085f,1.f));
}
void UAnomaliaZPrigimaliaSessionWidget::ClosePage() { if(DetailsFrame)DetailsFrame->SetVisibility(ESlateVisibility::Collapsed); }
void UAnomaliaZPrigimaliaSessionWidget::ShowHome() { SelectPage(0); }
void UAnomaliaZPrigimaliaSessionWidget::ShowOptions() { SelectPage(1); }
void UAnomaliaZPrigimaliaSessionWidget::ShowMods()
{
    if(!bMainMenu || !WorkshopFrame) return;
    // MODS exists only in the start menu, never during gameplay pause.
    bWorkshopMyModsOnly=false;
    RefreshMods(); SelectPage(2);
    if(DetailsFrame) DetailsFrame->SetVisibility(ESlateVisibility::Collapsed);
    if(WorkshopFrame) WorkshopFrame->SetVisibility(ESlateVisibility::Visible);
    RefreshWorkshop();
}
void UAnomaliaZPrigimaliaSessionWidget::RefreshMods()
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
        FString Json,Error; FAnomaliaZPrigimaliaModManifest Manifest;
        const int64 Bytes=IFileManager::Get().FileSize(*File);
        if(Bytes<0 || Bytes>256*1024 || !FFileHelper::LoadFileToString(Json,*File) ||
           !FJsonObjectConverter::JsonObjectStringToUStruct(Json,&Manifest,0,0))
        { AddRow(Folder+TEXT(" — manifeste illisible")); continue; }
        if(!UAnomaliaZPrigimaliaModResolver::ValidateModManifest(Manifest,Error))
        { AddRow(Folder+TEXT(" — déclaration rejetée : ")+Error); continue; }
        // Manifest validation does not authenticate a package or mount it into the game.
        AddRow(Manifest.Id+TEXT(" · ")+Manifest.Version+TEXT("\nManifeste reconnu · paquet non vérifié · inactif"));
    }
    if(Count==0) AddRow(TEXT("Aucun manifeste local. Aucun mod tiers activé."));
}
void UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterAll(){ bWorkshopMyModsOnly=false; if(WorkshopCategory) WorkshopCategory->SetSelectedOption(TEXT("Tous")); RefreshWorkshop(); }
void UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterVehicles(){ bWorkshopMyModsOnly=false; if(WorkshopCategory) WorkshopCategory->SetSelectedOption(TEXT("Véhicules")); RefreshWorkshop(); }
void UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterWeapons(){ bWorkshopMyModsOnly=false; if(WorkshopCategory) WorkshopCategory->SetSelectedOption(TEXT("Armes")); RefreshWorkshop(); }
void UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterBuildings(){ bWorkshopMyModsOnly=false; if(WorkshopCategory) WorkshopCategory->SetSelectedOption(TEXT("Bâtiments")); RefreshWorkshop(); }
void UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterCreatures(){ bWorkshopMyModsOnly=false; if(WorkshopCategory) WorkshopCategory->SetSelectedOption(TEXT("Créatures")); RefreshWorkshop(); }
void UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterSurvival(){ bWorkshopMyModsOnly=false; if(WorkshopCategory) WorkshopCategory->SetSelectedOption(TEXT("Survie")); RefreshWorkshop(); }
void UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterMaps(){ bWorkshopMyModsOnly=false; if(WorkshopCategory) WorkshopCategory->SetSelectedOption(TEXT("Cartes")); RefreshWorkshop(); }
void UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterGameplay(){ bWorkshopMyModsOnly=false; if(WorkshopCategory) WorkshopCategory->SetSelectedOption(TEXT("Gameplay")); RefreshWorkshop(); }
void UAnomaliaZPrigimaliaSessionWidget::WorkshopFilterTools(){ bWorkshopMyModsOnly=false; if(WorkshopCategory) WorkshopCategory->SetSelectedOption(TEXT("Outils")); RefreshWorkshop(); }
void UAnomaliaZPrigimaliaSessionWidget::WorkshopShowMyMods()
{
    bWorkshopMyModsOnly=true;
    if(WorkshopSearch) WorkshopSearch->SetText(FText::GetEmpty());
    if(WorkshopCategory) WorkshopCategory->SetSelectedOption(TEXT("Tous"));
    RefreshWorkshop();
}
void UAnomaliaZPrigimaliaSessionWidget::WorkshopShowCatalogue()
{
    bWorkshopMyModsOnly=false;
    if(WorkshopSearch) WorkshopSearch->SetText(FText::GetEmpty());
    if(WorkshopCategory) WorkshopCategory->SetSelectedOption(TEXT("Tous"));
    RefreshWorkshop();
}
void UAnomaliaZPrigimaliaSessionWidget::WorkshopShowCategories()
{
    bWorkshopMyModsOnly=false;
    RefreshWorkshop();
    if(WorkshopCategory && GetOwningPlayer()) WorkshopCategory->SetUserFocus(GetOwningPlayer());
}
void UAnomaliaZPrigimaliaSessionWidget::WorkshopShowCollections()
{
    if(WorkshopStatus) WorkshopStatus->SetText(FText::FromString(
        TEXT("Collections : aucune collection communautaire publiée par un service connecté. Les créations locales restent visibles dans Mods.")));
}
void UAnomaliaZPrigimaliaSessionWidget::WorkshopShowCommunity()
{
    if(WorkshopStatus) WorkshopStatus->SetText(FText::FromString(
        TEXT("Communauté non connectée : discussions et avis indisponibles. Aucun nombre ni avis fictif ne sera affiché.")));
}
void UAnomaliaZPrigimaliaSessionWidget::WorkshopShowDownloads()
{
    if(WorkshopStatus) WorkshopStatus->SetText(FText::FromString(
        TEXT("Téléchargements : aucun gestionnaire de paquets UE5 authentifiés n'est encore connecté. Ouvrez le dossier Mods pour consulter les manifestes.")));
}
void UAnomaliaZPrigimaliaSessionWidget::WorkshopShowSettings()
{
    ShowOptions();
}
void UAnomaliaZPrigimaliaSessionWidget::WorkshopOpenLocalModsFolder()
{
    OpenModsFolder();
    if(WorkshopStatus) WorkshopStatus->SetText(FText::FromString(
        TEXT("Ouverture du dossier des manifestes locaux demandée. Les paquets non authentifiés restent inactifs.")));
}

void UAnomaliaZPrigimaliaSessionWidget::CloseWorkshop()
{
    if(WorkshopFrame) WorkshopFrame->SetVisibility(ESlateVisibility::Collapsed);
    if(DetailsFrame) DetailsFrame->SetVisibility(ESlateVisibility::Collapsed);
    if(ModsButton) ModsButton->SetUserFocus(GetOwningPlayer());
}
void UAnomaliaZPrigimaliaSessionWidget::WorkshopSearchChanged(const FText&)
{
    if(WorkshopFrame && WorkshopFrame->GetVisibility()==ESlateVisibility::Visible) RefreshWorkshop();
}
void UAnomaliaZPrigimaliaSessionWidget::WorkshopCategoryChanged(FString,ESelectInfo::Type)
{
    if(WorkshopFrame && WorkshopFrame->GetVisibility()==ESlateVisibility::Visible) RefreshWorkshop();
}
void UAnomaliaZPrigimaliaSessionWidget::OpenWorkshopTools()
{
#if PLATFORM_WINDOWS
    // Secondary action only. The actual Workshop UI runs inside UE5.
    FPlatformProcess::LaunchURL(TEXT("anomalia-tools://workshop"),nullptr,nullptr);
    if(WorkshopStatus) WorkshopStatus->SetText(FText::FromString(TEXT("Ouverture d’ANOMALIA Tools demandée (si installé sur Windows).")));
#else
    if(WorkshopStatus) WorkshopStatus->SetText(FText::FromString(TEXT("ANOMALIA Tools est disponible pour Windows.")));
#endif
}
void UAnomaliaZPrigimaliaSessionWidget::OpenWorkshopHosting()
{
    FPlatformProcess::LaunchURL(TEXT("https://cmd-hosting-web-production.up.railway.app/#cmdMods"),nullptr,nullptr);
    if(WorkshopStatus) WorkshopStatus->SetText(FText::FromString(TEXT("Page CMD Hosting ouverte dans votre navigateur. Installation serveur non disponible.")));
}
void UAnomaliaZPrigimaliaSessionWidget::RefreshWorkshop()
{
    if(!WorkshopCards || !WorkshopStatus || !WidgetTree)return;
    WorkshopCards->ClearChildren();

    struct FWorkForgeCard
    {
        FString Id, Name, Author, Category, Version, Description, Preview;
        bool bLocalTools=false;
        bool bInstalledManifest=false;
    };
    TArray<FWorkForgeCard> Entries;
    const FString Search=WorkshopSearch?WorkshopSearch->GetText().ToString().TrimStartAndEnd():TEXT("");
    const FString Filter=WorkshopCategory?WorkshopCategory->GetSelectedOption():TEXT("Tous");
    const FString Sort=WorkshopSort?WorkshopSort->GetSelectedOption():TEXT("Récents");
    const auto Matches=[&](const FWorkForgeCard& Item)
    {
        return (!bWorkshopMyModsOnly || Item.bInstalledManifest) &&
          (Filter.IsEmpty() || Filter==TEXT("Tous") || Filter.Equals(Item.Category,ESearchCase::IgnoreCase)) &&
          (Search.IsEmpty() || Item.Name.Contains(Search,ESearchCase::IgnoreCase) ||
            Item.Category.Contains(Search,ESearchCase::IgnoreCase) ||
            Item.Description.Contains(Search,ESearchCase::IgnoreCase) ||
            Item.Author.Contains(Search,ESearchCase::IgnoreCase));
    };
    // Real data only. Never invent subscribers, downloads, ratings, authors or published mods.
#if PLATFORM_WINDOWS
    const FString AppData=FPlatformMisc::GetEnvironmentVariable(TEXT("APPDATA"));
    const TArray<FString> Workspaces={
        FPaths::Combine(AppData,TEXT("ANOMALIA Tools"),TEXT("private-workspaces")),
        FPaths::Combine(AppData,TEXT("anomalia-tools"),TEXT("private-workspaces"))
    };
    for(const FString& Workspace:Workspaces)
    {
        if(AppData.IsEmpty() || !IFileManager::Get().DirectoryExists(*Workspace))continue;
        TArray<FString> Folders;IFileManager::Get().FindFiles(Folders,*(Workspace/TEXT("*")),false,true);
        Folders.Sort();int32 Scanned=0;
        for(const FString& Folder:Folders)
        {
            if(++Scanned>500 || Entries.Num()>=180)break;
            if(Folder.Len()<2 || Folder.Len()>100 || Folder==TEXT("_workshop"))continue;
            bool ValidId=true;
            for(const TCHAR C:Folder)
                if(!((C>=TEXT('a') && C<=TEXT('z')) || (C>=TEXT('0') && C<=TEXT('9')) || C==TEXT('-')))
                    {ValidId=false;break;}
            if(!ValidId)continue;
            const FString File=FPaths::Combine(Workspace,Folder,TEXT("Config/workshop.json"));
            const int64 Size=IFileManager::Get().FileSize(*File);
            if(Size<=0 || Size>64*1024)continue;
            FString Data;if(!FFileHelper::LoadFileToString(Data,*File))continue;
            TSharedPtr<FJsonObject> Json;
            if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Data),Json) || !Json.IsValid())continue;
            FWorkForgeCard Card;
            FString Schema;
            if(!Json->TryGetStringField(TEXT("schema"),Schema) || Schema!=TEXT("anomalia-workshop-entry") ||
                !Json->TryGetStringField(TEXT("projectId"),Card.Id) || Card.Id!=Folder ||
                !Json->TryGetStringField(TEXT("title"),Card.Name) || Card.Name.IsEmpty())continue;
            Json->TryGetStringField(TEXT("category"),Card.Category);
            Json->TryGetStringField(TEXT("description"),Card.Description);
            Json->TryGetStringField(TEXT("modVersion"),Card.Version);
            Card.Name=Card.Name.Left(90);
            Card.Category=Card.Category.Left(35);
            Card.Description=Card.Description.Left(280);
            Card.Version=Card.Version.Left(32);
            Card.Author=TEXT("Votre création");
            Card.bLocalTools=true;
            Entries.Add(MoveTemp(Card));
        }
        break;
    }
#endif
    const FString Root=FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("Mods"));
    TArray<FString> Folders;IFileManager::Get().FindFiles(Folders,*(Root/TEXT("*")),false,true);Folders.Sort();
    int32 Scanned=0;
    for(const FString& Folder:Folders)
    {
        if(++Scanned>200 || Entries.Num()>=300)break;
        const FString File=FPaths::Combine(Root,Folder,TEXT("manifest.json"));
        const int64 Size=IFileManager::Get().FileSize(*File);
        if(Size<=0 || Size>256*1024)continue;
        FString Json,Error;FAnomaliaZPrigimaliaModManifest Manifest;
        if(!FFileHelper::LoadFileToString(Json,*File) ||
            !FJsonObjectConverter::JsonObjectStringToUStruct(Json,&Manifest,0,0) ||
            !UAnomaliaZPrigimaliaModResolver::ValidateModManifest(Manifest,Error))continue;
        FWorkForgeCard Card;
        Card.Id=Manifest.Id.Left(100);
        Card.Name=Manifest.Id.Left(90);
        Card.Version=Manifest.Version.Left(32);
        Card.Author=TEXT("Manifeste local");
        Card.bInstalledManifest=true;
        Card.Category=TEXT("Autres");
        Card.Description=TEXT("Fichier de mod local validé. Ce mod n'est pas encore chargé dans UE5.");
        Entries.Add(MoveTemp(Card));
    }
    const int32 Total=Entries.Num();
    int32 WorkspacesCount=0;
    int32 InstalledCount=0;
    for(const FWorkForgeCard& Card:Entries)
    {
        if(Card.bLocalTools) ++WorkspacesCount;
        if(Card.bInstalledManifest) ++InstalledCount;
    }
    if(WorkshopCountLabel) WorkshopCountLabel->SetText(FText::AsNumber(InstalledCount));
    if(WorkshopCreatorsLabel) WorkshopCreatorsLabel->SetText(FText::AsNumber(WorkspacesCount));
    if(WorkshopInstalledLabel) WorkshopInstalledLabel->SetText(FText::FromString(
        FString::Printf(TEXT("Manifestes locaux       %d"),InstalledCount)));
    const TCHAR* CategoryKeys[]={TEXT("Tous"),TEXT("Véhicules"),TEXT("Créatures"),
        TEXT("Bâtiments"),TEXT("Cartes"),TEXT("Armes"),TEXT("Survie"),
        TEXT("Gameplay"),TEXT("Outils")};
    for(int32 Cat=0;Cat<9 && Cat<WorkshopCategoryCountLabels.Num();++Cat)
    {
        int32 Count=0;
        for(const FWorkForgeCard& Entry:Entries)
            if(Cat==0 || Entry.Category.Equals(CategoryKeys[Cat],ESearchCase::IgnoreCase))
                ++Count;
        if(WorkshopCategoryCountLabels[Cat])
            WorkshopCategoryCountLabels[Cat]->SetText(FText::FromString(
                FString::Printf(TEXT("%d mod(s) locaux"),Count)));
    }
    TArray<FWorkForgeCard> Visible;
    for(const FWorkForgeCard& Card:Entries)if(Matches(Card))Visible.Add(Card);
    if(Sort==TEXT("Nom A-Z"))
        Visible.Sort([](const FWorkForgeCard& A,const FWorkForgeCard& B){return A.Name < B.Name;});
    else if(Sort==TEXT("Catégorie"))
        Visible.Sort([](const FWorkForgeCard& A,const FWorkForgeCard& B){return A.Category==B.Category ? A.Name<B.Name : A.Category<B.Category;});
    else if(Sort==TEXT("Version"))
        Visible.Sort([](const FWorkForgeCard& A,const FWorkForgeCard& B){return A.Version>B.Version;});

    const FLinearColor Red(.77f,.045f,.025f,1.f),Gold(1.f,.80f,.63f,1.f),Soft(.82f,.84f,.88f,1.f);
    auto* DefaultArt=LoadObject<UTexture2D>(nullptr,TEXT("/Game/AnomaliaZPrigimalia/WorkForge/Artwork/T_WFModCardFallback.T_WFModCardFallback"),nullptr,LOAD_NoWarn);
    if(!DefaultArt) DefaultArt=LoadObject<UTexture2D>(nullptr,TEXT("/Game/AnomaliaZPrigimalia/Branding/T_MenuBackdrop.T_MenuBackdrop"),nullptr,LOAD_NoWarn);
    auto Text=[&](const FString& Caption,int32 Size,const FLinearColor& Color)
    {
        auto* Label=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        Label->SetText(FText::FromString(Caption));Label->SetAutoWrapText(true);
        auto Font=Label->GetFont();Font.Size=Size;Label->SetFont(Font);
        Label->SetColorAndOpacity(FSlateColor(Color));
        return Label;
    };
    // Cards are genuine Slate/UMG widgets, not a screenshot or flattened mock-up.
    for(int32 Index=0;Index<Visible.Num();Index+=4)
    {
        auto* CardsRow=WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
        WorkshopCards->AddChildToVerticalBox(CardsRow)->SetPadding(FMargin(4,5));
        for(int32 Col=0;Col<4;++Col)
        {
            if(Index+Col>=Visible.Num())break;
            const FWorkForgeCard& Entry=Visible[Index+Col];
            auto* Card=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
            Card->SetPadding(FMargin(1));
            Card->SetBrushColor(FLinearColor(.34f,.12f,.09f,.98f));
            auto* CardSlot=CardsRow->AddChildToHorizontalBox(Card);
            CardSlot->SetPadding(FMargin(5,3));
            CardSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
            auto* Content=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
            Card->SetContent(Content);
            auto* Art=WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
            auto* ImageHeight=WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
            ImageHeight->SetHeightOverride(145.f);
            Content->AddChildToVerticalBox(ImageHeight);
            ImageHeight->SetContent(Art);
            if(DefaultArt)
            {
                auto* Image=WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
                Image->SetBrushFromTexture(DefaultArt,true);
                Image->SetColorAndOpacity(FLinearColor(1.f,1.f,1.f,.95f));
                Art->AddChildToOverlay(Image);
            }
            auto* Shade=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
            Shade->SetBrushColor(FLinearColor(.035f,.022f,.026f,.58f));
            auto* ShadeContent=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
            Shade->SetContent(ShadeContent);
            Art->AddChildToOverlay(Shade);
            ShadeContent->AddChildToVerticalBox(Text(Entry.Category.IsEmpty()?TEXT("MOD ANOMALIA"):Entry.Category.ToUpper(),12,Gold))->SetPadding(FMargin(10,5));
            ShadeContent->AddChildToVerticalBox(Text(Entry.Name,16,FLinearColor::White))->SetPadding(FMargin(10,25,10,0));

            auto* DetailPanel=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
            DetailPanel->SetBrushColor(FLinearColor(.045f,.047f,.060f,.99f));
            DetailPanel->SetPadding(FMargin(12,8));
            Content->AddChildToVerticalBox(DetailPanel);
            auto* Details=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
            DetailPanel->SetContent(Details);
            Details->AddChildToVerticalBox(Text(TEXT("Par ")+Entry.Author,11,Soft))->SetPadding(FMargin(0,2));
            Details->AddChildToVerticalBox(Text(Entry.Description.IsEmpty()?TEXT("Mod ANOMALIA"):Entry.Description,12,Gold))->SetPadding(FMargin(0,3));
            Details->AddChildToVerticalBox(Text(TEXT("Version : ")+Entry.Version,11,Soft))->SetPadding(FMargin(0,4));
            auto* Footer=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),
                FName(*FString::Printf(TEXT("WorkshopModAction%d"),Index+Col)));
            Footer->SetBackgroundColor(Red);
            Footer->SetContent(Text(Entry.bLocalTools?
                TEXT("OUVRIR ANOMALIA TOOLS  ↗"):TEXT("OUVRIR DOSSIER MODS  ↗"),
                12,FLinearColor::White));
            if(Entry.bLocalTools)
                Footer->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::OpenWorkshopTools);
            else
                Footer->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopOpenLocalModsFolder);
            Details->AddChildToVerticalBox(Footer)->SetPadding(FMargin(0,7,0,1));
        }
    }
    WorkshopStatus->SetText(FText::FromString(FString::Printf(
        TEXT("MODS • %d manifeste(s) et création(s) locale(s) • %d affiché(s) • Communauté non connectée • Aucun paquet tiers activé%s"),
        Total,Visible.Num(),bWorkshopMyModsOnly?TEXT(" • Vue : Mes mods"):TEXT(""))));
    if(Visible.IsEmpty())
    {
        auto* Empty=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
        Empty->SetBrushColor(FLinearColor(.17f,.065f,.060f,.90f));
        Empty->SetPadding(FMargin(16));
        WorkshopCards->AddChildToVerticalBox(Empty)->SetPadding(FMargin(5,4));
        auto* EmptyContent=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
        Empty->SetContent(EmptyContent);
        EmptyContent->AddChildToVerticalBox(Text(
            TEXT("AUCUN MOD DISPONIBLE POUR CETTE SÉLECTION\n\nLes mods locaux vérifiés et les créations ANOMALIA Tools apparaîtront ici.\nLe catalogue communautaire n'est pas encore connecté."),15,Gold));
        auto* OpenFolder=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),TEXT("WorkshopEmptyOpenFolder"));
        OpenFolder->SetBackgroundColor(Red);
        OpenFolder->SetContent(Text(TEXT("OUVRIR LE DOSSIER MODS"),13,FLinearColor::White));
        OpenFolder->OnClicked.AddDynamic(this,&UAnomaliaZPrigimaliaSessionWidget::WorkshopOpenLocalModsFolder);
        EmptyContent->AddChildToVerticalBox(OpenFolder)->SetPadding(FMargin(0,12,0,4));
    }
}

void UAnomaliaZPrigimaliaSessionWidget::OpenModsFolder()
{
    const FString Root=FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("Mods")));
    if(IFileManager::Get().MakeDirectory(*Root,true)) FPlatformProcess::ExploreFolder(*Root);
    else if(Feedback) Feedback->SetText(FText::FromString(TEXT("Impossible d’ouvrir le dossier Mods.")));
}
void UAnomaliaZPrigimaliaSessionWidget::OpenWorldEditor()
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
    const FString Launcher=Root/TEXT("bootstrap/Launch-AnomaliaZPrigimaliaUE5.vbs");
    if(Valid && FPaths::FileExists(Launcher) && FPlatformProcess::LaunchFileInDefaultExternalApplication(*Launcher))
    { if(Feedback) Feedback->SetText(FText::FromString(TEXT("Ouverture du projet synchronisé dans Unreal Editor. Votre partie reste en pause."))); return; }
#endif
    if(Feedback) Feedback->SetText(FText::FromString(TEXT("Le projet Unreal synchronisé n’est pas disponible. Attendez la fin de la mise à jour de l’éditeur.")));
}
void UAnomaliaZPrigimaliaSessionWidget::ShowServerBrowser()
{
    if(!bMainMenu || !ServerBrowserFrame) return;
    FinishIntro();ClosePage();
    if(WorkshopFrame) WorkshopFrame->SetVisibility(ESlateVisibility::Collapsed);
    if(NavigationFrame) NavigationFrame->SetVisibility(ESlateVisibility::Collapsed);
    ServerBrowserFrame->SetVisibility(ESlateVisibility::Visible);
    if(ServerSearch) ServerSearch->SetText(FText::GetEmpty());
    RefreshServerBrowser();
    if(ServerSelect && GetOwningPlayer()) ServerSelect->SetUserFocus(GetOwningPlayer());
}
void UAnomaliaZPrigimaliaSessionWidget::CloseServerBrowser()
{
    if(ServerBrowserFrame) ServerBrowserFrame->SetVisibility(ESlateVisibility::Collapsed);
    if(NavigationFrame) NavigationFrame->SetVisibility(ESlateVisibility::Visible);
    if(PlayButton && GetOwningPlayer()) PlayButton->SetUserFocus(GetOwningPlayer());
}
void UAnomaliaZPrigimaliaSessionWidget::TabOfficialServers(){ServerCategory=TEXT("Officiel");RefreshServerBrowser();}
void UAnomaliaZPrigimaliaSessionWidget::TabCommunityServers(){ServerCategory=TEXT("Communautaire");RefreshServerBrowser();}
void UAnomaliaZPrigimaliaSessionWidget::TabFavoriteServers(){ServerCategory=TEXT("Favoris");RefreshServerBrowser();}
void UAnomaliaZPrigimaliaSessionWidget::ServerSearchChanged(const FText&){RefreshServerBrowser();}
void UAnomaliaZPrigimaliaSessionWidget::ServerSelectionChanged(FString SelectedItem,ESelectInfo::Type)
{
    SelectedServerId.Empty();
    for(const FServerBrowserEntry& Row:ServerEntries)
    {
        const FString Option=Row.Name+TEXT("  |  ")+Row.Map+TEXT("  |  ")+Row.Address;
        if(SelectedItem==Option)
        {
            SelectedServerId=Row.Id;
            if(ServerStatus) ServerStatus->SetText(FText::FromString(
                FString::Printf(TEXT("%s\nCarte : %s\nCatégorie : %s\nJoueurs : non vérifiés\nConnexion : %s"),
                    *Row.Name,*Row.Map,*Row.Category,*Row.Address)));
            break;
        }
    }
}
void UAnomaliaZPrigimaliaSessionWidget::RefreshServerBrowser()
{
    if(!ServerSelect || !ServerResults || !ServerStatus) return;
    // No invented servers, player counts or ping. A trusted local service
    // may write this bounded config with each host:port and category.
    ServerEntries.Reset();
    const FString File=FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("ServerBrowser"),TEXT("servers.json"));
    FString Raw;TSharedPtr<FJsonObject> Root;
    if(IFileManager::Get().FileExists(*File) &&
        IFileManager::Get().FileSize(*File)>0 &&
        IFileManager::Get().FileSize(*File)<=256*1024 &&
        FFileHelper::LoadFileToString(Raw,*File) &&
        FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw),Root) && Root.IsValid())
    {
        const TArray<TSharedPtr<FJsonValue>>* Items=nullptr;
        if(Root->TryGetArrayField(TEXT("servers"),Items) && Items)
        {
            for(const auto& Value:*Items)
            {
                if(ServerEntries.Num()>=128) break;
                const TSharedPtr<FJsonObject> Item=Value.IsValid()?Value->AsObject():nullptr;
                if(!Item.IsValid()) continue;
                FServerBrowserEntry Entry;
                if(!Item->TryGetStringField(TEXT("id"),Entry.Id) || Entry.Id.Len()<1 || Entry.Id.Len()>64) continue;
                if(!Item->TryGetStringField(TEXT("name"),Entry.Name) || Entry.Name.IsEmpty() || Entry.Name.Len()>96) continue;
                if(!Item->TryGetStringField(TEXT("address"),Entry.Address) || Entry.Address.Len()>260) continue;
                Item->TryGetStringField(TEXT("map"),Entry.Map);
                if(Entry.Map.IsEmpty())Entry.Map=TEXT("Carte non renseignée");
                Entry.Map=Entry.Map.Left(65);
                Item->TryGetStringField(TEXT("category"),Entry.Category);
                if(!Entry.Category.Equals(TEXT("Officiel"),ESearchCase::IgnoreCase) &&
                    !Entry.Category.Equals(TEXT("Communautaire"),ESearchCase::IgnoreCase)) continue;
                Item->TryGetBoolField(TEXT("favorite"),Entry.bFavorite);
                // Strict URL sanitation: no commands, embedded options, paths,
                // userinfo, Unicode spoofing or extra colons. Only host:port.
                FString Host,Port;
                if(!Entry.Address.Split(TEXT(":"),&Host,&Port,ESearchCase::CaseSensitive,ESearchDir::FromEnd) ||
                    Host.IsEmpty() || Host.Len()>253 || !Port.IsNumeric() ||
                    Port.Len()>5 || FCString::Atoi(*Port)<1 || FCString::Atoi(*Port)>65535) continue;
                bool bHostValid=true;
                for(const TCHAR Ch:Host)
                    if(!FChar::IsAlnum(Ch) && Ch!='.' && Ch!='-') {bHostValid=false;break;}
                if(!bHostValid || Host.Contains(TEXT(":")))continue;
                ServerEntries.Add(Entry);
            }
        }
    }
    const FString Query=ServerSearch?ServerSearch->GetText().ToString().TrimStartAndEnd():TEXT("");
    ServerSelect->ClearOptions();
    ServerResults->ClearChildren();
    int32 Matches=0;
    for(const FServerBrowserEntry& Entry:ServerEntries)
    {
        if(ServerCategory==TEXT("Favoris") ? !Entry.bFavorite :
            !Entry.Category.Equals(ServerCategory,ESearchCase::IgnoreCase)) continue;
        if(!Query.IsEmpty() && !Entry.Name.Contains(Query,ESearchCase::IgnoreCase) &&
            !Entry.Map.Contains(Query,ESearchCase::IgnoreCase)) continue;
        const FString Option=Entry.Name+TEXT("  |  ")+Entry.Map+TEXT("  |  ")+Entry.Address;
        ServerSelect->AddOption(Option);
        auto* Row=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        Row->SetText(FText::FromString(FString::Printf(TEXT("%s  ·  %s  ·  joueurs non vérifiés"),
            *Entry.Name,*Entry.Map)));
        Row->SetColorAndOpacity(FSlateColor(FLinearColor(.89f,.91f,.93f,1.f)));
        Row->SetAutoWrapText(true);
        ServerResults->AddChildToVerticalBox(Row)->SetPadding(FMargin(4,8));
        ++Matches;
    }
    SelectedServerId.Empty();
    if(Matches)
    {
        ServerSelect->SetSelectedIndex(0);
        ServerSelectionChanged(ServerSelect->GetSelectedOption(),ESelectInfo::Direct);
    }
    else
    {
        auto* Empty=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        Empty->SetText(FText::FromString(TEXT(
            "Aucun serveur enregistré dans cet onglet.\n"
            "Source de liste : Saved/ServerBrowser/servers.json\n"
            "Aucun serveur officiel ou communautaire fictif n'est affiché.")));
        Empty->SetAutoWrapText(true);
        Empty->SetColorAndOpacity(FSlateColor(FLinearColor(.88f,.86f,.84f,1.f)));
        ServerResults->AddChildToVerticalBox(Empty);
        ServerStatus->SetText(FText::FromString(
            TEXT("Liste vide. Les connexions et joueurs doivent être vérifiés auprès d'un véritable serveur.")));
    }
}
void UAnomaliaZPrigimaliaSessionWidget::JoinSelectedServer()
{
    if(!bMainMenu || SelectedServerId.IsEmpty())return;
    for(const FServerBrowserEntry& Entry:ServerEntries)
    {
        if(Entry.Id!=SelectedServerId)continue;
        auto* PC=GetOwningPlayer();if(!PC||!TravelLoadingFrame)return;
        const FString Address=Entry.Address; // Already strict-validated on loading.
        if(ServerBrowserFrame) ServerBrowserFrame->SetVisibility(ESlateVisibility::Collapsed);
        if(NavigationFrame) NavigationFrame->SetVisibility(ESlateVisibility::Collapsed);
        TravelLoadingFrame->SetVisibility(ESlateVisibility::Visible);
        if(TravelStatus)TravelStatus->SetText(FText::FromString(
            FString::Printf(TEXT("Connexion à %s (%s) ..."),*Entry.Name,*Address)));
        UGameplayStatics::SetGamePaused(PC,false);
        TWeakObjectPtr<APlayerController> WeakPC=PC;
        if(UWorld* World=GetWorld())
        {
            FTimerHandle Handle;
            World->GetTimerManager().SetTimer(Handle,FTimerDelegate::CreateWeakLambda(this,
                [WeakPC,Address]()
                {
                    if(WeakPC.IsValid())
                    {
                        WeakPC->SetInputMode(FInputModeGameOnly());
                        WeakPC->bShowMouseCursor=false;
                        WeakPC->ClientTravel(Address,TRAVEL_Absolute);
                    }
                }),.3f,false);
        }
        return;
    }
}
void UAnomaliaZPrigimaliaSessionWidget::ShowOnlinePlayers()
{
    if(bMainMenu||!OnlinePlayersFrame)return;
    ClosePage();
    if(NavigationFrame)NavigationFrame->SetVisibility(ESlateVisibility::Collapsed);
    OnlinePlayersFrame->SetVisibility(ESlateVisibility::Visible);
    RefreshOnlinePlayers();
}
void UAnomaliaZPrigimaliaSessionWidget::CloseOnlinePlayers()
{
    if(OnlinePlayersFrame)OnlinePlayersFrame->SetVisibility(ESlateVisibility::Collapsed);
    if(NavigationFrame)NavigationFrame->SetVisibility(ESlateVisibility::Visible);
}
void UAnomaliaZPrigimaliaSessionWidget::RefreshOnlinePlayers()
{
    if(!OnlinePlayerRows)return;
    OnlinePlayerRows->ClearChildren();
    int32 Count=0;
    const AGameStateBase* GameState=GetWorld()?GetWorld()->GetGameState<AGameStateBase>():nullptr;
    if(GameState)
    {
        for(APlayerState* Player:GameState->PlayerArray)
        {
            if(!IsValid(Player)||Count>=64)continue;
            FString Name=Player->GetPlayerName().TrimStartAndEnd();
            if(Name.IsEmpty())Name=TEXT("Joueur sans nom");
            auto* Line=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
            Line->SetText(FText::FromString(Name.Left(70)));
            Line->SetColorAndOpacity(FSlateColor(FLinearColor::White));
            OnlinePlayerRows->AddChildToVerticalBox(Line)->SetPadding(FMargin(0,8));
            ++Count;
        }
    }
    if(Count==0)
    {
        auto* None=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        None->SetText(FText::FromString(TEXT(
            "Aucun joueur répliqué par la session en cours.\n"
            "La liste est lue depuis Unreal GameState, sans pseudo fictif.")));
        None->SetAutoWrapText(true);
        OnlinePlayerRows->AddChildToVerticalBox(None);
    }
}
void UAnomaliaZPrigimaliaSessionWidget::ShowInviteFriends()
{
    if(Feedback)Feedback->SetText(FText::FromString(TEXT(
        "Invitations : aucune plateforme d'amis (Steam / Xbox / PSN) n'est encore connectée. "
        "Le jeu ne prétend pas avoir envoyé d'invitation.")));
}
void UAnomaliaZPrigimaliaSessionWidget::Play()
{
    if(bMainMenu){ ShowServerBrowser();return; }
    ResumeLocalSession();
}
void UAnomaliaZPrigimaliaSessionWidget::ResumeLocalSession()
{
    FinishIntro();
    auto* PC=GetOwningPlayer(); if(!PC) return;
    RemoveFromParent(); UGameplayStatics::SetGamePaused(PC,false);
    PC->SetInputMode(FInputModeGameOnly()); PC->bShowMouseCursor=false;
}
void UAnomaliaZPrigimaliaSessionWidget::ChangeQuality()
{
    Quality=(Quality+1)%3;
    const TArray<FString> Profiles={TEXT("Performance_Fallback"),TEXT("PC_Medium"),TEXT("PC_High")};
    const TCHAR* Names[]={TEXT("faible"),TEXT("moyenne"),TEXT("élevée")};
    const bool OK=UAnomaliaZPrigimaliaPerformanceLibrary::ApplyGraphicsPreset(Profiles[Quality]);
    if(QualityLabel) QualityLabel->SetText(FText::FromString(FString(TEXT("Qualité : "))+Names[Quality]+TEXT(" (changer)")));
    if(Feedback) Feedback->SetText(FText::FromString(OK?TEXT("Réglages graphiques locaux appliqués."):TEXT("Impossible d’appliquer ces réglages.")));
}
void UAnomaliaZPrigimaliaSessionWidget::Save()
{
    auto* Mode=GetWorld()?GetWorld()->GetAuthGameMode<AAnomaliaZPrigimaliaGameMode>():nullptr;
    const bool OK=Mode && Mode->SaveLocalGame();
    if(Feedback) Feedback->SetText(FText::FromString(OK?TEXT("Personnage et inventaire sauvegardés."):TEXT("Sauvegarde non confirmée : opération en cours ou erreur de stockage.")));
}
void UAnomaliaZPrigimaliaSessionWidget::SaveAndQuit()
{
    auto* Mode=GetWorld()?GetWorld()->GetAuthGameMode<AAnomaliaZPrigimaliaGameMode>():nullptr;
    if(Mode && Mode->SaveLocalGame()) Quit();
    else if(Feedback) Feedback->SetText(FText::FromString(TEXT("Sauvegarde non confirmée. La partie reste ouverte.")));
}
void UAnomaliaZPrigimaliaSessionWidget::Quit() { UKismetSystemLibrary::QuitGame(this,GetOwningPlayer(),EQuitPreference::Quit,false); }
void UAnomaliaZPrigimaliaSessionWidget::ToggleSubstances() { ToggleItemPolicy(0); }
void UAnomaliaZPrigimaliaSessionWidget::ToggleTobacco() { ToggleItemPolicy(1); }
void UAnomaliaZPrigimaliaSessionWidget::ToggleAlcohol() { ToggleItemPolicy(2); }
void UAnomaliaZPrigimaliaSessionWidget::RefreshItemPolicyLabels()
{
    const auto* Mode=GetWorld()?GetWorld()->GetAuthGameMode<AAnomaliaZPrigimaliaGameMode>():nullptr;
    if(!Mode || ItemPolicyLabels.Num()!=3) return;
    const bool Enabled[]={Mode->ActiveServerSettings.bAllowRPSubstances,Mode->ActiveServerSettings.bAllowTobacco,Mode->ActiveServerSettings.bAllowAlcohol};
    const TCHAR* Names[]={TEXT("Substances RP"),TEXT("Tabac"),TEXT("Alcool")};
    for(int32 Index=0;Index<3;++Index) if(ItemPolicyLabels[Index])
        ItemPolicyLabels[Index]->SetText(FText::FromString(FString(Names[Index])+(Enabled[Index]?TEXT(" : autorisé"):TEXT(" : interdit"))));
}
void UAnomaliaZPrigimaliaSessionWidget::ToggleItemPolicy(int32 Index)
{
    auto* Mode=GetWorld()?GetWorld()->GetAuthGameMode<AAnomaliaZPrigimaliaGameMode>():nullptr;
    if(!Mode || GetWorld()->GetNetMode()!=NM_Standalone || Index<0 || Index>2) return;
    auto Candidate=Mode->ActiveServerSettings;
    bool* Flags[]={&Candidate.bAllowRPSubstances,&Candidate.bAllowTobacco,&Candidate.bAllowAlcohol};
    *Flags[Index]=!*Flags[Index];FString Error;
    const bool Saved=UAnomaliaZPrigimaliaConfigLibrary::SaveServerSettings(Mode->ServerId,Candidate,Error);
    if(Saved) Mode->ActiveServerSettings=Candidate;
    RefreshItemPolicyLabels();
    if(Feedback) Feedback->SetText(FText::FromString(Saved?TEXT("Règle appliquée et enregistrée pour cette partie."):Error));
}
FReply UAnomaliaZPrigimaliaSessionWidget::NativeOnKeyDown(const FGeometry& Geometry,const FKeyEvent& Event)
{
    if(bStartupIntro) { FinishIntro();return FReply::Handled(); }
    if(Event.GetKey()==EKeys::Escape || Event.GetKey()==EKeys::Gamepad_FaceButton_Right)
    {
        if(ServerBrowserFrame && ServerBrowserFrame->GetVisibility()==ESlateVisibility::Visible)
        { CloseServerBrowser(); }
        else if(OnlinePlayersFrame && OnlinePlayersFrame->GetVisibility()==ESlateVisibility::Visible)
        { CloseOnlinePlayers(); }
        else if(WorkshopFrame && WorkshopFrame->GetVisibility()==ESlateVisibility::Visible)
        { CloseWorkshop(); }
        else if(DetailsFrame && DetailsFrame->GetVisibility()!=ESlateVisibility::Collapsed)
        { ClosePage(); if(HomeButton) HomeButton->SetUserFocus(GetOwningPlayer()); }
        else if(!bMainMenu) Play();
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(Geometry,Event);
}
