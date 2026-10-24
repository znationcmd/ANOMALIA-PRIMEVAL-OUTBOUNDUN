#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/ComboBoxString.h"
#include "AnomaliaSessionWidget.generated.h"
class UButton;
class UTextBlock;
class UVerticalBox;
class UWidgetSwitcher;
class ACameraActor;
class UImage;
class UBorder;
class UCanvasPanel;
class UComboBoxString;
class UEditableTextBox;
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaSessionWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    static UAnomaliaSessionWidget* Open(APlayerController* PC,bool MainMenu=false);
    virtual void NativeConstruct() override;
    virtual void NativeDestruct() override;
    virtual void NativeTick(const FGeometry& Geometry,float DeltaTime) override;
    virtual FReply NativeOnMouseButtonDown(const FGeometry& Geometry,const FPointerEvent& Event) override;
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry,const FKeyEvent& Event) override;
private:
    void BuildLayout();
    void BuildPremiumWorkshop(UCanvasPanel* Canvas);
    bool bMainMenu=false;
    int32 Quality=1;
    UPROPERTY() TObjectPtr<UButton> PlayButton;
    UPROPERTY() TObjectPtr<UTextBlock> QualityLabel;
    UPROPERTY() TObjectPtr<UTextBlock> Feedback;
    UPROPERTY() TObjectPtr<UWidgetSwitcher> Pages;
    UPROPERTY() TObjectPtr<UVerticalBox> ModRows;
    UPROPERTY() TObjectPtr<UBorder> WorkshopFrame;
    UPROPERTY() TObjectPtr<UVerticalBox> WorkshopCards;
    UPROPERTY() TObjectPtr<UEditableTextBox> WorkshopSearch;
    UPROPERTY() TObjectPtr<UComboBoxString> WorkshopCategory;
    UPROPERTY() TObjectPtr<UTextBlock> WorkshopStatus;
    UPROPERTY() TObjectPtr<UButton> HomeButton;
    UPROPERTY() TObjectPtr<UButton> OptionsButton;
    UPROPERTY() TObjectPtr<UButton> ModsButton;
    UPROPERTY() TObjectPtr<ACameraActor> MenuCamera;
    TWeakObjectPtr<AActor> PreviousViewTarget;
    UPROPERTY() TObjectPtr<UImage> MenuArtwork;
    UPROPERTY() TObjectPtr<UBorder> NavigationFrame;
    UPROPERTY() TObjectPtr<UBorder> DetailsFrame;
    UPROPERTY() TObjectPtr<UUserWidget> HiddenStatusWidget;
    ESlateVisibility PreviousStatusVisibility=ESlateVisibility::Visible;
    double IntroStarted=0;
    bool bStartupIntro=false;
    void FinishIntro();
    UFUNCTION() void ClosePage();
    UFUNCTION() void ShowHome();
    UFUNCTION() void ShowOptions();
    UFUNCTION() void ShowMods();
    UFUNCTION() void RefreshMods();
    UFUNCTION() void RefreshWorkshop();
    UFUNCTION() void WorkshopSearchChanged(const FText& NewText);
    UFUNCTION() void WorkshopCategoryChanged(FString SelectedItem, ESelectInfo::Type SelectionType);
    UFUNCTION() void CloseWorkshop();
    UFUNCTION() void OpenWorkshopTools();
    UFUNCTION() void OpenWorkshopHosting();
    UFUNCTION() void WorkshopFilterAll();
    UFUNCTION() void WorkshopFilterVehicles();
    UFUNCTION() void WorkshopFilterWeapons();
    UFUNCTION() void WorkshopFilterBuildings();
    UFUNCTION() void WorkshopFilterCreatures();
    UFUNCTION() void WorkshopFilterSurvival();
    UFUNCTION() void WorkshopFilterMaps();
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
