#include "AnomaliaZPrigimaliaIntroWidget.h"

#include "AnomaliaZPrigimaliaSessionWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/AudioComponent.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "MediaPlayer.h"
#include "MediaSoundComponent.h"
#include "MediaTexture.h"
#include "Misc/Paths.h"
#include "Sound/SoundBase.h"

namespace
{
    FString IntroMoviePath()
    {
        // Staged non-UAsset movie: ensure packaging copies Content/Movies.
        return FPaths::ConvertRelativePathToFull(FPaths::Combine(
            FPaths::ProjectContentDir(), TEXT("Movies"),
            TEXT("ANOMALIAZ_PRIGIMALIA_Intro_Cinematique_30s.mp4")));
    }
}

UAnomaliaZPrigimaliaIntroWidget* UAnomaliaZPrigimaliaIntroWidget::Open(APlayerController* PC)
{
    if (!PC || !PC->IsLocalController() || PC->GetNetMode() != NM_Standalone)
        return nullptr;
    if (!FPaths::FileExists(IntroMoviePath()))
    {
        UE_LOG(LogTemp, Warning, TEXT("PRIGIMALIA_INTRO_MOVIE_MISSING: %s"), *IntroMoviePath());
        return nullptr;
    }

    auto* Intro = CreateWidget<UAnomaliaZPrigimaliaIntroWidget>(PC, StaticClass());
    if (!Intro) return nullptr;
    Intro->AddToViewport(120);
    UGameplayStatics::SetGamePaused(PC, true);
    FInputModeUIOnly Mode;
    Mode.SetWidgetToFocus(Intro->TakeWidget());
    Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    PC->SetInputMode(Mode);
    PC->bShowMouseCursor = true;
    return Intro;
}

TSharedRef<SWidget> UAnomaliaZPrigimaliaIntroWidget::RebuildWidget()
{
    if (!WidgetTree)
        WidgetTree = NewObject<UWidgetTree>(this, TEXT("WidgetTree"));
    if (!WidgetTree->RootWidget)
    {
        auto* Root = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass(), TEXT("IntroRoot"));
        WidgetTree->RootWidget = Root;

        auto* Backdrop = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("DarkBackdrop"));
        Backdrop->SetBrushColor(FLinearColor::Black);
        Root->AddChildToOverlay(Backdrop);

        VideoImage = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("IntroMovieFrame"));
        VideoImage->SetVisibility(ESlateVisibility::HitTestInvisible);
        auto* MovieSlot = Root->AddChildToOverlay(VideoImage);
        MovieSlot->SetHorizontalAlignment(HAlign_Fill);
        MovieSlot->SetVerticalAlignment(VAlign_Fill);

        ContinueButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("IntroContinue"));
        ContinueText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("IntroContinueLabel"));
        ContinueText->SetText(FText::FromString(TEXT("CLIQUER POUR COMMENCER")));
        ContinueText->SetColorAndOpacity(FSlateColor(FLinearColor::White));
        ContinueText->SetJustification(ETextJustify::Center);
        ContinueButton->SetContent(ContinueText);
        ContinueButton->SetVisibility(ESlateVisibility::Collapsed);
        ContinueButton->OnClicked.AddDynamic(this, &UAnomaliaZPrigimaliaIntroWidget::OnContinueClicked);
        auto* ContinueSlot = Root->AddChildToOverlay(ContinueButton);
        ContinueSlot->SetHorizontalAlignment(HAlign_Center);
        ContinueSlot->SetVerticalAlignment(VAlign_Bottom);
        ContinueSlot->SetPadding(FMargin(24.f, 24.f, 24.f, 84.f));

        SkipButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("IntroSkip"));
        auto* SkipLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        SkipLabel->SetText(FText::FromString(TEXT("PASSER  >>")));
        SkipLabel->SetColorAndOpacity(FSlateColor(FLinearColor::White));
        SkipButton->SetContent(SkipLabel);
        SkipButton->OnClicked.AddDynamic(this, &UAnomaliaZPrigimaliaIntroWidget::OnContinueClicked);
        auto* SkipSlot = Root->AddChildToOverlay(SkipButton);
        SkipSlot->SetHorizontalAlignment(HAlign_Right);
        SkipSlot->SetVerticalAlignment(VAlign_Bottom);
        SkipSlot->SetPadding(FMargin(24.f));
    }
    return Super::RebuildWidget();
}

