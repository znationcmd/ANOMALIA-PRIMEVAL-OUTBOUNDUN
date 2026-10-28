#include "AnomaliaInventoryWidget.h"
#include "AnomaliaInventoryComponent.h"
#include "AnomaliaLootPickup.h"
#include "Engine/SceneCapture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ScaleBox.h"
#include "Misc/PackageName.h"
#include "Materials/MaterialInterface.h"
#include "AnomaliaSurvivor.h"
#include "Vehicles/AnomaliaChaosRoadVehicle.h"
#include "Vehicles/AnomaliaVehicleSurvival.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/PlayerController.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SizeBox.h"
#include "Brushes/SlateColorBrush.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Components/WrapBox.h"
#include "Components/WrapBoxSlot.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SafeZone.h"
#include "Blueprint/WidgetTree.h"
#include "Blueprint/WidgetLayoutLibrary.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/ScrollBox.h"
#include "Components/ScrollBoxSlot.h"
#include "Components/TextBlock.h"
#include "Components/EditableTextBox.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"

void UAnomaliaInventoryActionRelay::Execute()
{
    if (TargetWidget) TargetWidget->PerformAction(Action, StackId, Count, OtherStackId);
}

UAnomaliaInventoryWidget* UAnomaliaInventoryWidget::CreateForPlayerInventory(APlayerController* Player)
{
    auto* Survivor=Player?Cast<AAnomaliaSurvivor>(Player->GetPawn()):nullptr;
    if(!Survivor||!Survivor->IsLocallyControlled()||!Survivor->InventoryComponent)return nullptr;
    if(Survivor->InventoryWidget&&Survivor->InventoryWidget->IsInViewport())return Survivor->InventoryWidget;
    auto* Screen=CreateWidget<UAnomaliaInventoryWidget>(Player,UAnomaliaInventoryWidget::StaticClass());
    if(!Screen)return nullptr;
    Survivor->InventoryWidget=Screen;
    Screen->InitializeForInventory(Survivor->InventoryComponent);Screen->AddToViewport(80);
    FInputModeGameAndUI Mode;Mode.SetWidgetToFocus(Screen->TakeWidget());Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    Player->SetInputMode(Mode);Screen->FocusFirstAction();Player->bShowMouseCursor=true;Player->SetIgnoreMoveInput(true);Player->SetIgnoreLookInput(true);
    return Screen;
}

void UAnomaliaInventoryWidget::InitializeForInventory(UAnomaliaInventoryComponent* InInventory)
{
    if (Inventory) Inventory->OnInventoryUpdated.RemoveDynamic(this, &UAnomaliaInventoryWidget::RefreshInventory);
    Inventory = InInventory;
    CurrentPage=0;
    if (Inventory) Inventory->OnInventoryUpdated.AddDynamic(this, &UAnomaliaInventoryWidget::RefreshInventory);
    RefreshInventory();
}

TSharedRef<SWidget> UAnomaliaInventoryWidget::RebuildWidget()
{
    if(!WidgetTree) WidgetTree=NewObject<UWidgetTree>(this,TEXT("WidgetTree"));
    BuildLayout();
    return Super::RebuildWidget();
}

void UAnomaliaInventoryWidget::NativeConstruct()
{
    Super::NativeConstruct();
    SetIsFocusable(true);
    BuildLayout();
    RefreshInventory();
    BeginCharacterView();
}

void UAnomaliaInventoryWidget::NativeDestruct()
{
    if (Inventory) Inventory->OnInventoryUpdated.RemoveDynamic(this, &UAnomaliaInventoryWidget::RefreshInventory);
    if(NearbyVehicle)
    {
        NearbyVehicle->CargoInventory->OnInventoryUpdated.RemoveDynamic(this,&UAnomaliaInventoryWidget::RefreshInventory);
        NearbyVehicle->SurvivalSystems->OnServicesUpdated.RemoveDynamic(this,&UAnomaliaInventoryWidget::RefreshInventory);
    }
    EndCharacterView();
    ReleaseIcons();
    Super::NativeDestruct();
}

void UAnomaliaInventoryWidget::StyleButton(UButton* Button,bool bSelected)
{
    FButtonStyle Style=Button->GetStyle();
    Style.Normal=FSlateColorBrush(bSelected?FLinearColor(.38f,.38f,.38f,.55f):FLinearColor(.045f,.045f,.045f,.28f));
    Style.Hovered=FSlateColorBrush(FLinearColor(.55f,.55f,.55f,.32f));
    Style.Pressed=FSlateColorBrush(FLinearColor(.7f,.7f,.7f,.5f));
    Style.Disabled=FSlateColorBrush(FLinearColor(.09f,.09f,.09f,.25f));
    Style.NormalPadding=FMargin(4.f,2.f);Style.PressedPadding=Style.NormalPadding;
    Button->SetStyle(Style);
}

void UAnomaliaInventoryWidget::BuildLayout()
{
    if(!WidgetTree||RootCanvas)return;
    RootCanvas=WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(),TEXT("InventoryCanvas"));
    auto* Safe=WidgetTree->ConstructWidget<USafeZone>(USafeZone::StaticClass());
    Safe->SetContent(RootCanvas);WidgetTree->RootWidget=Safe;
    auto Text=[&](const FString& Value,int32 Size=14){
        auto* T=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        T->SetText(FText::FromString(Value));T->SetColorAndOpacity(FSlateColor(FLinearColor(.92f,.92f,.92f)));
        auto Font=T->GetFont();Font.Size=Size;if(Size>=18)Font.TypefaceFontName=TEXT("Bold");T->SetFont(Font);T->SetAutoWrapText(true);return T;
    };
    auto Panel=[&](FName Name,const FAnchors& Anchors){
        auto* B=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(),Name);
        B->SetBrush(FSlateColorBrush(FLinearColor(.025f,.025f,.025f,.32f)));
        B->SetPadding(FMargin(2.f));auto* LayoutSlot=RootCanvas->AddChildToCanvas(B);
        LayoutSlot->SetAnchors(Anchors);LayoutSlot->SetOffsets(FMargin(0));LayoutSlot->SetZOrder(1);return B;
    };
    auto* Top=WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
    auto* Header=Panel(TEXT("EquipmentHeader"),FAnchors(.68f,.08f,.96f,.125f));
    Header->SetBrush(FSlateColorBrush(FLinearColor(.45f,.45f,.45f,.72f)));Header->SetContent(Top);
    auto Tab=[&](FName Name,const FString& Label){auto* B=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),Name);B->SetContent(Text(Label,15));StyleButton(B);auto* Slot=Top->AddChildToHorizontalBox(B);Slot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));return B;};
    InventoryTab=Tab(TEXT("InventoryTab"),TEXT("ÉQUIPEMENT"));InventoryTab->OnClicked.AddDynamic(this,&UAnomaliaInventoryWidget::ShowInventoryTab);
    CraftTab=Tab(TEXT("CraftTab"),TEXT("CRAFT"));CraftTab->OnClicked.AddDynamic(this,&UAnomaliaInventoryWidget::ShowCraftTab);
    BankTab=Tab(TEXT("BankTab"),TEXT("€"));BankTab->OnClicked.AddDynamic(this,&UAnomaliaInventoryWidget::ShowBankTab);
    CloseButton=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),TEXT("InventoryClose"));CloseButton->SetContent(Text(TEXT("×"),22));StyleButton(CloseButton);CloseButton->OnClicked.AddDynamic(this,&UAnomaliaInventoryWidget::CloseInventory);
    auto* CloseSlot=RootCanvas->AddChildToCanvas(CloseButton);CloseSlot->SetAnchors(FAnchors(.965f,.025f,.99f,.07f));CloseSlot->SetOffsets(FMargin(0));

    auto* NearbyScroll=WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(),TEXT("ProximityScroll"));
    Panel(TEXT("NearbyFrame"),FAnchors(.055f,.08f,.335f,.90f))->SetContent(NearbyScroll);
    ProximityList=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("VehicleProximity"));NearbyScroll->AddChild(ProximityList);

    auto* Right=WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
    Panel(TEXT("StorageFrame"),FAnchors(.68f,.13f,.96f,.92f))->SetContent(Right);
    auto Full=[&](UWidget* W){auto* S=Right->AddChildToCanvas(W);S->SetAnchors(FAnchors(0,0,1,1));S->SetOffsets(FMargin(0));};
    StoragePanel=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("StoragePanel"));Full(StoragePanel);
    EquipmentList=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("EquippedMeshes"));
    StoragePanel->AddChildToVerticalBox(EquipmentList)->SetPadding(FMargin(0,0,0,6));
    auto* Scroll=WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(),TEXT("InventoryScroll"));
    StoragePanel->AddChildToVerticalBox(Scroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    ItemList=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("InventoryItems"));Scroll->AddChild(ItemList);
    // These are actual equipped meshes, not empty clickable slots.
    WeightStatus=Text(TEXT(""));StoragePanel->AddChildToVerticalBox(WeightStatus)->SetPadding(FMargin(0,5));
    auto* Pages=WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());StoragePanel->AddChildToVerticalBox(Pages);
    PreviousPageButton=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),TEXT("InventoryPreviousPage"));
    PreviousPageButton->SetContent(Text(TEXT("‹")));StyleButton(PreviousPageButton);PreviousPageButton->OnClicked.AddDynamic(this,&UAnomaliaInventoryWidget::PreviousPage);Pages->AddChildToHorizontalBox(PreviousPageButton);
    PageStatus=Text(TEXT(""),11);Pages->AddChildToHorizontalBox(PageStatus)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    NextPageButton=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),TEXT("InventoryNextPage"));
    NextPageButton->SetContent(Text(TEXT("›")));StyleButton(NextPageButton);NextPageButton->OnClicked.AddDynamic(this,&UAnomaliaInventoryWidget::NextPage);Pages->AddChildToHorizontalBox(NextPageButton);

    BankPanel=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("BankPanel"));Full(BankPanel);
    BankPanel->AddChildToVerticalBox(Text(TEXT("COMPTE & TRANSFERTS"),17))->SetPadding(FMargin(0,0,0,10));
    BankStatus=Text(TEXT(""));BankPanel->AddChildToVerticalBox(BankStatus)->SetPadding(FMargin(0,0,0,16));
    BankRecipient=WidgetTree->ConstructWidget<UEditableTextBox>(UEditableTextBox::StaticClass(),TEXT("BankRecipient"));BankRecipient->SetHintText(FText::FromString(TEXT("Compte destinataire")));BankPanel->AddChildToVerticalBox(BankRecipient)->SetPadding(FMargin(0,5));
    BankAmount=WidgetTree->ConstructWidget<UEditableTextBox>(UEditableTextBox::StaticClass(),TEXT("BankAmount"));BankAmount->SetHintText(FText::FromString(TEXT("Montant EUR : 10,50")));BankPanel->AddChildToVerticalBox(BankAmount)->SetPadding(FMargin(0,5));
    TransferButton=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),TEXT("BankTransfer"));TransferButton->SetContent(Text(TEXT("TRANSFÉRER")));StyleButton(TransferButton);TransferButton->OnClicked.AddDynamic(this,&UAnomaliaInventoryWidget::TransferMoney);BankPanel->AddChildToVerticalBox(TransferButton)->SetPadding(FMargin(0,5));
    auto* BankScroll=WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass());BankPanel->AddChildToVerticalBox(BankScroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    BankWithdrawals=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());BankScroll->AddChild(BankWithdrawals);

    CraftPanel=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("CraftPanel"));Full(CraftPanel);
    CraftPanel->AddChildToVerticalBox(Text(TEXT("FABRICATION À LA MAIN"),18))->SetPadding(FMargin(0,0,0,12));
    auto* CraftScroll=WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass());CraftPanel->AddChildToVerticalBox(CraftScroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    CraftList=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("CraftRecipes"));CraftScroll->AddChild(CraftList);

    auto* Center=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    auto* CenterSlot=RootCanvas->AddChildToCanvas(Center);CenterSlot->SetAnchors(FAnchors(.35f,.008f,.65f,.08f));CenterSlot->SetOffsets(FMargin(0));
    MoneyStatus=Text(TEXT("ESPÈCES —"),23);MoneyStatus->SetJustification(ETextJustify::Center);MoneyStatus->SetColorAndOpacity(FSlateColor(FLinearColor(.95f,.90f,.70f)));MoneyStatus->SetShadowOffset(FVector2D(1,2));MoneyStatus->SetShadowColorAndOpacity(FLinearColor(0,0,0,.9f));Center->AddChildToVerticalBox(MoneyStatus);
    BankBalanceStatus=Text(TEXT("Compte en cours de chargement"),12);BankBalanceStatus->SetJustification(ETextJustify::Center);BankBalanceStatus->SetShadowOffset(FVector2D(1,1));BankBalanceStatus->SetShadowColorAndOpacity(FLinearColor(0,0,0,.9f));Center->AddChildToVerticalBox(BankBalanceStatus);
    HandsList=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("HandsItems"));
    Panel(TEXT("HandsFrame"),FAnchors(.35f,.51f,.65f,.83f))->SetContent(HandsList);
    DetailsList=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("SelectedItemActions"));
    Panel(TEXT("SelectionFrame"),FAnchors(.35f,.66f,.65f,.965f))->SetContent(DetailsList);
    UseStatus=Text(TEXT(""),12);auto* StatusSlot=RootCanvas->AddChildToCanvas(UseStatus);StatusSlot->SetAnchors(FAnchors(.35f,.96f,.65f,.995f));StatusSlot->SetOffsets(FMargin(0));
    ShowInventoryTab();
}

