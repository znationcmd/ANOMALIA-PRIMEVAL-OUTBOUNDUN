#include "AnomaliaFurnitureWidget.h"
#include "AnomaliaFurnitureComponent.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/ScrollBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "InputCoreTypes.h"

#define LOCTEXT_NAMESPACE "AnomaliaFurniture"

void UAnomaliaFurnitureActionRelay::Execute()
{ if (Target) Target->Perform(Action, Type); }

void UAnomaliaFurnitureWidget::InitializeForFurniture(UAnomaliaFurnitureComponent* Component)
{ Furniture = Component; SetIsFocusable(true); }

void UAnomaliaFurnitureWidget::AddButton(UVerticalBox* Container, const FText& Label, FName Action, FName Type)
{
    UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
    UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Text->SetText(Label);
    Button->SetContent(Text);
    Container->AddChildToVerticalBox(Button)->SetPadding(FMargin(12.f, 4.f));
    UAnomaliaFurnitureActionRelay* Relay = NewObject<UAnomaliaFurnitureActionRelay>(this);
    Relay->Target = this; Relay->Action = Action; Relay->Type = Type;
    Relays.Add(Relay);
    Button->OnClicked.AddDynamic(Relay, &UAnomaliaFurnitureActionRelay::Execute);
}

void UAnomaliaFurnitureWidget::NativeConstruct()
{
    Super::NativeConstruct();
    if (!WidgetTree || WidgetTree->RootWidget) return;
    UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
    WidgetTree->RootWidget = Canvas;
    UBorder* Frame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
    Frame->SetBrushColor(FLinearColor(.012f, .035f, .055f, .97f));
    UCanvasPanelSlot* Slot = Canvas->AddChildToCanvas(Frame);
    Slot->SetAnchors(FAnchors(.15f, .05f, .85f, .95f));
    Slot->SetOffsets(FMargin(0));
    UScrollBox* Scroll = WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass());
    Frame->SetContent(Scroll);
    UVerticalBox* Content = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    Scroll->AddChild(Content);
    UTextBlock* Heading = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Heading->SetText(LOCTEXT("Title", "ANOMALIA / AMEUBLEMENT — PROTOTYPE CRÉATIF"));
    Content->AddChildToVerticalBox(Heading)->SetPadding(FMargin(12));
    UTextBlock* Help = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Help->SetText(LOCTEXT("Help", "Choisissez un meuble, puis visez le sol et appuyez sur B.\nG : sélectionner · T : déplacer · H : pivoter · F2 : catalogue.\nLes modèles sont encore des cubes temporaires. Les droits sont vérifiés par le serveur."));
    Help->SetAutoWrapText(true);
    Content->AddChildToVerticalBox(Help)->SetPadding(FMargin(12));
    AddButton(Content, LOCTEXT("Bed", "Lit"), TEXT("place"), TEXT("bed"));
    AddButton(Content, LOCTEXT("Table", "Table"), TEXT("place"), TEXT("table"));
    AddButton(Content, LOCTEXT("Chair", "Chaise"), TEXT("place"), TEXT("chair"));
    AddButton(Content, LOCTEXT("Sofa", "Canapé"), TEXT("place"), TEXT("sofa"));
    AddButton(Content, LOCTEXT("Wardrobe", "Armoire"), TEXT("place"), TEXT("wardrobe"));
    AddButton(Content, LOCTEXT("Kitchen", "Cuisine"), TEXT("place"), TEXT("kitchen"));
    AddButton(Content, LOCTEXT("Lamp", "Lampe"), TEXT("place"), TEXT("lamp"));
    AddButton(Content, LOCTEXT("Beehive", "Ruche"), TEXT("place"), TEXT("beehive"));
    AddButton(Content, LOCTEXT("Doghouse", "Niche"), TEXT("place"), TEXT("doghouse"));
    AddButton(Content, LOCTEXT("Barn", "Grange"), TEXT("place"), TEXT("barn"));
    AddButton(Content, LOCTEXT("Fence", "Clôture"), TEXT("place"), TEXT("fence"));
    AddButton(Content, LOCTEXT("TractorShed", "Abri agricole"), TEXT("place"), TEXT("tractor_shed"));
    Status = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Status->SetAutoWrapText(true);
    Status->SetText(Furniture && !Furniture->GetSelectedId().IsEmpty()
        ? LOCTEXT("Selected", "Meuble sélectionné. Les actions restent soumises à vos droits.")
        : LOCTEXT("NoSelection", "Aucun meuble sélectionné. Fermez puis utilisez G en visant un meuble."));
    Content->AddChildToVerticalBox(Status)->SetPadding(FMargin(12));
    AddButton(Content, LOCTEXT("Rotate", "Pivoter la sélection de 90°"), TEXT("rotate"));
    AddButton(Content, LOCTEXT("Remove", "Supprimer la sélection…"), TEXT("remove"));
    Confirmation = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    Content->AddChildToVerticalBox(Confirmation);
    UTextBlock* Warning = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Warning->SetText(LOCTEXT("Question", "Confirmer la suppression du meuble sélectionné ?"));
    Confirmation->AddChildToVerticalBox(Warning);
    AddButton(Confirmation, LOCTEXT("Confirm", "Confirmer la suppression"), TEXT("confirm"));
    AddButton(Confirmation, LOCTEXT("Cancel", "Conserver le meuble"), TEXT("cancel"));
    Confirmation->SetVisibility(ESlateVisibility::Collapsed);
    AddButton(Content, LOCTEXT("Undo", "Annuler la dernière modification"), TEXT("undo"));
    AddButton(Content, LOCTEXT("Redo", "Rétablir la modification"), TEXT("redo"));
    AddButton(Content, LOCTEXT("Close", "Fermer / Échap"), TEXT("close"));
}

