#include "AnomaliaLootPickup.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"
#include "Net/UnrealNetwork.h"

AAnomaliaLootPickup::AAnomaliaLootPickup()
{
    bReplicates = true;
    SetReplicateMovement(true);
    Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PickupMesh"));
    SetRootComponent(Mesh);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Box(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Box.Succeeded()) Mesh->SetStaticMesh(Box.Object);
    Mesh->SetRelativeScale3D(FVector(.18f, .18f, .12f));
    Mesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Mesh->SetCollisionResponseToAllChannels(ECR_Ignore);
    Label = CreateDefaultSubobject<UTextRenderComponent>(TEXT("PickupLabel"));
    Label->SetupAttachment(Mesh);
    Label->SetAbsolute(false, false, true);
    Label->SetRelativeLocation(FVector(0, 0, 150));
    Label->SetWorldSize(14.f);
    Label->SetHorizontalAlignment(EHTA_Center);
}
void AAnomaliaLootPickup::Configure(FName Id, int32 Quantity, const FString& Name)
{
    if (!HasAuthority()) return;
    ItemId = Id; Count = Quantity; DisplayName = Name;
    OnRep_Item(); ForceNetUpdate();
}
void AAnomaliaLootPickup::OnRep_Item()
{
    Label->SetText(FText::FromString(FString::Printf(TEXT("%s x%d [Interact]"), *DisplayName, Count)));
}
void AAnomaliaLootPickup::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AAnomaliaLootPickup, ItemId);
    DOREPLIFETIME(AAnomaliaLootPickup, Count);
    DOREPLIFETIME(AAnomaliaLootPickup, DisplayName);
}
