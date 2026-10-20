#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "AnomaliaFurnitureWidget.generated.h"

class UAnomaliaFurnitureComponent;
class UAnomaliaFurnitureWidget;
class UVerticalBox;
class UTextBlock;
class UButton;

UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaFurnitureActionRelay : public UObject
{
    GENERATED_BODY()
public:
    UPROPERTY() TObjectPtr<UAnomaliaFurnitureWidget> Target;
    FName Action;
    FName Type;
    UFUNCTION() void Execute();
};

/** Native palette for the creative furniture prototype; all mutations still go through server RPCs. */
UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaFurnitureWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    void InitializeForFurniture(UAnomaliaFurnitureComponent* Component);
    void ShowResult(bool bSuccess);
    virtual void NativeConstruct() override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
private:
    friend class UAnomaliaFurnitureActionRelay;
    UPROPERTY() TObjectPtr<UAnomaliaFurnitureComponent> Furniture;
    UPROPERTY() TObjectPtr<UVerticalBox> Confirmation;
    UPROPERTY() TObjectPtr<UTextBlock> Status;
    UPROPERTY() TArray<TObjectPtr<UAnomaliaFurnitureActionRelay>> Relays;
    FString PendingRemovalId;
    void Perform(FName Action, FName Type);
    void AddButton(UVerticalBox* Container, const FText& Label, FName Action, FName Type = NAME_None);
};