void UAnomaliaInventoryWidget::ShowInventoryTab()
{
    if(CraftPanel)CraftPanel->SetVisibility(ESlateVisibility::Collapsed);if(CraftTab)StyleButton(CraftTab,false);
    bBankTab=false;if(StoragePanel)StoragePanel->SetVisibility(ESlateVisibility::Visible);if(BankPanel)BankPanel->SetVisibility(ESlateVisibility::Collapsed);
    if(InventoryTab)StyleButton(InventoryTab,true);if(BankTab)StyleButton(BankTab,false);
}
void UAnomaliaInventoryWidget::ShowBankTab()
{
    if(CraftPanel)CraftPanel->SetVisibility(ESlateVisibility::Collapsed);if(CraftTab)StyleButton(CraftTab,false);
    bBankTab=true;if(StoragePanel)StoragePanel->SetVisibility(ESlateVisibility::Collapsed);if(BankPanel)BankPanel->SetVisibility(ESlateVisibility::Visible);
    if(InventoryTab)StyleButton(InventoryTab,false);if(BankTab)StyleButton(BankTab,true);
}

void UAnomaliaInventoryWidget::BeginCharacterView()
{
    auto* PC=GetOwningPlayer();auto* Pawn=GetOwningPlayerPawn();if(!PC||!Pawn||PreviewCamera||!GetWorld())return;
    PreviousViewTarget=PC->GetViewTarget();const FVector Target=Pawn->GetActorLocation();
    FVector Position=Target+Pawn->GetActorForwardVector()*500.f+FVector(0,0,15);
    FHitResult Hit;FCollisionQueryParams Params(SCENE_QUERY_STAT(InventoryCamera),false,Pawn);
    if(GetWorld()->LineTraceSingleByChannel(Hit,Target,Position,ECC_Camera,Params))Position=Hit.Location+Hit.Normal*12.f;
    FActorSpawnParameters Spawn;Spawn.ObjectFlags|=RF_Transient;
    PreviewCamera=GetWorld()->SpawnActor<ACameraActor>(Position,(Target-Position).Rotation(),Spawn);
    if(!PreviewCamera)return;
    PreviewCamera->GetCameraComponent()->SetFieldOfView(45.f);PreviewCamera->GetCameraComponent()->bConstrainAspectRatio=false;
    auto* Fill=NewObject<UPointLightComponent>(PreviewCamera);Fill->SetupAttachment(PreviewCamera->GetRootComponent());Fill->SetIntensity(1800.f);Fill->SetAttenuationRadius(650.f);Fill->SetCastShadows(false);Fill->RegisterComponent();Fill->SetWorldLocation(Target+Pawn->GetActorForwardVector()*160.f+FVector(0,0,100));
    PC->SetViewTarget(PreviewCamera);
    HidePreviewPickupPrompts();
}
void UAnomaliaInventoryWidget::EndCharacterView()
{
    if(auto* PC=GetOwningPlayer())for(const auto& Hidden:PreviewHiddenPickups)if(auto* Actor=Hidden.Get())PC->HiddenActors.Remove(Actor);
    if(auto* PC=GetOwningPlayer())PC->HiddenActors.RemoveAll([](const auto& Actor){return !IsValid(Actor.Get());});
    PreviewHiddenPickups.Reset();
    if(PreviewCamera)
    {
        if(auto* PC=GetOwningPlayer();PC&&PC->GetViewTarget()==PreviewCamera)PC->SetViewTarget(IsValid(PreviousViewTarget)?PreviousViewTarget.Get():GetOwningPlayerPawn());
        PreviewCamera->Destroy();PreviewCamera=nullptr;
    }
    PreviousViewTarget=nullptr;
}
void UAnomaliaInventoryWidget::RefreshEquipment()
{
    if(!EquipmentList)return;EquipmentList->ClearChildren();
    auto* User=Cast<AAnomaliaSurvivor>(GetOwningPlayerPawn());if(!User)return;
    auto* Strip=WidgetTree->ConstructWidget<UWrapBox>(UWrapBox::StaticClass());EquipmentList->AddChildToVerticalBox(Strip);
    for(const FName Id:{FName(TEXT("worn_head")),FName(TEXT("worn_top")),FName(TEXT("worn_vest")),FName(TEXT("worn_gloves")),FName(TEXT("worn_legs")),FName(TEXT("worn_feet")),FName(TEXT("worn_back"))})
      if(auto* Icon=GarmentIcon(Id)){auto* Image=Thumbnail(Icon,60);Image->SetToolTipText(FText::FromString(ContainerLabel(Id)));Strip->AddChildToWrapBox(Image)->SetPadding(FMargin(2));}
}

