#include "AnomaliaZPrigimaliaBankTerminal.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"
AAnomaliaZPrigimaliaBankTerminal::AAnomaliaZPrigimaliaBankTerminal()
{
    bReplicates = true; SetReplicateMovement(true);
    Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("TerminalMesh")); SetRootComponent(Mesh);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Box(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Box.Succeeded()) Mesh->SetStaticMesh(Box.Object);
    Mesh->SetRelativeScale3D(FVector(.5f, .5f, 1.f));
    Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Label = CreateDefaultSubobject<UTextRenderComponent>(TEXT("BankLabel")); Label->SetupAttachment(Mesh);
    Label->SetAbsolute(false, false, true); Label->SetRelativeLocation(FVector(0,0,65));
    Label->SetWorldSize(18); Label->SetHorizontalAlignment(EHTA_Center);
    Label->SetText(FText::FromString(TEXT("BANQUE RP  /  Inventaire [I]")));
}
