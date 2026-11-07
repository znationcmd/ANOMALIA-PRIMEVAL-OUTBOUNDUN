#include "AnomaliaZPrigimaliaIntroWidget.h"

#include "AnomaliaZPrigimaliaSessionWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/TextBlock.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "MediaPlayer.h"
#include "MediaSoundComponent.h"
#include "MediaTexture.h"
#include "Misc/Paths.h"
#include "HAL/PlatformTime.h"

namespace
{
    FString UnifiedMoviePath()
    {
        // ONE continuous H264/AAC MP4, duration 35.000s. All sounds and scenes
        // are embedded: no extra Voice SoundWave, blood or emergency file.
        return FPaths::ConvertRelativePathToFull(FPaths::Combine(
            FPaths::ProjectContentDir(), TEXT("Movies"),
            TEXT("ANOMALIAZ_PRIGIMALIA_GENERIQUE_35s_ALERTE_ROUGE.mp4")));
    }
}

UAnomaliaZPrigimaliaIntroWidget* UAnomaliaZPrigimaliaIntroWidget::Open(APlayerController* PC)
{
    if (!PC || !PC->IsLocalController() || PC->GetNetMode() != NM_Standalone)
        return nullptr;
    if (!FPaths::FileExists(UnifiedMoviePath()))
    {
        UE_LOG(LogTemp, Warning, TEXT("PRIGIMALIA_UNIFIED_35S_MOVIE_MISSING: %s"), *UnifiedMoviePath());
        return nullptr;
    }

    auto* Intro = CreateWidget<UAnomaliaZPrigimaliaIntroWidget>(PC, StaticClass());
    if (!Intro) return nullptr;
    Intro->AddToViewport(120);
    if (Intro->bMenuOpened) return Intro;
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

        VideoImage = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("Unified35sMovie"));
        VideoImage->SetVisibility(ESlateVisibility::HitTestInvisible);
        auto* MovieSlot = Root->AddChildToOverlay(VideoImage);
        MovieSlot->SetHorizontalAlignment(HAlign_Fill);
        MovieSlot->SetVerticalAlignment(VAlign_Fill);

        ContinueButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("IntroContinue"));
        auto* ContinueText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("IntroContinueLabel"));
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
        auto* SkipText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("IntroSkipLabel"));
        SkipText->SetText(FText::FromString(TEXT("PASSER  >>")));
        SkipText->SetColorAndOpacity(FSlateColor(FLinearColor::White));
        SkipButton->SetContent(SkipText);
        SkipButton->OnClicked.AddDynamic(this, &UAnomaliaZPrigimaliaIntroWidget::OnSkipClicked);
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
        VideoSound = NewObject<UMediaSoundComponent>(PC, TEXT("PrigimaliaUnified35sSound"));
        if (VideoSound)
        {
            VideoSound->SetMediaPlayer(VideoPlayer);
            VideoSound->RegisterComponent();
            VideoSound->Activate(true);
        }
    }
    if (!VideoPlayer->OpenFile(UnifiedMoviePath()))
    {
        UE_LOG(LogTemp, Warning, TEXT("PRIGIMALIA_UNIFIED_35S_OPEN_FAILED"));
        FinishToMainMenu();
    }
}

void UAnomaliaZPrigimaliaIntroWidget::OnMovieOpenFailed(FString FailedUrl)
{
    UE_LOG(LogTemp, Warning, TEXT("PRIGIMALIA_UNIFIED_35S_MEDIA_FAILED: %s"), *FailedUrl);
    FinishToMainMenu();
}

void UAnomaliaZPrigimaliaIntroWidget::PauseAtClick()
{
    if (bAwaitingClick || bClicked || bMenuOpened) return;
    bAwaitingClick = true;
    if (VideoPlayer) VideoPlayer->Pause();
    if (SkipButton) SkipButton->SetVisibility(ESlateVisibility::Collapsed);
    if (ContinueButton)
    {
        ContinueButton->SetIsEnabled(true);
        ContinueButton->SetVisibility(ESlateVisibility::Visible);
    }
    UE_LOG(LogTemp, Log, TEXT("PRIGIMALIA_UNIFIED_35S_PAUSED_AT_CLICK"));
}

void UAnomaliaZPrigimaliaIntroWidget::OnSkipClicked()
{
    if (bClicked || bAwaitingClick || bMenuOpened || !VideoPlayer) return;
    // PASSER skips only the first 24 seconds, not the original spoken name,
    // blood sequence or five-second red announcement.
    if (!VideoPlayer->Seek(FTimespan::FromSeconds(23.9)))
        UE_LOG(LogTemp, Warning, TEXT("PRIGIMALIA_UNIFIED_35S_SKIP_SEEK_FAILED"));
    PauseAtClick();
}

void UAnomaliaZPrigimaliaIntroWidget::OnContinueClicked()
{
    if (bClicked || bMenuOpened || !bAwaitingClick) return;
    bClicked = true;
    bAwaitingClick = false;
    ClickStartedAt = FPlatformTime::Seconds();
    if (ContinueButton) ContinueButton->SetVisibility(ESlateVisibility::Collapsed);
    if (SkipButton) SkipButton->SetVisibility(ESlateVisibility::Collapsed);
    // Resume THE SAME 35-second file at 24 seconds: embedded original voice,
    // six seconds of original blood and five seconds of the red emergency card.
    if (!VideoPlayer || !VideoPlayer->Play())
    {
        UE_LOG(LogTemp, Warning, TEXT("PRIGIMALIA_UNIFIED_35S_RESUME_FAILED"));
        FinishToMainMenu();
    }
}

void UAnomaliaZPrigimaliaIntroWidget::OnVideoEnded()
{
    // At second 35, the actual native Unreal main menu appears automatically.
    FinishToMainMenu();
}

void UAnomaliaZPrigimaliaIntroWidget::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
    Super::NativeTick(Geometry, DeltaTime);
    if (bMenuOpened || !VideoPlayer) return;
    if (!bClicked && !bAwaitingClick && VideoPlayer->GetTime().GetTotalSeconds() >= 23.95)
    {
        // Do not interrupt the title voice which begins in the same MP4 at 24s.
        PauseAtClick();
    }
    if (bClicked && ClickStartedAt >= 0.0 &&
        FPlatformTime::Seconds() - ClickStartedAt > 12.5)
    {
        // The remaining integrated movie is only 11 seconds. Prevent a
        // permanently paused/black UI if an end callback is lost.
        UE_LOG(LogTemp, Warning, TEXT("PRIGIMALIA_UNIFIED_35S_END_CALLBACK_TIMEOUT"));
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
        // Never strand the player on a paused intro if the menu cannot open.
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
        VideoPlayer->OnMediaOpenFailed.RemoveDynamic(this, &UAnomaliaZPrigimaliaIntroWidget::OnMovieOpenFailed);
        VideoPlayer->Close();
    }
    if (VideoSound)
    {
        VideoSound->Stop();
        VideoSound->DestroyComponent();
        VideoSound = nullptr;
    }
    Super::NativeDestruct();
}