void UAnomaliaInventoryWidget::AddGridStack(const FAnomaliaInventoryStack& Stack)
{
    if(!ActiveGrid||!Inventory)return;const FIntPoint Size=Inventory->GetItemSize(Stack.ItemId,Stack.bRotated);
    auto* Button=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),MakeUniqueObjectName(WidgetTree,UButton::StaticClass(),FName(*FString::Printf(TEXT("InventoryTile_%d"),Stack.StackId))));StyleButton(Button,SelectedStackId==Stack.StackId);
    const int32 TileFontSize=FMath::Clamp(FMath::FloorToInt(GridCellSize*.2f),12,22);
    auto* Tile=WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());Button->SetContent(Tile);
    if(auto* Icon=ItemIcon(Stack.ItemId))
    {
      auto* Fit=WidgetTree->ConstructWidget<UScaleBox>(UScaleBox::StaticClass());Fit->SetStretch(EStretch::ScaleToFit);Fit->SetContent(Thumbnail(Icon,128));Tile->AddChildToOverlay(Fit)->SetHorizontalAlignment(HAlign_Fill); 
    }
    else
    {
      auto* Label=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Label->SetText(FText::FromString(Inventory->GetItemDisplayName(Stack.ItemId)));
      auto Font=Label->GetFont();Font.Size=FMath::Max(9,TileFontSize-2);Label->SetFont(Font);Label->SetAutoWrapText(true);Label->SetClipping(EWidgetClipping::ClipToBounds);
      auto* S=Tile->AddChildToOverlay(Label);S->SetPadding(FMargin(3,2,2,14));S->SetVerticalAlignment(VAlign_Center);
    }
    auto* Quantity=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Quantity->SetText(FText::FromString(FString::Printf(TEXT("×%d"),Stack.Count)));auto Font=Quantity->GetFont();Font.Size=11;Font.TypefaceFontName=TEXT("Bold");Quantity->SetFont(Font);Quantity->SetShadowOffset(FVector2D(1,1));Quantity->SetShadowColorAndOpacity(FLinearColor::Black);auto* Q=Tile->AddChildToOverlay(Quantity);Q->SetHorizontalAlignment(HAlign_Right);Q->SetVerticalAlignment(VAlign_Bottom);Q->SetPadding(FMargin(2));
    Button->SetToolTipText(FText::FromString(FString::Printf(TEXT("%s ×%d · %d×%d cases"),*Inventory->GetItemDisplayName(Stack.ItemId),Stack.Count,Size.X,Size.Y)));
    auto* LayoutSlot=ActiveGrid->AddChildToCanvas(Button);LayoutSlot->SetPosition(FVector2D(Stack.X*GridCellSize+1,Stack.Y*GridCellSize+1));LayoutSlot->SetSize(FVector2D(Size.X*GridCellSize-2,Size.Y*GridCellSize-2));LayoutSlot->SetZOrder(1);
    BindAction(Button,EAnomaliaInventoryAction::SelectStack,Stack.StackId);
    auto TileStyle=Button->GetStyle();TileStyle.NormalPadding=FMargin(1.f);TileStyle.PressedPadding=FMargin(1.f);Button->SetStyle(TileStyle);
}


void UAnomaliaInventoryWidget::RefreshInventory()
{
    if (!ItemList || !WidgetTree) return;
    const auto* Previous=FocusedAction();const bool HadFocus=Previous!=nullptr;
    const auto PreviousAction=Previous?Previous->Action:EAnomaliaInventoryAction::Stow;
    const int32 PreviousStack=Previous?Previous->StackId:0,PreviousOther=Previous?Previous->OtherStackId:0;
    ActionRelays.Reset();
    ItemList->ClearChildren();
    if(DetailsList)DetailsList->ClearChildren();
    if(HandsList)HandsList->ClearChildren();
    if(BankWithdrawals)BankWithdrawals->ClearChildren();
    RefreshEquipment();
    RefreshCrafting();
    if (!Inventory)
    {
        UTextBlock* Missing = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        Missing->SetText(FText::FromString(TEXT("Inventaire indisponible.")));
        ItemList->AddChildToVerticalBox(Missing);
        return;
    }

    if(MoneyStatus)MoneyStatus->SetText(FText::FromString(FString::Printf(TEXT("ESPÈCES  %lld,%02lld €"),static_cast<long long>(Inventory->CashBalanceCents/100),static_cast<long long>(Inventory->CashBalanceCents%100))));
    if(BankBalanceStatus)BankBalanceStatus->SetText(FText::FromString(Inventory->BankAccountId.IsEmpty()?TEXT("Compte en cours de chargement"):FString::Printf(TEXT("BANQUE  %lld,%02lld €"),static_cast<long long>(Inventory->BankBalanceCents/100),static_cast<long long>(Inventory->BankBalanceCents%100))));
    if(UseStatus) UseStatus->SetText(FText::FromString(Inventory->UseMessage));
    if (BankStatus)
        BankStatus->SetText(FText::FromString(FString::Printf(TEXT("BANQUE RP · Compte %s · %lld,%02lld EUR\n%s %s"),
            *Inventory->BankAccountId, static_cast<long long>(Inventory->BankBalanceCents/100),
            static_cast<long long>(Inventory->BankBalanceCents%100),
            Inventory->bBankingAvailable ? TEXT("Terminal connecté") : TEXT("Terminal hors de portée"), *Inventory->BankMessage)));
    if (TransferButton) TransferButton->SetIsEnabled(Inventory->bBankingAvailable);
    if (Inventory->bBankingAvailable)
    {
        UVerticalBox* Withdrawals = BankWithdrawals;
        for (int32 Euros : {5,10,20,50,100,200,500})
        {
            UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), MakeUniqueObjectName(WidgetTree, UButton::StaticClass(), FName(*FString::Printf(TEXT("BankWithdraw_eur_note_%d_action"), Euros))));
            UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
            Text->SetText(FText::FromString(FString::Printf(TEXT("Retirer %d EUR"), Euros))); Button->SetContent(Text);
            Button->SetIsEnabled(Inventory->BankBalanceCents >= Euros*100);
            StyleButton(Button);Withdrawals->AddChildToVerticalBox(Button)->SetPadding(FMargin(3.f));
            BindAction(Button, EAnomaliaInventoryAction::WithdrawNote, 0, Euros);
        }
    }
    RefreshVehicleProximity();
    const float Weight = Inventory->GetCurrentWeightKg();
    int32 StoredStacks=0;
    for(const auto& Stack:Inventory->Stacks)if(Stack.ContainerId!=TEXT("hands"))++StoredStacks;
    PageCount=FMath::Max(1,FMath::DivideAndRoundUp(StoredStacks,ItemsPerPage));
    CurrentPage=FMath::Clamp(CurrentPage,0,PageCount-1);
    if(PageStatus)PageStatus->SetText(FText::FromString(FString::Printf(TEXT("Page %d / %d · %d piles"),CurrentPage+1,PageCount,StoredStacks)));
    if(PreviousPageButton)PreviousPageButton->SetIsEnabled(CurrentPage>0);
    if(NextPageButton)NextPageButton->SetIsEnabled(CurrentPage+1<PageCount);
    for(UWidget* W:{static_cast<UWidget*>(PreviousPageButton),static_cast<UWidget*>(NextPageButton),static_cast<UWidget*>(PageStatus)})if(W)W->SetVisibility(PageCount>1?ESlateVisibility::Visible:ESlateVisibility::Collapsed);
    if(WeightStatus)WeightStatus->SetText(FText::FromString(FString::Printf(TEXT("CHARGE  %.1f / %.1f KG"),Weight,Inventory->WeightCapacityKg)));
    if(!Inventory->Stacks.ContainsByPredicate([&](const auto& Stack){return Stack.StackId==SelectedStackId;}))
        SelectedStackId=0;
    auto* PersonalTarget=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
    auto* PersonalLabel=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());PersonalLabel->SetText(FText::FromString(TEXT("Ranger")));auto SmallFont=PersonalLabel->GetFont();SmallFont.Size=12;PersonalLabel->SetFont(SmallFont);PersonalTarget->SetContent(PersonalLabel);StyleButton(PersonalTarget);PersonalTarget->SetVisibility(Inventory->Stacks.ContainsByPredicate([](const auto& S){return S.ContainerId==TEXT("hands");})?ESlateVisibility::Visible:ESlateVisibility::Collapsed);ItemList->AddChildToVerticalBox(PersonalTarget)->SetPadding(FMargin(0,0,0,8));
    BindAction(PersonalTarget,EAnomaliaInventoryAction::Stow,0);
    int32 StoredIndex=0,BoxIndex=0;
    for (const FAnomaliaInventoryCompartment& Box : Inventory->Compartments)
    {
        const int32 ContainerIndex=BoxIndex++;
        const bool Expanded=ExpandedContainers.Contains(Box.Id)?ExpandedContainers[Box.Id]:(Box.Id!=TEXT("pockets")||Inventory->GetUsedCells(Box.Id)>0);
        auto* Header=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),MakeUniqueObjectName(WidgetTree,UButton::StaticClass(),FName(*(TEXT("Container_")+Box.Id.ToString()+TEXT("_action")))));
        auto* Title=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        Title->SetText(FText::FromString(FString::Printf(TEXT("%s (%d/%d)  %s"),*ContainerLabel(Box.Id).ToUpper(),Inventory->GetUsedCells(Box.Id),Box.Width*Box.Height,Expanded?TEXT("−"):TEXT("+"))));
        auto HeaderFont=Title->GetFont();HeaderFont.Size=13;HeaderFont.TypefaceFontName=TEXT("Bold");Title->SetFont(HeaderFont);Title->SetAutoWrapText(true);
        auto* HeaderRow=WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());Header->SetContent(HeaderRow);
        if(auto* Icon=GarmentIcon(Box.Id))HeaderRow->AddChildToHorizontalBox(Thumbnail(Icon,24))->SetPadding(FMargin(0,0,5,0));
        auto* TitleSlot=HeaderRow->AddChildToHorizontalBox(Title);TitleSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));TitleSlot->SetVerticalAlignment(VAlign_Center);
        ItemList->AddChildToVerticalBox(Header)->SetPadding(FMargin(0,7,0,1));BindAction(Header,EAnomaliaInventoryAction::ToggleContainer,0,0,ContainerIndex);auto HS=Header->GetStyle();HS.Normal=FSlateColorBrush(FLinearColor(.13f,.13f,.13f,.70f));Header->SetStyle(HS);
        if(!Expanded){for(const auto& S:Inventory->Stacks)if(S.ContainerId==Box.Id)++StoredIndex;continue;}
        auto* GridSize=WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
        const float ViewportScale=FMath::Max(.1f,UWidgetLayoutLibrary::GetViewportScale(this));
        const float VirtualWidth=UWidgetLayoutLibrary::GetViewportSize(this).X/ViewportScale;
        GridCellSize=FMath::Clamp((VirtualWidth*.28f-12.f)/FMath::Max(1,Box.Width),18.f,96.f);
        int32 VisibleRows=2;for(const auto& S:Inventory->Stacks)if(S.ContainerId==Box.Id)VisibleRows=FMath::Max(VisibleRows,S.Y+Inventory->GetItemSize(S.ItemId,S.bRotated).Y+1);
        VisibleRows=FMath::Min(Box.Height,VisibleRows);
        GridSize->SetWidthOverride(Box.Width*GridCellSize);GridSize->SetHeightOverride(VisibleRows*GridCellSize);
        ActiveGrid=WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());GridSize->SetContent(ActiveGrid);
        ItemList->AddChildToVerticalBox(GridSize)->SetHorizontalAlignment(HAlign_Center);
        for(int32 Y=0;Y<VisibleRows;++Y)for(int32 X=0;X<Box.Width;++X)
        {
            auto* Cell=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());Cell->SetBrush(FSlateColorBrush(FLinearColor(.16f,.16f,.16f,.30f)));Cell->SetVisibility(ESlateVisibility::HitTestInvisible);
            auto* LayoutSlot=ActiveGrid->AddChildToCanvas(Cell);LayoutSlot->SetPosition(FVector2D(X*GridCellSize+1,Y*GridCellSize+1));LayoutSlot->SetSize(FVector2D(GridCellSize-2,GridCellSize-2));
        }
        for (const FAnomaliaInventoryStack& Stack : Inventory->Stacks)
        {
            if (Stack.ContainerId != Box.Id) continue;
            const int32 Index=StoredIndex++;
            if(Index<CurrentPage*ItemsPerPage || Index>=(CurrentPage+1)*ItemsPerPage)continue;
            AddGridStack(Stack);
        }
    }
    ActiveGrid=nullptr;
    auto* HandsTitle=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());HandsTitle->SetText(FText::FromString(TEXT("MAINS")));auto HandsFont=HandsTitle->GetFont();HandsFont.Size=14;HandsTitle->SetFont(HandsFont);HandsTitle->SetJustification(ETextJustify::Center);
    auto* HandsBand=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());HandsBand->SetBrush(FSlateColorBrush(FLinearColor(.45f,.45f,.45f,.75f)));HandsBand->SetContent(HandsTitle);HandsList->AddChildToVerticalBox(HandsBand);
    bool HasHeld=false;
    for(const auto& Stack:Inventory->Stacks)if(Stack.ContainerId==TEXT("hands"))
    {
        HasHeld=true;auto* Button=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());StyleButton(Button,Stack.StackId==SelectedStackId);
        auto* Content=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());Button->SetContent(Content);
        auto* Text=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Text->SetText(FText::FromString(FString::Printf(TEXT("%s ×%d"),*Inventory->GetItemDisplayName(Stack.ItemId),Stack.Count)));auto Font=Text->GetFont();Font.Size=13;Text->SetFont(Font);Text->SetJustification(ETextJustify::Center);Content->AddChildToVerticalBox(Text);
        if(auto* Icon=ItemIcon(Stack.ItemId))Content->AddChildToVerticalBox(Thumbnail(Icon,150))->SetHorizontalAlignment(HAlign_Center);
        HandsList->AddChildToVerticalBox(Button);BindAction(Button,EAnomaliaInventoryAction::SelectStack,Stack.StackId);
    }
    if(auto* Frame=HandsList->GetParent())if(auto* Layout=Cast<UCanvasPanelSlot>(Frame->Slot))Layout->SetAnchors(HasHeld?FAnchors(.35f,.51f,.65f,.85f):FAnchors(.35f,.51f,.65f,.56f));
    const auto* Selected=Inventory->Stacks.FindByPredicate([&](const auto& Stack){return Stack.StackId==SelectedStackId;});
    if(DetailsList&&DetailsList->GetParent())DetailsList->GetParent()->SetVisibility(Selected?ESlateVisibility::Visible:ESlateVisibility::Collapsed);
    if(Selected)AddStackRow(*Selected);
    if(HadFocus && GetOwningPlayer())
    {
        UButton* Fallback=nullptr;
        for(const auto& Relay:ActionRelays)
        {
            if(Relay->Action==EAnomaliaInventoryAction::Stow&&Relay->StackId==0)Fallback=Relay->Button;
            if(Relay->Button->IsVisible()&&Relay->Action==PreviousAction&&Relay->StackId==PreviousStack&&Relay->OtherStackId==PreviousOther)
            {Relay->Button->SetUserFocus(GetOwningPlayer());return;}
        }
        if(Fallback)Fallback->SetUserFocus(GetOwningPlayer());
    }
}

