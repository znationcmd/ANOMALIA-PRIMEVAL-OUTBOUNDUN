#include "AnomaliaInventoryWidget.h"
#include "AnomaliaInventoryComponent.h"
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
    Super::NativeDestruct();
}

void UAnomaliaInventoryWidget::StyleButton(UButton* Button,bool bSelected)
{
    FButtonStyle Style=Button->GetStyle();
    Style.Normal=FSlateColorBrush(bSelected?FLinearColor(.025f,.22f,.27f,.97f):FLinearColor(.025f,.055f,.07f,.94f));
    Style.Hovered=FSlateColorBrush(FLinearColor(.035f,.28f,.34f));
    Style.Pressed=FSlateColorBrush(FLinearColor(.02f,.4f,.48f));
    Style.Disabled=FSlateColorBrush(FLinearColor(.035f,.045f,.055f,.7f));
    Style.NormalPadding=FMargin(8.f,6.f);Style.PressedPadding=Style.NormalPadding;
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
        T->SetText(FText::FromString(Value));T->SetColorAndOpacity(FSlateColor(FLinearColor(.8f,.91f,.93f)));
        auto Font=T->GetFont();Font.Size=Size;T->SetFont(Font);T->SetAutoWrapText(true);return T;
    };
    auto Panel=[&](FName Name,const FAnchors& Anchors){
        auto* B=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(),Name);
        B->SetBrush(FSlateColorBrush(FLinearColor(.008f,.025f,.035f,.91f)));
        B->SetPadding(FMargin(10.f));auto* LayoutSlot=RootCanvas->AddChildToCanvas(B);
        LayoutSlot->SetAnchors(Anchors);LayoutSlot->SetOffsets(FMargin(0));LayoutSlot->SetZOrder(1);return B;
    };
    auto* Top=WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
    Panel(TEXT("InventoryHeader"),FAnchors(.025f,.035f,.975f,.12f))->SetContent(Top);
    Top->AddChildToHorizontalBox(Text(TEXT("ANOMALIA  /  ÉQUIPEMENT"),20))->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    auto Tab=[&](FName Name,const FString& Label){auto* B=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),Name);B->SetContent(Text(Label));StyleButton(B);Top->AddChildToHorizontalBox(B)->SetPadding(FMargin(4,0));return B;};
    InventoryTab=Tab(TEXT("InventoryTab"),TEXT("INVENTAIRE"));InventoryTab->OnClicked.AddDynamic(this,&UAnomaliaInventoryWidget::ShowInventoryTab);
    BankTab=Tab(TEXT("BankTab"),TEXT("BANQUE"));BankTab->OnClicked.AddDynamic(this,&UAnomaliaInventoryWidget::ShowBankTab);
    CloseButton=Tab(TEXT("InventoryClose"),TEXT("FERMER  [TAB / ÉCHAP]"));CloseButton->OnClicked.AddDynamic(this,&UAnomaliaInventoryWidget::CloseInventory);

    auto* NearbyScroll=WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(),TEXT("ProximityScroll"));
    Panel(TEXT("NearbyFrame"),FAnchors(.025f,.15f,.285f,.81f))->SetContent(NearbyScroll);
    ProximityList=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("VehicleProximity"));NearbyScroll->AddChild(ProximityList);

    auto* Right=WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
    Panel(TEXT("StorageFrame"),FAnchors(.715f,.15f,.975f,.81f))->SetContent(Right);
    auto Full=[&](UWidget* W){auto* S=Right->AddChildToCanvas(W);S->SetAnchors(FAnchors(0,0,1,1));S->SetOffsets(FMargin(0));};
    StoragePanel=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("StoragePanel"));Full(StoragePanel);
    StoragePanel->AddChildToVerticalBox(Text(TEXT("ÉQUIPEMENT PORTÉ"),12));
    EquipmentList=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("EquippedMeshes"));
    StoragePanel->AddChildToVerticalBox(EquipmentList)->SetPadding(FMargin(0,5,0,10));
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

    auto* Center=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
    auto* CenterSlot=RootCanvas->AddChildToCanvas(Center);CenterSlot->SetAnchors(FAnchors(.32f,.15f,.68f,.32f));CenterSlot->SetOffsets(FMargin(0));
    auto* CharacterTitle=Text(TEXT("SURVIVANT  /  TENUE PORTÉE"),14);CharacterTitle->SetJustification(ETextJustify::Center);Center->AddChildToVerticalBox(CharacterTitle);
    HandsList=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("HandsItems"));
    Panel(TEXT("HandsFrame"),FAnchors(.32f,.70f,.68f,.81f))->SetContent(HandsList);
    DetailsList=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("SelectedItemActions"));
    Panel(TEXT("SelectionFrame"),FAnchors(.025f,.84f,.975f,.965f))->SetContent(DetailsList);
    UseStatus=Text(TEXT(""),12);auto* StatusSlot=RootCanvas->AddChildToCanvas(UseStatus);StatusSlot->SetAnchors(FAnchors(.03f,.965f,.97f,1));StatusSlot->SetOffsets(FMargin(0));
    ShowInventoryTab();
}

