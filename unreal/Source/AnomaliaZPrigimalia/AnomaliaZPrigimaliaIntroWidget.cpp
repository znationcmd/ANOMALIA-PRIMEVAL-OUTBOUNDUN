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
#include "HAL/PlatformTime.h"
#include "Sound/SoundBase.h"

namespace
{
    FString IntroMoviePath()
    {
        // Staged non-UAsset movie: ensure packaging copies Content/Movies.
        return FPaths::ConvertRelativePathToFull(FPaths::Combine(
            FPaths::ProjectContentDir(), TEXT("Movies"),
            TEXT("INTRO_JEU_24s_MUSIQUE.mp4")));
    }

    FString EmergencyMoviePath()
    {
        // Exactly five seconds of the user-approved red/yellow alert screen.
        return FPaths::ConvertRelativePathToFull(FPaths::Combine(
            FPaths::ProjectContentDir(), TEXT("Movies"),
            TEXT("ANOMALIAZ_Alerte_Rouge_5s.mp4")));
    }

    FString ClickBloodMoviePath()
    {
        // Click-only original liquid blood animation, no spoken audio embedded.
        // The spoken title remains the separate SW_IntroTitle SoundWave.
        return FPaths::ConvertRelativePathToFull(FPaths::Combine(
            FPaths::ProjectContentDir(), TEXT("Movies"),
            TEXT("ANOMALIAZ_PRIGIMALIA_Clic_Sang_6s.mp4")));
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
    if (Intro->bMenuOpened) return Intro; // OpenFile may have failed during NativeConstruct.
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
    VideoPlayer->OnMediaOpenFailed.AddDynamic(this, &UAnomaliaZPrigimaliaIntroWidget::OnMovieOpenFailed);
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

void UAnomaliaZPrigimaliaIntroWidget::OnMovieOpenFailed(FString FailedUrl)
{
    UE_LOG(LogTemp, Warning, TEXT("PRIGIMALIA_INTRO_MEDIA_FAILED: %s"), *FailedUrl);
    if (bMenuOpened) return;

    if (Phase == EIntroPhase::Emergency)
    {
        // Never trap the game if the five-second clip is missing or unreadable.
        FinishToMainMenu();
    }
    else if (Phase == EIntroPhase::BloodAndVoice)
    {
        bBloodFinished = true;
        if (bVoiceFinished) BeginEmergencyScreen();
    }
    else
    {
        FinishToMainMenu();
    }
}

void UAnomaliaZPrigimaliaIntroWidget::OnVideoEnded()
{
    if (bMenuOpened) return;
    if (Phase == EIntroPhase::Emergency)
    {
        // NativeTick enforces 5 seconds regardless of early decoder callbacks.
        return;
    }
    if (Phase == EIntroPhase::BloodAndVoice)
    {
        bBloodFinished = true;
        if (bVoiceFinished) BeginEmergencyScreen();
        return;
    }
    if (ContinueButton) ContinueButton->SetVisibility(ESlateVisibility::Visible);
    if (SkipButton) SkipButton->SetVisibility(ESlateVisibility::Collapsed);
}

void UAnomaliaZPrigimaliaIntroWidget::OnContinueClicked()
{
    if (bClicked || bMenuOpened) return;
    bClicked = true;
    Phase = EIntroPhase::BloodAndVoice;
    ClickStartedAt = FPlatformTime::Seconds();
    bBloodFinished = true; // Fallback when the blood clip cannot be opened.
    if (VideoPlayer)
    {
        VideoPlayer->Close();
        // As soon as the player clicks, this replaces the intro by six seconds
        // of visibly flowing crimson drips over the existing game artwork.
        // The sequence is deliberately silent; voice is triggered below.
        if (FPaths::FileExists(ClickBloodMoviePath()))
        {
            if (!VideoPlayer->OpenFile(ClickBloodMoviePath()))
                UE_LOG(LogTemp, Warning, TEXT("PRIGIMALIA_BLOOD_MOVIE_FAILED"));
            else bBloodFinished = false;
        }
        else
        {
            UE_LOG(LogTemp, Warning, TEXT("PRIGIMALIA_BLOOD_MOVIE_MISSING"));
        }
    }
    if (ContinueButton) ContinueButton->SetIsEnabled(false);
    if (SkipButton) SkipButton->SetVisibility(ESlateVisibility::Collapsed);
    // No on-screen title. The zombie voice is the only title announcement.
    if (ContinueButton) ContinueButton->SetVisibility(ESlateVisibility::Collapsed);

    // Independent voice on click; movie sound does NOT substitute for the click reaction.
    USoundBase* Voice = LoadObject<USoundBase>(nullptr,
        TEXT("/Game/AnomaliaZPrigimalia/Branding/SW_IntroTitle_Original_v5.SW_IntroTitle_Original_v5"));
    if (!Voice)
    {
        UE_LOG(LogTemp, Warning, TEXT("PRIGIMALIA_INTRO_TITLE_VOICE_MISSING: import VOIX_ET_SON_ORIGINAUX_NON_MODIFIES.wav"));
        bVoiceFinished = true;
        if (bBloodFinished) BeginEmergencyScreen();
        return;
    }
    VoiceComponent = UGameplayStatics::CreateSound2D(
        this, Voice, 1.f, 1.f, 0.f, nullptr, false, false);
    if (VoiceComponent)
    {
        VoiceComponent->bIsUISound = true;
        VoiceComponent->OnAudioFinished.AddDynamic(this, &UAnomaliaZPrigimaliaIntroWidget::OnVoiceEnded);
        VoiceComponent->Play();
    }
    else
    {
        bVoiceFinished = true;
        if (bBloodFinished) BeginEmergencyScreen();
    }
}

void UAnomaliaZPrigimaliaIntroWidget::OnVoiceEnded()
{
    if (bMenuOpened || Phase != EIntroPhase::BloodAndVoice) return;
    bVoiceFinished = true;
    // Wait for BOTH the original voice and the exact six-second blood animation.
    if (bBloodFinished) BeginEmergencyScreen();
}

void UAnomaliaZPrigimaliaIntroWidget::BeginEmergencyScreen()
{
    if (bMenuOpened || Phase != EIntroPhase::BloodAndVoice) return;
    if (!bVoiceFinished || !bBloodFinished) return;
    Phase = EIntroPhase::Emergency;
    EmergencyStartedAt = FPlatformTime::Seconds();
    if (!VideoPlayer || !FPaths::FileExists(EmergencyMoviePath()))
    {
        UE_LOG(LogTemp, Warning, TEXT("PRIGIMALIA_EMERGENCY_5S_MOVIE_MISSING"));
        FinishToMainMenu();
        return;
    }
    VideoPlayer->Close();
    if (!VideoPlayer->OpenFile(EmergencyMoviePath()))
    {
        UE_LOG(LogTemp, Warning, TEXT("PRIGIMALIA_EMERGENCY_5S_MOVIE_OPEN_FAILED"));
        FinishToMainMenu();
    }
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


void UAnomaliaZPrigimaliaIntroWidget::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
    Super::NativeTick(Geometry, DeltaTime);
    if (bMenuOpened) return;
    const double Now = FPlatformTime::Seconds();
    if (Phase == EIntroPhase::BloodAndVoice && ClickStartedAt >= 0.0)
    {
        // Windows MediaPlayer end callbacks can be missed in paused UI scenes.
        // The actual blood video is exactly six seconds long.
        if (!bBloodFinished && Now - ClickStartedAt >= 6.25)
            bBloodFinished = true;
        // Failsafe only: the original recording is ~5.04s, don't risk a frozen menu.
        if (!bVoiceFinished && Now - ClickStartedAt >= 9.0)
            bVoiceFinished = true;
        if (bBloodFinished && bVoiceFinished)
            BeginEmergencyScreen();
    }
    else if (Phase == EIntroPhase::Emergency && EmergencyStartedAt >= 0.0 &&
             Now - EmergencyStartedAt >= 5.0)
    {
        // Show exactly five seconds, THEN open the real Unreal session menu.
        FinishToMainMenu();
    }
}

void UAnomaliaZPrigimaliaIntroWidget::NativeDestruct()
{
    if (VideoPlayer)
    {
        VideoPlayer->OnEndReached.RemoveDynamic(this, &UAnomaliaZPrigimaliaIntroWidget::OnVideoEnded);
        VideoPlayer->OnMediaOpenFailed.RemoveDynamic(this, &UAnomaliaZPrigimaliaIntroWidget::OnMovieOpenFailed);
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