void UAnomaliaInventoryWidget::AddStackRow(const FAnomaliaInventoryStack& Stack)
{
    UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(),
        MakeUniqueObjectName(WidgetTree,UHorizontalBox::StaticClass(),FName(*FString::Printf(TEXT("InventoryStack_%d_row"),Stack.StackId))));
    DetailsList->AddChildToVerticalBox(Row)->SetPadding(FMargin(12.f, 3.f));
    UTextBlock* Label = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    const FIntPoint Size=Inventory->GetItemSize(Stack.ItemId,Stack.bRotated);
    Label->SetText(FText::FromString(FString::Printf(TEXT("%s ×%d"), *Inventory->GetItemDisplayName(Stack.ItemId), Stack.Count)));
    Label->SetColorAndOpacity(FSlateColor(FLinearColor(.91f, .95f, .96f)));
    auto Font=Label->GetFont();Font.Size=13;Label->SetFont(Font);Label->SetAutoWrapText(true);
    Row->AddChildToHorizontalBox(Label)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

    const FString UseLabel=Inventory->GetUseActionLabel(Stack.ItemId);
    if(!UseLabel.IsEmpty())
    {
        auto* UseButton=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),
            MakeUniqueObjectName(WidgetTree,UButton::StaticClass(),FName(*FString::Printf(TEXT("UseStack_%d_action"),Stack.StackId))));
        auto* UseText=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        UseText->SetText(FText::FromString(UseLabel));UseButton->SetContent(UseText);
        UseButton->SetIsEnabled(!Inventory->IsPersistenceLocked());
        Row->AddChildToHorizontalBox(UseButton)->SetPadding(FMargin(5.f));
        BindAction(UseButton,EAnomaliaInventoryAction::Use,Stack.StackId,Stack.Count);
    }

    if (Inventory && Inventory->bBankingAvailable && Stack.ItemId.ToString().StartsWith(TEXT("eur_note_")))
    {
        UButton* Deposit = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), MakeUniqueObjectName(WidgetTree, UButton::StaticClass(), FName(*FString::Printf(TEXT("BankDeposit_%d_action"), Stack.StackId))));
        UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        Text->SetText(FText::FromString(TEXT("Déposer 1 billet"))); Deposit->SetContent(Text);
        Row->AddChildToHorizontalBox(Deposit)->SetPadding(FMargin(5.f));
        BindAction(Deposit, EAnomaliaInventoryAction::DepositNote, Stack.StackId);
    }
    UButton* HandsButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
    UTextBlock* HandsLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    if(NearbyVehicle && NearbyVehicle->SurvivalSystems->HasOpenPanel(TEXT("trunk")) && !NearbyVehicle->SurvivalSystems->State.bLocked)
    {
        auto* Deposit=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
        auto* Text=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Text->SetText(FText::FromString(TEXT("Déposer au coffre")));Deposit->SetContent(Text);Row->AddChildToHorizontalBox(Deposit);
        BindAction(Deposit,EAnomaliaInventoryAction::VehicleService,Stack.StackId,Stack.Count,static_cast<int32>(EAnomaliaVehicleServiceAction::Deposit));
    }
    const bool bHeld = Stack.ContainerId == TEXT("hands");
    HandsLabel->SetText(FText::FromString(bHeld ? TEXT("Ranger") : TEXT("Mains")));
    HandsButton->SetContent(HandsLabel);
    Row->AddChildToHorizontalBox(HandsButton)->SetPadding(FMargin(5.f));
    BindAction(HandsButton, bHeld ? EAnomaliaInventoryAction::Stow : EAnomaliaInventoryAction::MoveToHands, Stack.StackId);

    if(!bHeld && Size.X!=Size.Y)
    {
        auto* RotateButton=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),
            MakeUniqueObjectName(WidgetTree,UButton::StaticClass(),FName(*FString::Printf(TEXT("RotateStack_%d_action"),Stack.StackId))));
        auto* RotateLabel=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        RotateLabel->SetText(FText::FromString(TEXT("Tourner 90°")));RotateButton->SetContent(RotateLabel);
        RotateButton->SetIsEnabled(!Inventory->IsPersistenceLocked());
        Row->AddChildToHorizontalBox(RotateButton)->SetPadding(FMargin(5.f));
        BindAction(RotateButton,EAnomaliaInventoryAction::Rotate,Stack.StackId);
    }

    if (Stack.Count > 1)
    {
        UButton* SplitButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
        UTextBlock* SplitLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        SplitLabel->SetText(FText::FromString(TEXT("½ pile")));
        SplitButton->SetContent(SplitLabel);
        Row->AddChildToHorizontalBox(SplitButton)->SetPadding(FMargin(5.f));
        BindAction(SplitButton, EAnomaliaInventoryAction::SplitHalf, Stack.StackId, Stack.Count / 2);
    }

    const FAnomaliaInventoryStack* Matching = Inventory->Stacks.FindByPredicate([&](const FAnomaliaInventoryStack& Other)
    {
        return Other.ItemId == Stack.ItemId && Other.StackId != Stack.StackId && Other.ContainerId != TEXT("hands") && Stack.ContainerId != TEXT("hands");
    });
    if (Matching)
    {
        UButton* MergeButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
        UTextBlock* MergeLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        MergeLabel->SetText(FText::FromString(TEXT("Fusionner")));
        MergeButton->SetContent(MergeLabel);
        Row->AddChildToHorizontalBox(MergeButton)->SetPadding(FMargin(5.f));
        BindAction(MergeButton, EAnomaliaInventoryAction::Merge, Stack.StackId, 0, Matching->StackId);
    }
    auto* Destinations=WidgetTree->ConstructWidget<UWrapBox>(UWrapBox::StaticClass());Destinations->SetExplicitWrapSize(true);Destinations->SetWrapSize(UWidgetLayoutLibrary::GetViewportSize(this).X/FMath::Max(.1f,UWidgetLayoutLibrary::GetViewportScale(this))*.88f);DetailsList->AddChildToVerticalBox(Destinations)->SetPadding(FMargin(8,6));
    for(int32 I=0;I<Inventory->Compartments.Num();++I)
    {
        const auto& Box=Inventory->Compartments[I];if(Box.bRecoveryOnly||Box.Id==Stack.ContainerId)continue;
        auto* Button=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());auto* Text=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Text->SetText(FText::FromString(ContainerLabel(Box.Id)));auto Small=Text->GetFont();Small.Size=12;Text->SetFont(Small);Button->SetContent(Text);Destinations->AddChildToWrapBox(Button)->SetPadding(FMargin(3));BindAction(Button,EAnomaliaInventoryAction::StowInContainer,Stack.StackId,0,I);
    }

}

