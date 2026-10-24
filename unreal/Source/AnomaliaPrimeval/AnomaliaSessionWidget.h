#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "AnomaliaSessionWidget.generated.h"
class UButton;
class UTextBlock;
class UVerticalBox;
class UWidgetSwitcher;
class ACameraActor;
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaSessionWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    static UAnomaliaSessionWidget* Open(APlayerController* PC,bool MainMenu=false);
    virtual void NativeConstruct() override;
    virtual void NativeDestruct() override;
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry,const FKeyEvent& Event) override;
private:
    void BuildLayout();
    bool bMainMenu=false;
    int32 Quality=1;
    UPROPERTY() TObjectPtr<UButton> PlayButton;
    UPROPERTY() TObjectPtr<UTextBlock> QualityLabel;
    UPROPERTY() TObjectPtr<UTextBlock> Feedback;
    UPROPERTY() TObjectPtr<UWidgetSwitcher> Pages;
    UPROPERTY() TObjectPtr<UVerticalBox> ModRows;
    UPROPERTY() TObjectPtr<UButton> HomeButton;
    UPROPERTY() TObjectPtr<UButton> OptionsButton;
    UPROPERTY() TObjectPtr<UButton> ModsButton;
    UPROPERTY() TObjectPtr<ACameraActor> MenuCamera;
    TWeakObjectPtr<AActor> PreviousViewTarget;
    UFUNCTION() void ShowHome();
    UFUNCTION() void ShowOptions();
    UFUNCTION() void ShowMods();
    UFUNCTION() void RefreshMods();
    UFUNCTION() void OpenModsFolder();
    UFUNCTION() void OpenWorldEditor();
    void SelectPage(int32 Index);
    UFUNCTION() void Play();
    UFUNCTION() void ChangeQuality();
    UFUNCTION() void Save();
    UFUNCTION() void SaveAndQuit();
    UFUNCTION() void Quit();
    UFUNCTION() void ToggleSubstances();
    UFUNCTION() void ToggleTobacco();
    UFUNCTION() void ToggleAlcohol();
    void ToggleItemPolicy(int32 Index);
    void RefreshItemPolicyLabels();
    UPROPERTY() TArray<TObjectPtr<UTextBlock>> ItemPolicyLabels;
};
