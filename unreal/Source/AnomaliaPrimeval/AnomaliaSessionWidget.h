#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "AnomaliaSessionWidget.generated.h"
class UButton;
class UTextBlock;
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaSessionWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    static UAnomaliaSessionWidget* Open(APlayerController* PC,bool MainMenu=false);
    virtual void NativeConstruct() override;
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry,const FKeyEvent& Event) override;
private:
    void BuildLayout();
    bool bMainMenu=false;
    int32 Quality=1;
    UPROPERTY() TObjectPtr<UButton> PlayButton;
    UPROPERTY() TObjectPtr<UTextBlock> QualityLabel;
    UPROPERTY() TObjectPtr<UTextBlock> Feedback;
    UFUNCTION() void Play();
    UFUNCTION() void ChangeQuality();
    UFUNCTION() void Save();
    UFUNCTION() void SaveAndQuit();
    UFUNCTION() void Quit();
};