void UAnomaliaZPrigimaliaIntroWidget::NativeConstruct()
{
    Super::NativeConstruct();
    SetIsFocusable(true);

    VideoPlayer = NewObject<UMediaPlayer>(this);
    VideoTexture = NewObject<UMediaTexture>(this);
    if (!VideoPlayer || !VideoTexture)
    {
        FinishToMainMenu();
        return;
    }
    VideoPlayer->SetLooping(false);
    VideoPlayer->PlayOnOpen = true;
    VideoPlayer->OnEndReached.AddDynamic(this, &UAnomaliaZPrigimaliaIntroWidget::OnVideoEnded);
    VideoTexture->SetMediaPlayer(VideoPlayer);
    VideoTexture->UpdateResource();

    FSlateBrush FrameBrush;
    FrameBrush.SetResourceObject(VideoTexture);
    FrameBrush.ImageSize = FVector2D(1920.f, 1080.f);
    if (VideoImage) VideoImage->SetBrush(FrameBrush);

    if (APlayerController* PC = GetOwningPlayer())
    {
        VideoSound = NewObject<UMediaSoundComponent>(PC, TEXT("PrigimaliaIntroMovieSound"));
        if (VideoSound)
        {
            VideoSound->SetMediaPlayer(VideoPlayer);
            VideoSound->RegisterComponent();
            VideoSound->Activate(true);
        }
    }

    if (!VideoPlayer->OpenFile(IntroMoviePath()))
    {
        UE_LOG(LogTemp, Warning, TEXT("PRIGIMALIA_INTRO_OPEN_FAILED"));
        FinishToMainMenu();
    }
}

void UAnomaliaZPrigimaliaIntroWidget::OnVideoEnded()
{
    if (bClicked || bMenuOpened) return;
    if (ContinueButton) ContinueButton->SetVisibility(ESlateVisibility::Visible);
    if (SkipButton) SkipButton->SetVisibility(ESlateVisibility::Collapsed);
}

void UAnomaliaZPrigimaliaIntroWidget::OnContinueClicked()
{
    if (bClicked || bMenuOpened) return;
    bClicked = true;
    if (VideoPlayer) VideoPlayer->Close();
    if (ContinueButton) ContinueButton->SetIsEnabled(false);
    if (SkipButton) SkipButton->SetVisibility(ESlateVisibility::Collapsed);
    if (ContinueText)
        ContinueText->SetText(FText::FromString(TEXT("ANOMALIA'Z PRIGIMALIA")));

    // Independent voice on click; movie sound does NOT substitute for the click reaction.
    const USoundBase* Voice = LoadObject<USoundBase>(nullptr,
        TEXT("/Game/AnomaliaZPrigimalia/Branding/SW_IntroTitle.SW_IntroTitle"));
    if (!Voice)
    {
        UE_LOG(LogTemp, Warning, TEXT("PRIGIMALIA_INTRO_TITLE_VOICE_MISSING: import SW_IntroTitle.wav"));
        FinishToMainMenu();
        return;
    }
    VoiceComponent = UGameplayStatics::SpawnSound2D(
        this, const_cast<USoundBase*>(Voice), 1.f, 1.f, 0.f, nullptr, false, false);
    if (VoiceComponent)
    {
        VoiceComponent->bIsUISound = true;
        VoiceComponent->OnAudioFinished.AddDynamic(this, &UAnomaliaZPrigimaliaIntroWidget::OnVoiceEnded);
    }
    else FinishToMainMenu();
}

void UAnomaliaZPrigimaliaIntroWidget::OnVoiceEnded()
{
    FinishToMainMenu();
}

void UAnomaliaZPrigimaliaIntroWidget::FinishToMainMenu()
{
    if (bMenuOpened) return;
    bMenuOpened = true;
    APlayerController* PC = GetOwningPlayer();
    RemoveFromParent();
    if (PC && !UAnomaliaZPrigimaliaSessionWidget::Open(PC, true))
    {
        // Never leave a player permanently paused when the UI cannot be built.
        UGameplayStatics::SetGamePaused(PC, false);
        FInputModeGameOnly Mode;
        PC->SetInputMode(Mode);
        PC->bShowMouseCursor = false;
    }
}

void UAnomaliaZPrigimaliaIntroWidget::NativeDestruct()
{
    if (VideoPlayer)
    {
        VideoPlayer->OnEndReached.RemoveDynamic(this, &UAnomaliaZPrigimaliaIntroWidget::OnVideoEnded);
        VideoPlayer->Close();
    }
    if (VideoSound)
    {
        VideoSound->Stop();
        VideoSound->DestroyComponent();
        VideoSound = nullptr;
    }
    if (VoiceComponent)
    {
        VoiceComponent->OnAudioFinished.RemoveDynamic(this, &UAnomaliaZPrigimaliaIntroWidget::OnVoiceEnded);
        VoiceComponent->Stop();
        VoiceComponent->DestroyComponent();
        VoiceComponent = nullptr;
    }
    Super::NativeDestruct();
}