void UAnomaliaInventoryWidget::BindAction(UButton* Button, EAnomaliaInventoryAction Action, int32 StackId, int32 Count, int32 OtherStackId)
{
    if (!Button) return;
    StyleButton(Button,Action==EAnomaliaInventoryAction::SelectStack && StackId==SelectedStackId);
    UAnomaliaInventoryActionRelay* Relay = NewObject<UAnomaliaInventoryActionRelay>(this);
    Relay->TargetWidget = this;
    Relay->Button=Button;
    Relay->Action = Action;
    Relay->StackId = StackId;
    Relay->Count = Count;
    Relay->OtherStackId = OtherStackId;
    ActionRelays.Add(Relay);
    Button->OnClicked.AddDynamic(Relay, &UAnomaliaInventoryActionRelay::Execute);
}

void UAnomaliaInventoryWidget::PerformAction(EAnomaliaInventoryAction Action, int32 StackId, int32 Count, int32 OtherStackId)
{
    if (!Inventory) return;
    switch (Action)
    {
        case EAnomaliaInventoryAction::CollectNearby:
        {
            if(NearbyPickups.IsValidIndex(OtherStackId))
            {
                auto* Pickup=NearbyPickups[OtherStackId].Get();
                Inventory->RequestCollectNearby(Pickup);
                RefreshInventory();
            }
            break;
        }
        case EAnomaliaInventoryAction::CraftRecipe:
        {
            const auto& Recipes=UAnomaliaInventoryComponent::GetHandcraftRecipes();
            if(Recipes.IsValidIndex(OtherStackId))Inventory->RequestCraftRecipe(Recipes[OtherStackId].Id);break;
        }
        case EAnomaliaInventoryAction::ToggleContainer:
            if(Inventory->Compartments.IsValidIndex(OtherStackId))
            {const auto& Box=Inventory->Compartments[OtherStackId];const bool Was=ExpandedContainers.Contains(Box.Id)?ExpandedContainers[Box.Id]:(Box.Id!=TEXT("pockets")||Inventory->GetUsedCells(Box.Id)>0);ExpandedContainers.Add(Box.Id,!Was);RefreshInventory();}break;
        case EAnomaliaInventoryAction::StowInContainer:
            if(Inventory->Compartments.IsValidIndex(OtherStackId))
            {const FName Id=Inventory->Compartments[OtherStackId].Id;ExpandedContainers.Add(Id,true);Inventory->RequestStowStackIn(StackId,Id);}break;
        case EAnomaliaInventoryAction::SelectStack:
            SelectedStackId=StackId;RefreshInventory();break;
        case EAnomaliaInventoryAction::VehicleService:
            if(OtherStackId==int32(EAnomaliaVehicleServiceAction::Deposit) && StackId==0)
            {
                const auto* Held=Inventory->Stacks.FindByPredicate([](const auto& Stack){return Stack.ContainerId==TEXT("hands");});
                if(!Held)break;StackId=Held->StackId;Count=Held->Count;
            }
            if(auto* User=Cast<AAnomaliaSurvivor>(GetOwningPlayerPawn()))
                User->RequestVehicleService(NearbyVehicle,static_cast<EAnomaliaVehicleServiceAction>(OtherStackId),StackId,Count);
            break;
        case EAnomaliaInventoryAction::MoveToHands:
            Inventory->RequestMoveStack(StackId, TEXT("hands"), 0, 0, false);
            FocusFirstAction();
            break;
        case EAnomaliaInventoryAction::Stow:
            if(StackId==0)
            {
                const auto* Held=Inventory->Stacks.FindByPredicate([](const auto& Stack){return Stack.ContainerId==TEXT("hands");});
                if(!Held)break;StackId=Held->StackId;
            }
            Inventory->RequestStowStack(StackId);
            FocusFirstAction();
            break;
        case EAnomaliaInventoryAction::Rotate:
        {
            const auto* Stack=Inventory->Stacks.FindByPredicate([&](const auto& S){return S.StackId==StackId;});
            if(Stack)Inventory->RequestMoveStack(StackId,Stack->ContainerId,Stack->X,Stack->Y,!Stack->bRotated);
            FocusFirstAction();
            break;
        }
        case EAnomaliaInventoryAction::SplitHalf:
            Inventory->RequestSplitStack(StackId, Count);
            break;
        case EAnomaliaInventoryAction::Merge:
            Inventory->RequestMergeStacks(StackId, OtherStackId);
            break;
        case EAnomaliaInventoryAction::Use:
            Inventory->RequestUseStack(StackId,Count);
            FocusFirstAction();
            break;
        case EAnomaliaInventoryAction::DepositNote:
        {
            const auto* Stack = Inventory->Stacks.FindByPredicate([&](const auto& Row) { return Row.StackId == StackId; });
            if (Stack) Inventory->RequestBankOperation(EAnomaliaBankAction::Deposit, Stack->ItemId);
            break;
        }
        case EAnomaliaInventoryAction::WithdrawNote:
            Inventory->RequestBankOperation(EAnomaliaBankAction::Withdraw, FName(*FString::Printf(TEXT("eur_note_%d"), Count)));
            break;
        default:
            break;
    }
}

void UAnomaliaInventoryWidget::TransferMoney()
{
    if (!Inventory || !BankRecipient || !BankAmount || !BankStatus) return;
    FString Input = BankAmount->GetText().ToString().TrimStartAndEnd().Replace(TEXT(","), TEXT("."));
    FString Whole, Fraction;
    if (!Input.Split(TEXT("."), &Whole, &Fraction)) Whole = Input;
    const auto Digits = [](const FString& Text)
    { for (TCHAR C : Text) if (C < '0' || C > '9') return false; return true; };
    if (Whole.IsEmpty() || Whole.Len() > 10 || Fraction.Len() > 2 || !Digits(Whole) || !Digits(Fraction))
    { BankStatus->SetText(FText::FromString(TEXT("Montant invalide : utilisez un nombre positif, avec deux décimales au maximum."))); return; }
    if (Fraction.Len() == 1) Fraction += TEXT("0");
    const int64 Amount = FCString::Atoi64(*Whole)*100 + (Fraction.IsEmpty() ? 0 : FCString::Atoi64(*Fraction));
    Inventory->RequestBankOperation(EAnomaliaBankAction::Transfer, NAME_None, BankRecipient->GetText().ToString().TrimStartAndEnd(), Amount);
}

void UAnomaliaInventoryWidget::FocusFirstAction()
{
    if (CloseButton && GetOwningPlayer()) CloseButton->SetUserFocus(GetOwningPlayer());
}