void UAnomaliaInventoryWidget::ShowInventoryTab()
{
    bBankTab=false;if(StoragePanel)StoragePanel->SetVisibility(ESlateVisibility::Visible);if(BankPanel)BankPanel->SetVisibility(ESlateVisibility::Collapsed);
    if(InventoryTab)StyleButton(InventoryTab,true);if(BankTab)StyleButton(BankTab,false);
}
void UAnomaliaInventoryWidget::ShowBankTab()
{
    bBankTab=true;if(StoragePanel)StoragePanel->SetVisibility(ESlateVisibility::Collapsed);if(BankPanel)BankPanel->SetVisibility(ESlateVisibility::Visible);
    if(InventoryTab)StyleButton(InventoryTab,false);if(BankTab)StyleButton(BankTab,true);
}

void UAnomaliaInventoryWidget::BeginCharacterView()
{
    auto* PC=GetOwningPlayer();auto* Pawn=GetOwningPlayerPawn();if(!PC||!Pawn||PreviewCamera||!GetWorld())return;
    PreviousViewTarget=PC->GetViewTarget();const FVector Target=Pawn->GetActorLocation();
    FVector Position=Target+Pawn->GetActorForwardVector()*580.f+FVector(0,0,15);
    FHitResult Hit;FCollisionQueryParams Params(SCENE_QUERY_STAT(InventoryCamera),false,Pawn);
    if(GetWorld()->LineTraceSingleByChannel(Hit,Target,Position,ECC_Camera,Params))Position=Hit.Location+Hit.Normal*12.f;
    FActorSpawnParameters Spawn;Spawn.ObjectFlags|=RF_Transient;
    PreviewCamera=GetWorld()->SpawnActor<ACameraActor>(Position,(Target-Position).Rotation(),Spawn);
    if(!PreviewCamera)return;
    PreviewCamera->GetCameraComponent()->SetFieldOfView(45.f);PreviewCamera->GetCameraComponent()->bConstrainAspectRatio=false;
    auto* Fill=NewObject<UPointLightComponent>(PreviewCamera);Fill->SetupAttachment(PreviewCamera->GetRootComponent());Fill->SetIntensity(1800.f);Fill->SetAttenuationRadius(650.f);Fill->SetCastShadows(false);Fill->RegisterComponent();Fill->SetWorldLocation(Target+Pawn->GetActorForwardVector()*160.f+FVector(0,0,100));
    PC->SetViewTarget(PreviewCamera);
}
void UAnomaliaInventoryWidget::EndCharacterView()
{
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
    FString Parts;
    auto Add=[&](const TCHAR* Label,USkeletalMeshComponent* Mesh){if(Mesh&&Mesh->GetSkeletalMeshAsset()){if(!Parts.IsEmpty())Parts+=TEXT("  ·  ");Parts+=Label;}};
    Add(TEXT("Veste"),User->JacketMesh);Add(TEXT("Pantalon"),User->PantsMesh);Add(TEXT("Bottes"),User->BootsMesh);Add(TEXT("Gants"),User->GlovesMesh);Add(TEXT("Tête"),User->HeadgearMesh);Add(TEXT("Gilet"),User->VestMesh);Add(TEXT("Sac"),User->BackpackMesh);
    auto* Label=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Label->SetText(FText::FromString(Parts.IsEmpty()?TEXT("Aucun vêtement modulaire porté"):Parts));auto Font=Label->GetFont();Font.Size=11;Label->SetFont(Font);Label->SetAutoWrapText(true);Label->SetJustification(ETextJustify::Center);EquipmentList->AddChildToVerticalBox(Label);
}

