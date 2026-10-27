#include "AnomaliaPlaceSign.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"

AAnomaliaPlaceSign::AAnomaliaPlaceSign()
{
    RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    Board=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Board"));Board->SetupAttachment(RootComponent);
    Board->SetCollisionProfileName(TEXT("BlockAll"));
    FrontText=CreateDefaultSubobject<UTextRenderComponent>(TEXT("FrontText"));FrontText->SetupAttachment(RootComponent);
    BackText=CreateDefaultSubobject<UTextRenderComponent>(TEXT("BackText"));BackText->SetupAttachment(RootComponent);
    FrontText->SetRelativeLocation(FVector(5,0,200));BackText->SetRelativeLocation(FVector(-5,0,200));
    BackText->SetRelativeRotation(FRotator(0,180,0));
    for(auto* Text:{FrontText.Get(),BackText.Get()})
    {
        Text->SetHorizontalAlignment(EHTA_Center);Text->SetVerticalAlignment(EVRTA_TextCenter);
        Text->SetTextRenderColor(FColor(12,18,20));Text->SetWorldSize(22);
        Text->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
}
bool AAnomaliaPlaceSign::SnapToGround(float ExpectedGroundZCm)
{
    if(!GetWorld() || !FMath::IsFinite(ExpectedGroundZCm)) return false;
    const FVector P=GetActorLocation();FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaSignGround),true,this);
    FHitResult Hit;
    if(!GetWorld()->LineTraceSingleByChannel(Hit,FVector(P.X,P.Y,ExpectedGroundZCm+500),
        FVector(P.X,P.Y,ExpectedGroundZCm-500),ECC_WorldStatic,Query) ||
        FMath::Abs(Hit.ImpactPoint.Z-ExpectedGroundZCm)>150 || Hit.ImpactNormal.Z<.94 || Hit.ImpactPoint.Z<500) return false;
    SetActorLocation(Hit.ImpactPoint);return true;
}
void AAnomaliaPlaceSign::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    for(auto* Text:{FrontText.Get(),BackText.Get()})
    {
        Text->SetText(PlaceName);
        // Long labels remain inside a 2.8 metre plate; this does not rescale the board.
        const int32 Length=FMath::Max(1,PlaceName.ToString().Len());
        Text->SetWorldSize(FMath::Min(22.f,380.f/Length));
    }
}