void UAnomaliaInventoryWidget::PreviousPage()
{
    if(CurrentPage<=0)return;
    --CurrentPage;RefreshInventory();
    if(PreviousPageButton && PreviousPageButton->GetIsEnabled() && GetOwningPlayer())PreviousPageButton->SetUserFocus(GetOwningPlayer());
    else FocusFirstAction();
}
void UAnomaliaInventoryWidget::NextPage()
{
    if(CurrentPage+1>=PageCount)return;
    ++CurrentPage;RefreshInventory();
    if(NextPageButton && NextPageButton->GetIsEnabled() && GetOwningPlayer())NextPageButton->SetUserFocus(GetOwningPlayer());
    else FocusFirstAction();
}

void UAnomaliaInventoryWidget::CloseInventory()
{
    if (auto* Survivor = Cast<AAnomaliaSurvivor>(GetOwningPlayerPawn()))
        Survivor->CloseInventory();
}

FReply UAnomaliaInventoryWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    if(Event.GetKey()==EKeys::PageUp || Event.GetKey()==EKeys::Gamepad_LeftShoulder)
    { PreviousPage();return FReply::Handled(); }
    if(Event.GetKey()==EKeys::PageDown || Event.GetKey()==EKeys::Gamepad_RightShoulder)
    { NextPage();return FReply::Handled(); }
    if (Event.GetKey() == EKeys::Gamepad_FaceButton_Right || Event.GetKey() == EKeys::Gamepad_Special_Left || Event.GetKey() == EKeys::Escape)
    {
        CloseInventory();
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(Geometry, Event);
}

void UAnomaliaInventoryWidget::AddVehicleButton(const FString& Label,int32 ServiceAction,int32 StackId,int32 Count)
{
 auto* Button=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
 auto* Text=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Text->SetText(FText::FromString(Label));Text->SetAutoWrapText(true);Button->SetContent(Text);
 ProximityList->AddChildToVerticalBox(Button)->SetPadding(FMargin(8.f,4.f));
 BindAction(Button,EAnomaliaInventoryAction::VehicleService,StackId,Count,ServiceAction);
}
TArray<AAnomaliaLootPickup*> UAnomaliaInventoryWidget::FindNearbyPickups() const
{
 TArray<AAnomaliaLootPickup*> Found;
 const auto* User=GetOwningPlayerPawn();auto* World=GetWorld();if(!User||!World)return Found;
 for(TActorIterator<AAnomaliaLootPickup> It(World);It;++It)
 {
  auto* Pickup=*It;if(!IsValid(Pickup)||Pickup->Count<=0||Pickup->ItemId.IsNone()||
   FVector::DistSquared(User->GetActorLocation(),Pickup->GetActorLocation())>FMath::Square(250.f))continue;
  FHitResult Hit;FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaInventoryProximity),false,User);Query.AddIgnoredActor(Pickup);
  if(!World->LineTraceSingleByChannel(Hit,User->GetActorLocation()+FVector(0,0,50),Pickup->GetActorLocation(),ECC_Visibility,Query))Found.Add(Pickup);
 }
 Found.Sort([&](const AAnomaliaLootPickup& A,const AAnomaliaLootPickup& B)
 {const double DA=FVector::DistSquared(User->GetActorLocation(),A.GetActorLocation()),DB=FVector::DistSquared(User->GetActorLocation(),B.GetActorLocation());return DA==DB?A.GetUniqueID()<B.GetUniqueID():DA<DB;});
 if(Found.Num()>64)Found.SetNum(64);return Found;
}
void UAnomaliaInventoryWidget::NativeTick(const FGeometry& Geometry,float DeltaTime)
{
 Super::NativeTick(Geometry,DeltaTime);IconDelay+=DeltaTime;if(IconDelay>.15f){CaptureNextIcon();IconDelay=0;}
 ProximityElapsed+=DeltaTime;if(ProximityElapsed<.5f)return;ProximityElapsed=0;HidePreviewPickupPrompts();
 FString Signature;for(const auto* P:FindNearbyPickups())Signature+=FString::Printf(TEXT("%u:%s:%d;"),P->GetUniqueID(),*P->ItemId.ToString(),P->Count);
 if(Signature!=ProximitySignature){ProximitySignature=MoveTemp(Signature);RefreshInventory();}
}
void UAnomaliaInventoryWidget::RefreshVehicleProximity()
{
 if(!ProximityList||!GetWorld())return;ProximityList->ClearChildren();
 auto* User=Cast<AAnomaliaSurvivor>(GetOwningPlayerPawn());AAnomaliaChaosRoadVehicle* Nearest=nullptr;double Distance=FMath::Square(200.f);
 if(User)for(TActorIterator<AAnomaliaChaosRoadVehicle> It(GetWorld());It;++It)
 {
  auto* Vehicle=*It;if(!Vehicle->SurvivalSystems->bEnabled)continue;
  const double Candidate=Vehicle->Body->Bounds.GetBox().ComputeSquaredDistanceToPoint(User->GetActorLocation());
  if(Candidate<Distance){Distance=Candidate;Nearest=Vehicle;}
 }
 if(NearbyVehicle!=Nearest)
 {
  if(NearbyVehicle){NearbyVehicle->CargoInventory->OnInventoryUpdated.RemoveDynamic(this,&UAnomaliaInventoryWidget::RefreshInventory);NearbyVehicle->SurvivalSystems->OnServicesUpdated.RemoveDynamic(this,&UAnomaliaInventoryWidget::RefreshInventory);}
  NearbyVehicle=Nearest;
  if(NearbyVehicle){NearbyVehicle->CargoInventory->OnInventoryUpdated.AddDynamic(this,&UAnomaliaInventoryWidget::RefreshInventory);NearbyVehicle->SurvivalSystems->OnServicesUpdated.AddDynamic(this,&UAnomaliaInventoryWidget::RefreshInventory);}
 }
 auto Label=[&](const FString& Value){auto* Text=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Text->SetText(FText::FromString(Value));auto Font=Text->GetFont();Font.Size=14;Text->SetFont(Font);Text->SetAutoWrapText(true);auto* Band=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());Band->SetBrush(FSlateColorBrush(FLinearColor(.45f,.45f,.45f,.7f)));Band->SetPadding(FMargin(5,3));Text->SetJustification(ETextJustify::Center);Band->SetContent(Text);ProximityList->AddChildToVerticalBox(Band)->SetPadding(FMargin(0,0,0,2));};
 Label(TEXT("À PROXIMITÉ"));
 NearbyPickups.Reset();
 auto* NearbyIcons=WidgetTree->ConstructWidget<UWrapBox>(UWrapBox::StaticClass());ProximityList->AddChildToVerticalBox(NearbyIcons);
 for(auto* Pickup:FindNearbyPickups())
 {
  const int32 Index=NearbyPickups.Add(Pickup);
  auto* Button=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
  auto* Tile=WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
  auto* Size=WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());Size->SetWidthOverride(70);Size->SetHeightOverride(70);Size->SetContent(Tile);Button->SetContent(Size);
  if(auto* Icon=ItemIcon(Pickup->ItemId))Tile->AddChildToOverlay(Thumbnail(Icon,66));
  else{auto* Name=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Name->SetText(FText::FromString(Inventory->GetItemDisplayName(Pickup->ItemId)));auto Font=Name->GetFont();Font.Size=11;Name->SetFont(Font);Name->SetAutoWrapText(true);Tile->AddChildToOverlay(Name)->SetVerticalAlignment(VAlign_Center);}
  auto* Count=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Count->SetText(FText::FromString(FString::Printf(TEXT("%d"),Pickup->Count)));auto Font=Count->GetFont();Font.Size=11;Count->SetFont(Font);auto* CountSlot=Tile->AddChildToOverlay(Count);CountSlot->SetHorizontalAlignment(HAlign_Right);CountSlot->SetVerticalAlignment(VAlign_Bottom);
  Button->SetToolTipText(FText::FromString(TEXT("Prendre")));
  NearbyIcons->AddChildToWrapBox(Button)->SetPadding(FMargin(1));
  BindAction(Button,EAnomaliaInventoryAction::CollectNearby,0,0,Index);
 }
 if(NearbyPickups.IsEmpty())Label(TEXT("Vide"));
 if(!NearbyVehicle)return;
 Label(TEXT("VÉHICULE / COFFRE"));
 const auto* Systems=NearbyVehicle->SurvivalSystems.Get();const auto& State=Systems->State;
 Label(State.bLocked?TEXT("Véhicule verrouillé — clé correspondante requise."):TEXT("Véhicule déverrouillé"));
 if(!Systems->bReady){Label(TEXT("Chargement de la sauvegarde du véhicule…"));return;}
 using Action=EAnomaliaVehicleServiceAction;
 if(!State.bKeyIssued)AddVehicleButton(TEXT("Récupérer la clé d’origine"),int32(Action::TakeInitialKey));
 AddVehicleButton(State.bLocked?TEXT("Déverrouiller avec ma clé"):TEXT("Verrouiller avec ma clé"),int32(Action::ToggleLock));
 if(State.bLocked)return;
 auto Piece=[&](const TCHAR* Name,bool Present,Action Install,Action Remove){AddVehicleButton(FString(Name)+(Present?TEXT(" · retirer"):TEXT(" · emplacement vide : installer")),int32(Present?Remove:Install));};
 if(Systems->HasOpenPanel(TEXT("hood")))
 {
  Label(TEXT("CAPOT — PIÈCES FONCTIONNELLES"));Piece(TEXT("Radiateur"),State.bRadiator,Action::InstallRadiator,Action::RemoveRadiator);
  Piece(TEXT("Bougie d’allumage"),State.bSparkPlug,Action::InstallSparkPlug,Action::RemoveSparkPlug);
  AddVehicleButton(FString::Printf(TEXT("Liquide de refroidissement : %.0f %% · remplir avec de l’eau"),State.Coolant*100),int32(Action::FillCoolant));
 }
 else Label(TEXT("Ouvrez le capot pour accéder au radiateur et à l’allumage."));
 if(Systems->HasOpenPanel(Systems->BatteryAccessPanel))Piece(TEXT("Batterie"),State.bBattery,Action::InstallBattery,Action::RemoveBattery);
 if(!Systems->HasOpenPanel(TEXT("trunk"))){Label(TEXT("Ouvrez la malle pour accéder à la cargaison."));return;}
 const auto* Cargo=NearbyVehicle->CargoInventory.Get();int32 Cells=0;for(const auto& Box:Cargo->Compartments)Cells+=Box.Width*Box.Height;
 Label(FString::Printf(TEXT("COFFRE · %d cases · %.1f / %.1f kg"),Cells,Cargo->GetCurrentWeightKg(),Cargo->WeightCapacityKg));
 AddVehicleButton(TEXT("Déposer"),int32(Action::Deposit));
 for(const auto& Stack:Cargo->Stacks)
  AddVehicleButton(FString::Printf(TEXT("%s ×%d"),*Cargo->GetItemDisplayName(Stack.ItemId),Stack.Count),int32(Action::Withdraw),Stack.StackId,Stack.Count);
}
UAnomaliaInventoryActionRelay* UAnomaliaInventoryWidget::FocusedAction() const
{for(const auto& Relay:ActionRelays)if(Relay&&Relay->Button&&Relay->Button->HasUserFocus(GetOwningPlayer()))return Relay.Get();return nullptr;}
FReply UAnomaliaInventoryWidget::NativeOnPreviewKeyDown(const FGeometry& Geometry,const FKeyEvent& Event)
{
 const auto Key=Event.GetKey();
 // Consume plain Tab before Slate moves focus; Shift+Tab still navigates controls.
 if(Key==EKeys::Tab&&!Event.IsShiftDown()&&!Event.IsControlDown()&&!Event.IsAltDown()&&!Event.IsCommandDown())
 {
  if(!Event.IsRepeat())CloseInventory();
  return FReply::Handled();
 }
 auto* Focus=FocusedAction();
 if(Key==EKeys::Gamepad_FaceButton_Left&&Focus)
 {
  if(Focus->Action==EAnomaliaInventoryAction::VehicleService)
  {
   auto Action=static_cast<EAnomaliaVehicleServiceAction>(Focus->OtherStackId);
   if(Action==EAnomaliaVehicleServiceAction::Withdraw)Action=EAnomaliaVehicleServiceAction::WithdrawToHands;
   if(Action==EAnomaliaVehicleServiceAction::WithdrawToHands||Action==EAnomaliaVehicleServiceAction::Deposit)
   {PerformAction(EAnomaliaInventoryAction::VehicleService,Focus->StackId,Focus->Count,int32(Action));return FReply::Handled();}
  }
  if(Focus->Action==EAnomaliaInventoryAction::MoveToHands||Focus->Action==EAnomaliaInventoryAction::Stow)
  {
   const auto* Stack=Inventory?Inventory->Stacks.FindByPredicate([&](const auto& S){return S.StackId==Focus->StackId;}):nullptr;
   if(Stack)PerformAction(Stack->ContainerId==TEXT("hands")?EAnomaliaInventoryAction::VehicleService:EAnomaliaInventoryAction::MoveToHands,Stack->StackId,Stack->Count,int32(EAnomaliaVehicleServiceAction::Deposit));
   return FReply::Handled();
  }
 }
 if(Key==EKeys::Gamepad_FaceButton_Bottom)
 {
  if(DraggedStackId)return FReply::Handled();
  if(Focus&&Focus->StackId>0)
  {
   bDraggingFromVehicle=Focus->Action==EAnomaliaInventoryAction::VehicleService&&Focus->OtherStackId==int32(EAnomaliaVehicleServiceAction::Withdraw);
   if(bDraggingFromVehicle){DraggedStackId=Focus->StackId;DraggedCount=Focus->Count;return FReply::Handled();}
   if(Focus->Action==EAnomaliaInventoryAction::MoveToHands||Focus->Action==EAnomaliaInventoryAction::Stow)
   {
    const auto* Stack=Inventory->Stacks.FindByPredicate([&](const auto& S){return S.StackId==Focus->StackId;});
    if(Stack){DraggedStackId=Stack->StackId;DraggedCount=Stack->Count;return FReply::Handled();}
   }
  }
 }
 return Super::NativeOnPreviewKeyDown(Geometry,Event);
}
FReply UAnomaliaInventoryWidget::NativeOnKeyUp(const FGeometry& Geometry,const FKeyEvent& Event)
{
 if(Event.GetKey()!=EKeys::Gamepad_FaceButton_Bottom||!DraggedStackId)return Super::NativeOnKeyUp(Geometry,Event);
 const int32 Stack=DraggedStackId,Count=DraggedCount;DraggedStackId=DraggedCount=0;
 const auto* Focus=FocusedAction();if(!Focus)return FReply::Handled();
 if(bDraggingFromVehicle)
 {
  if(Focus->Action!=EAnomaliaInventoryAction::VehicleService)
   PerformAction(EAnomaliaInventoryAction::VehicleService,Stack,Count,int32(Focus->Action==EAnomaliaInventoryAction::MoveToHands?EAnomaliaVehicleServiceAction::WithdrawToHands:EAnomaliaVehicleServiceAction::Withdraw));
 }
 else if(Focus->Action==EAnomaliaInventoryAction::VehicleService)
 {
  const auto Action=static_cast<EAnomaliaVehicleServiceAction>(Focus->OtherStackId);
  if(Action==EAnomaliaVehicleServiceAction::Deposit||Action==EAnomaliaVehicleServiceAction::Withdraw||Action==EAnomaliaVehicleServiceAction::InstallBattery||Action==EAnomaliaVehicleServiceAction::InstallRadiator||Action==EAnomaliaVehicleServiceAction::InstallSparkPlug)
   PerformAction(EAnomaliaInventoryAction::VehicleService,Stack,Count,int32(Action==EAnomaliaVehicleServiceAction::Withdraw?EAnomaliaVehicleServiceAction::Deposit:Action));
 }
 else if(Focus->Action==EAnomaliaInventoryAction::MoveToHands)PerformAction(EAnomaliaInventoryAction::MoveToHands,Stack,Count,0);
 return FReply::Handled();
}