void UAnomaliaInventoryWidget::AddGridStack(const FAnomaliaInventoryStack& Stack)
{
    if(!ActiveGrid||!Inventory)return;const FIntPoint Size=Inventory->GetItemSize(Stack.ItemId,Stack.bRotated);
    auto* Button=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),MakeUniqueObjectName(WidgetTree,UButton::StaticClass(),FName(*FString::Printf(TEXT("InventoryTile_%d"),Stack.StackId))));StyleButton(Button,SelectedStackId==Stack.StackId);
    const int32 TileFontSize=FMath::Clamp(FMath::FloorToInt(GridCellSize*.2f),12,22);
    const FString Caption=Inventory->GetItemDisplayName(Stack.ItemId).Left(FMath::Max(3,FMath::FloorToInt(Size.X*GridCellSize/(TileFontSize*.75f))-1));
    auto* Label=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Label->SetText(FText::FromString(FString::Printf(TEXT("%s\n×%d"),*Caption,Stack.Count)));auto Font=Label->GetFont();Font.Size=TileFontSize;Label->SetFont(Font);Label->SetAutoWrapText(true);Label->SetClipping(EWidgetClipping::ClipToBounds);Button->SetContent(Label);
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
    if (!Inventory)
    {
        UTextBlock* Missing = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        Missing->SetText(FText::FromString(TEXT("Inventaire indisponible.")));
        ItemList->AddChildToVerticalBox(Missing);
        return;
    }

    if(UseStatus) UseStatus->SetText(FText::FromString(Inventory->UseMessage));
    if (BankStatus)
        BankStatus->SetText(FText::FromString(FString::Printf(TEXT("BANQUE RP · Compte %s · %lld,%02lld EUR\n%s %s"),
            *Inventory->BankAccountId, static_cast<long long>(Inventory->BankBalanceCents/100),
            static_cast<long long>(Inventory->BankBalanceCents%100),
            Inventory->bBankingAvailable ? TEXT("Terminal à portée.") : TEXT("Approchez-vous d’un terminal bancaire."), *Inventory->BankMessage)));
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
    if(PageStatus)PageStatus->SetText(FText::FromString(FString::Printf(TEXT("Page %d / %d · %d piles · LB/RB"),CurrentPage+1,PageCount,StoredStacks)));
    if(PreviousPageButton)PreviousPageButton->SetIsEnabled(CurrentPage>0);
    if(NextPageButton)NextPageButton->SetIsEnabled(CurrentPage+1<PageCount);
    if(WeightStatus)WeightStatus->SetText(FText::FromString(FString::Printf(TEXT("CHARGE  %.1f / %.1f KG"),Weight,Inventory->WeightCapacityKg)));
    if(!Inventory->Stacks.ContainsByPredicate([&](const auto& Stack){return Stack.StackId==SelectedStackId;}))
        SelectedStackId=Inventory->Stacks.IsEmpty()?0:Inventory->Stacks[0].StackId;
    auto* PersonalTarget=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());
    auto* PersonalLabel=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());PersonalLabel->SetText(FText::FromString(TEXT("RANGER L’OBJET EN MAINS")));auto SmallFont=PersonalLabel->GetFont();SmallFont.Size=12;PersonalLabel->SetFont(SmallFont);PersonalTarget->SetContent(PersonalLabel);StyleButton(PersonalTarget);ItemList->AddChildToVerticalBox(PersonalTarget)->SetPadding(FMargin(0,0,0,8));
    BindAction(PersonalTarget,EAnomaliaInventoryAction::Stow,0);
    int32 StoredIndex=0;
    for (const FAnomaliaInventoryCompartment& Box : Inventory->Compartments)
    {
        UTextBlock* BoxTitle = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        const FString ContainerName=Box.Id==TEXT("pockets")?TEXT("POCHES"):Box.Id.ToString();
        BoxTitle->SetText(FText::FromString(FString::Printf(TEXT("%s  ·  %d × %d · %d / %d cases"), *ContainerName, Box.Width, Box.Height,
            Inventory->GetUsedCells(Box.Id),Box.Width*Box.Height)));
        auto BoxFont=BoxTitle->GetFont();BoxFont.Size=12;BoxTitle->SetFont(BoxFont);
        BoxTitle->SetColorAndOpacity(FSlateColor(FLinearColor(.32f, .86f, .94f)));
        if(Box.bRecoveryOnly) BoxTitle->SetText(FText::FromString(TEXT("RÉCUPÉRATION — retrait uniquement · objets conservés après migration")));
        ItemList->AddChildToVerticalBox(BoxTitle)->SetPadding(FMargin(14.f, 14.f, 8.f, 5.f));
        auto* GridSize=WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
        const float ViewportScale=FMath::Max(.1f,UWidgetLayoutLibrary::GetViewportScale(this));
        const float VirtualWidth=UWidgetLayoutLibrary::GetViewportSize(this).X/ViewportScale;
        GridCellSize=FMath::Clamp((VirtualWidth*.26f-40.f)/FMath::Max(1,Box.Width),18.f,96.f);
        GridSize->SetWidthOverride(Box.Width*GridCellSize);GridSize->SetHeightOverride(Box.Height*GridCellSize);
        ActiveGrid=WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());GridSize->SetContent(ActiveGrid);
        ItemList->AddChildToVerticalBox(GridSize)->SetHorizontalAlignment(HAlign_Center);
        for(int32 Y=0;Y<Box.Height;++Y)for(int32 X=0;X<Box.Width;++X)
        {
            auto* Cell=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());Cell->SetBrush(FSlateColorBrush(FLinearColor(.06f,.13f,.16f,.6f)));Cell->SetVisibility(ESlateVisibility::HitTestInvisible);
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
    auto* HandsTitle=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());HandsTitle->SetText(FText::FromString(TEXT("EN MAINS")));auto HandsFont=HandsTitle->GetFont();HandsFont.Size=12;HandsTitle->SetFont(HandsFont);HandsList->AddChildToVerticalBox(HandsTitle);
    bool HasHeld=false;
    for(const auto& Stack:Inventory->Stacks)if(Stack.ContainerId==TEXT("hands"))
    {
        HasHeld=true;auto* Button=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());StyleButton(Button,Stack.StackId==SelectedStackId);
        auto* Text=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Text->SetText(FText::FromString(FString::Printf(TEXT("%s ×%d"),*Inventory->GetItemDisplayName(Stack.ItemId),Stack.Count)));Button->SetContent(Text);HandsList->AddChildToVerticalBox(Button);BindAction(Button,EAnomaliaInventoryAction::SelectStack,Stack.StackId);
    }
    if(!HasHeld){auto* Empty=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Empty->SetText(FText::FromString(TEXT("Mains libres")));HandsList->AddChildToVerticalBox(Empty);}
    const auto* Selected=Inventory->Stacks.FindByPredicate([&](const auto& Stack){return Stack.StackId==SelectedStackId;});
    if(Selected)AddStackRow(*Selected);
    else{auto* Empty=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Empty->SetText(FText::FromString(TEXT("Sélectionnez un objet pour afficher ses actions.")));DetailsList->AddChildToVerticalBox(Empty);}
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
    Label->SetText(FText::FromString(FString::Printf(TEXT("%s  ×%d · %d×%d cases [%s · %d,%d]"), *Inventory->GetItemDisplayName(Stack.ItemId), Stack.Count,Size.X,Size.Y, *Stack.ContainerId.ToString(), Stack.X, Stack.Y)));
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
 auto Label=[&](const FString& Value){auto* Text=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Text->SetText(FText::FromString(Value));auto Font=Text->GetFont();Font.Size=13;Text->SetFont(Font);Text->SetAutoWrapText(true);ProximityList->AddChildToVerticalBox(Text)->SetPadding(FMargin(10.f,6.f));};
 Label(TEXT("PROXIMITÉ / VÉHICULE"));
 if(!NearbyVehicle){Label(TEXT("Approchez du véhicule puis ouvrez son coffre ou son capot."));return;}
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
 AddVehicleButton(TEXT("Cargaison — déposer ici (maintenir Croix) / objet en mains (Carré)"),int32(Action::Deposit));
 for(const auto& Stack:Cargo->Stacks)
  AddVehicleButton(FString::Printf(TEXT("%s ×%d · prendre (Croix), mains (Carré)"),*Cargo->GetItemDisplayName(Stack.ItemId),Stack.Count),int32(Action::Withdraw),Stack.StackId,Stack.Count);
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

