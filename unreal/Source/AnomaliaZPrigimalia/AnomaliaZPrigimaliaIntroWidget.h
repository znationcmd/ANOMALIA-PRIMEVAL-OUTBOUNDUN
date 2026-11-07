#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "AnomaliaZPrigimaliaIntroWidget.generated.h"

class APlayerController;
class UButton;
class UImage;
class UMediaPlayer;
class UMediaSoundComponent;
class UMediaTexture;

/**
 * A SINGLE, user-approved 35-second H.264/AAC movie (24s intro, 6s original
 * blood and spoken title, 5s red emergency card), then the genuine native menu.
 * At 24 seconds the ONE movie pauses for the original "click to start" action.
 * The remaining 11 seconds play from the SAME media file after the click.
 * No separate voice, blood movie, alert movie or spliced playback is required.
 */
UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaIntroWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    /** Return nullptr if the merged movie is missing, allowing the GameMode's real menu fallback. */
    static UAnomaliaZPrigimaliaIntroWidget* Open(APlayerController* PC);

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;
    virtual void NativeDestruct() override;

private:
    UFUNCTION() void OnVideoEnded();
    UFUNCTION() void OnMovieOpenFailed(FString FailedUrl);
    UFUNCTION() void OnContinueClicked();
    UFUNCTION() void OnSkipClicked();

    void PauseAtClick();
    void FinishToMainMenu();

    UPROPERTY(Transient) TObjectPtr<UMediaPlayer> VideoPlayer;
    UPROPERTY(Transient) TObjectPtr<UMediaTexture> VideoTexture;
    UPROPERTY(Transient) TObjectPtr<UMediaSoundComponent> VideoSound;
    UPROPERTY(Transient) TObjectPtr<UImage> VideoImage;
    UPROPERTY(Transient) TObjectPtr<UButton> ContinueButton;
    UPROPERTY(Transient) TObjectPtr<UButton> SkipButton;

    bool bAwaitingClick = false;
    bool bClicked = false;
    bool bMenuOpened = false;
    double ClickStartedAt = -1.0;
};