FString UAnomaliaInventoryWidget::ContainerLabel(FName Id) const
{
    static const TMap<FName,FString> Labels={
        {TEXT("pockets"),TEXT("Poches")},{TEXT("worn_top"),TEXT("Veste")},
        {TEXT("worn_legs"),TEXT("Pantalon")},{TEXT("worn_back"),TEXT("Sac à dos")},
        {TEXT("worn_vest"),TEXT("Gilet")},{TEXT("worn_head"),TEXT("Coiffure")},
        {TEXT("worn_gloves"),TEXT("Gants")},{TEXT("worn_feet"),TEXT("Chaussures")}
    };
    const auto* Label=Labels.Find(Id);return Label?*Label:Id.ToString();
}
void UAnomaliaInventoryWidget::ShowCraftTab()
{
    bBankTab=false;if(StoragePanel)StoragePanel->SetVisibility(ESlateVisibility::Collapsed);
    if(BankPanel)BankPanel->SetVisibility(ESlateVisibility::Collapsed);if(CraftPanel)CraftPanel->SetVisibility(ESlateVisibility::Visible);
    if(InventoryTab)StyleButton(InventoryTab,false);if(BankTab)StyleButton(BankTab,false);if(CraftTab)StyleButton(CraftTab,true);
}
void UAnomaliaInventoryWidget::RefreshCrafting()
{
    if(!CraftList||!Inventory)return;CraftList->ClearChildren();int32 RecipeIndex=0;
    for(const auto& Recipe:UAnomaliaInventoryComponent::GetHandcraftRecipes())
    {
        auto* Card=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
        Card->SetBrush(FSlateRoundedBoxBrush(FLinearColor(.055f,.055f,.055f,.6f),0.f,FLinearColor(.3f,.3f,.3f,.3f),0.f,FVector2D(16,16)));Card->SetPadding(FMargin(12));
        CraftList->AddChildToVerticalBox(Card)->SetPadding(FMargin(0,0,0,12));
        auto* Content=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());Card->SetContent(Content);
        auto* Title=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Title->SetText(FText::FromString(Recipe.Label));auto Font=Title->GetFont();Font.Size=18;Font.TypefaceFontName=TEXT("Bold");Title->SetFont(Font);Content->AddChildToVerticalBox(Title)->SetPadding(FMargin(0,0,0,8));
        FString Cost;TArray<FName> Keys;Recipe.Materials.GetKeys(Keys);Keys.Sort(FNameLexicalLess());
        for(const auto Key:Keys)
        {
            int32 Have=0;for(const auto& S:Inventory->Stacks)if(S.ItemId==Key&&!Inventory->IsRecoveryContainer(S.ContainerId))Have+=S.Count;
            if(!Cost.IsEmpty())Cost+=TEXT("\n");Cost+=FString::Printf(TEXT("%s  %d / %d"),*Inventory->GetItemDisplayName(Key),Have,Recipe.Materials[Key]);
        }
        auto* Ingredients=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Ingredients->SetText(FText::FromString(Cost));auto Small=Ingredients->GetFont();Small.Size=13;Ingredients->SetFont(Small);Content->AddChildToVerticalBox(Ingredients)->SetPadding(FMargin(0,0,0,10));
        auto* Button=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),MakeUniqueObjectName(WidgetTree,UButton::StaticClass(),FName(*(TEXT("CraftRecipe_")+Recipe.Id.ToString()+TEXT("_action")))));
        auto* Label=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Label->SetText(FText::FromString(TEXT("FABRIQUER")));Label->SetFont(Small);Button->SetContent(Label);
        Button->SetToolTipText(FText::FromString(TEXT("Fabriquer : ")+Recipe.Label));Button->SetIsEnabled(Inventory->HasCraftMaterials(Recipe.Id));Content->AddChildToVerticalBox(Button);
        BindAction(Button,EAnomaliaInventoryAction::CraftRecipe,0,0,RecipeIndex++);
    }
}