void UAnomaliaFurnitureWidget::Perform(FName Action, FName Type)
{
    if (!Furniture) return;
    if (Action == TEXT("confirm"))
    {
        // Captured ID, never a fresh selection: confirmation cannot delete a different object.
        const FString Id = PendingRemovalId;
        PendingRemovalId.Reset();
        Confirmation->SetVisibility(ESlateVisibility::Collapsed);
        if (!Id.IsEmpty()) Furniture->RequestRemove(Id, true);
        return;
    }
    PendingRemovalId.Reset();
    Confirmation->SetVisibility(ESlateVisibility::Collapsed);
    if (Action == TEXT("place")) Furniture->ChoosePlacementType(Type);
    else if (Action == TEXT("close")) Furniture->ClosePalette();
    else if (Action == TEXT("rotate")) Furniture->RotateSelectionFromPalette();
    else if (Action == TEXT("undo")) Furniture->RequestUndo();
    else if (Action == TEXT("redo")) Furniture->RequestRedo();
    else if (Action == TEXT("remove"))
    {
        PendingRemovalId = Furniture->GetSelectedId();
        if (!PendingRemovalId.IsEmpty()) Confirmation->SetVisibility(ESlateVisibility::Visible);
        else Status->SetText(LOCTEXT("MissingSelection", "Sélectionnez d’abord un meuble avec G."));
    }
}

void UAnomaliaFurnitureWidget::ShowResult(bool bSuccess)
{
    if (Status) Status->SetText(bSuccess
        ? LOCTEXT("Saved", "Modification sauvegardée.")
        : LOCTEXT("Refused", "Modification refusée : vérifiez vos droits, la distance, les collisions et la configuration du serveur."));
}

FReply UAnomaliaFurnitureWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    if (Event.GetKey() == EKeys::Escape || Event.GetKey() == EKeys::F2)
    {
        if (Furniture) Furniture->ClosePalette();
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(Geometry, Event);
}
#undef LOCTEXT_NAMESPACE
