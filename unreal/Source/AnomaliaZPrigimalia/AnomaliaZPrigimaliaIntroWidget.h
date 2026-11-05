#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "AnomaliaZPrigimaliaIntroWidget.generated.h"

class APlayerController;
class UAudioComponent;
class UButton;
class UImage;
class UMediaPlayer;
class UMediaSoundComponent;
class UMediaTexture;
class UTextBlock;

/**
 * Local startup only: a 24-second original-scene movie followed by the user's original voice and blood on click, then 5 seconds of red emergency announcement.
 * All existing game / server / persistence state stays in the original GameMode.
 */
UCLASS()
class ANOMALIAZPRIGIMALIA_API UAnomaliaZPrigimaliaIntroWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    /** nullptr means media is absent; caller should open the original menu. */
    static UAnomaliaZPrigimaliaIntroWidget* Open(APlayerController* PC);

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;
    virtual void NativeDestruct() override;

private:
    UFUNCTION() void OnVideoEnded();
    UFUNCTION() void OnMovieOpenFailed(FString FailedUrl);
    UFUNCTION() void OnMovieOpened(FString OpenedUrl);
    UFUNCTION() void OnContinueClicked();
    UFUNCTION() void OnVoiceEnded();

    void BeginEmergencyScreen();
    void FinishToMainMenu();

    UPROPERTY(Transient) TObjectPtr<UMediaPlayer> VideoPlayer;
    UPROPERTY(Transient) TObjectPtr<UMediaTexture> VideoTexture;
    UPROPERTY(Transient) TObjectPtr<UMediaSoundComponent> VideoSound;
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> VoiceComponent;
    UPROPERTY(Transient) TObjectPtr<UImage> VideoImage;
    UPROPERTY(Transient) TObjectPtr<UButton> ContinueButton;
    UPROPERTY(Transient) TObjectPtr<UButton> SkipButton;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> ContinueText;

    enum class EIntroPhase : uint8 { Intro, BloodAndVoice, Emergency };
    EIntroPhase Phase = EIntroPhase::Intro;
    bool bClicked = false;
    bool bMenuOpened = false;
    bool bBloodFinished = false;
    bool bVoiceFinished = false;
    double ClickStartedAt = -1.0;
    double EmergencyStartedAt = -1.0;
};