USkeletalMeshComponent* UAnomaliaInventoryWidget::WornMesh(FName Id) const
{
 auto* User=Cast<AAnomaliaSurvivor>(GetOwningPlayerPawn());if(!User)return nullptr;
 if(Id==TEXT("worn_top"))return User->JacketMesh;
 if(Id==TEXT("worn_legs"))return User->PantsMesh;
 if(Id==TEXT("worn_back"))return User->BackpackMesh;
 if(Id==TEXT("worn_gloves"))return User->GlovesMesh;
 if(Id==TEXT("worn_feet"))return User->BootsMesh;
 if(Id==TEXT("worn_head"))return User->HeadgearMesh;
 if(Id==TEXT("worn_vest"))return User->VestMesh;
 return nullptr;
}
void UAnomaliaInventoryWidget::HidePreviewPickupPrompts()
{
 auto* PC=GetOwningPlayer();if(!PC||!PreviewCamera||!GetWorld())return;
 // Camera-local only: no actor/component visibility or server state is modified.
 for(TActorIterator<AAnomaliaLootPickup> It(GetWorld());It;++It)
  if(IsValid(*It)&&!PC->HiddenActors.Contains(*It)){PC->HiddenActors.Add(*It);PreviewHiddenPickups.Add(*It);}
}
UTextureRenderTarget2D* UAnomaliaInventoryWidget::QueueIcon(FName Key,UPrimitiveComponent* Source,const FString& Signature)
{
 if(!Source||!GetWorld()||GetWorld()->GetNetMode()==NM_DedicatedServer)return nullptr;
 if(const auto* Existing=IconTextures.Find(Key))
 {
  if(IconSignatures.FindRef(Key)!=Signature){IconSignatures.Add(Key,Signature);IconComponents.Add(Key,Source);PendingIcons.AddUnique(Key);}
  return Existing->Get();
 }
 // Bounded, client-only snapshots; no continual render or asset writes.
 if(IconTextures.Num()>=32)return nullptr;
 auto* Target=NewObject<UTextureRenderTarget2D>(this,NAME_None,RF_Transient);
 Target->ClearColor=FLinearColor(0,0,0,1);Target->InitCustomFormat(256,256,PF_B8G8R8A8,false);
 Target->UpdateResourceImmediate(true);IconTextures.Add(Key,Target);IconComponents.Add(Key,Source);
 IconSignatures.Add(Key,Signature);PendingIcons.AddUnique(Key);return Target;
}
UTextureRenderTarget2D* UAnomaliaInventoryWidget::GarmentIcon(FName Id)
{
 auto* Part=WornMesh(Id);if(!Part||!Part->GetSkeletalMeshAsset())return nullptr;
 FString Signature=Part->GetSkeletalMeshAsset()->GetPathName();
 for(int32 I=0;I<Part->GetNumMaterials();++I)if(auto* M=Part->GetMaterial(I))Signature+=M->GetPathName();
 return QueueIcon(Id,Part,Signature);
}
UTextureRenderTarget2D* UAnomaliaInventoryWidget::ItemIcon(FName Id)
{
 const FName Key(*(TEXT("item_")+Id.ToString()));
 if(auto* Existing=IconTextures.Find(Key))return Existing->Get();
 if(MissingIconItems.Contains(Id))return nullptr;
 // Exact installed, audited geometry. Never substitute another item or pack.
 static const TMap<FName,FString> Sources={
  {TEXT("apple"),TEXT("/Game/Anomalia/ImportedFab/Batch_40571935754/ph_food_apple_01/Source_0/food_apple_01_4k/StaticMeshes/food_apple_01_4k")},
  {TEXT("canned_beans"),TEXT("/Game/Anomalia/ImportedFab/Batch_40571935754/ph_long_life_food/Source_2/long_life_food_4k/StaticMeshes/long_life_food_beans")}
 };
 const auto* Source=Sources.Find(Id);
 if(!Source||!FPackageName::DoesPackageExist(*Source)){MissingIconItems.Add(Id);return nullptr;}
 auto* Mesh=LoadObject<UStaticMesh>(nullptr,**Source);if(!Mesh){MissingIconItems.Add(Id);return nullptr;}
 if(!IconPreviewActor)
 {
  FActorSpawnParameters Params;Params.ObjectFlags|=RF_Transient;
  IconPreviewActor=GetWorld()->SpawnActor<AActor>(FVector(0,0,100000),FRotator::ZeroRotator,Params);
 }
 if(!IconPreviewActor)return nullptr;
 auto* Part=NewObject<UStaticMeshComponent>(IconPreviewActor,NAME_None,RF_Transient);
 Part->SetStaticMesh(Mesh);Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);Part->SetGenerateOverlapEvents(false);
 Part->SetCastShadow(false);Part->SetVisibleInSceneCaptureOnly(true);Part->SetWorldLocation(FVector(0,0,100000));
 IconPreviewActor->AddInstanceComponent(Part);Part->RegisterComponent();
 return QueueIcon(Key,Part,Mesh->GetPathName());
}
UWidget* UAnomaliaInventoryWidget::Thumbnail(UTextureRenderTarget2D* Texture,float Size)
{
 auto* Box=WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());Box->SetWidthOverride(Size);Box->SetHeightOverride(Size);
 auto* Image=WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
 FSlateBrush Brush;Brush.SetResourceObject(Texture);Brush.ImageSize=FVector2D(256,256);Image->SetBrush(Brush);Box->SetContent(Image);return Box;
}
void UAnomaliaInventoryWidget::CaptureNextIcon()
{
 if(PendingIcons.IsEmpty()||!GetWorld())return;
 if(!IconCapture)
 {
  FActorSpawnParameters Params;Params.ObjectFlags|=RF_Transient;
  IconCapture=GetWorld()->SpawnActor<ASceneCapture2D>(FVector::ZeroVector,FRotator::ZeroRotator,Params);
  if(!IconCapture)return;
  auto* Capture=IconCapture->GetCaptureComponent2D();Capture->bCaptureEveryFrame=false;Capture->bCaptureOnMovement=false;
  Capture->PrimitiveRenderMode=ESceneCapturePrimitiveRenderMode::PRM_UseShowOnlyList;
  Capture->ProjectionType=ECameraProjectionMode::Orthographic;Capture->CaptureSource=ESceneCaptureSource::SCS_FinalColorLDR;
  Capture->ShowFlags.SetLighting(false);Capture->ShowFlags.SetAtmosphere(false);Capture->ShowFlags.SetFog(false);
  Capture->ShowFlags.SetBloom(false);Capture->ShowFlags.SetMotionBlur(false);
 }
 const FName Key=PendingIcons[0];PendingIcons.RemoveAt(0);
 auto* Part=IconComponents.FindRef(Key).Get();auto* Target=IconTextures.FindRef(Key).Get();if(!IsValid(Part)||!Target)return;
 FBoxSphereBounds Bounds=Part->Bounds;
 if(auto* Skel=Cast<USkeletalMeshComponent>(Part);Skel&&Skel->GetSkeletalMeshAsset())
  Bounds=Skel->GetSkeletalMeshAsset()->GetBounds().TransformBy(Skel->GetComponentTransform());
 auto* Capture=IconCapture->GetCaptureComponent2D();
 const float Extent=FMath::Max3(Bounds.BoxExtent.X,Bounds.BoxExtent.Y,Bounds.BoxExtent.Z);
 FVector Direction=GetOwningPlayerPawn()?GetOwningPlayerPawn()->GetActorForwardVector():FVector::ForwardVector;
 if(Key==TEXT("worn_back"))Direction=-Direction;
 if(Key.ToString().StartsWith(TEXT("item_")))Direction=FVector(1,1,.35f).GetSafeNormal();
 const FVector Location=Bounds.Origin+Direction*FMath::Max(100.f,Extent*4.f);
 Capture->SetWorldLocationAndRotation(Location,(Bounds.Origin-Location).Rotation());Capture->OrthoWidth=FMath::Max(2.f,Extent*2.5f);
 Capture->TextureTarget=Target;Capture->ClearShowOnlyComponents();Capture->ShowOnlyComponent(Part);
 Capture->CaptureScene();++IconCaptureCount;
}
void UAnomaliaInventoryWidget::ReleaseIcons()
{
 if(IconCapture){IconCapture->Destroy();IconCapture=nullptr;}
 if(IconPreviewActor){IconPreviewActor->Destroy();IconPreviewActor=nullptr;}
 PendingIcons.Reset();IconComponents.Reset();IconTextures.Reset();IconSignatures.Reset();MissingIconItems.Reset();
}
