#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaZPrigimaliaBankTerminal.generated.h"
class UStaticMeshComponent;
class UTextRenderComponent;
/** Functional terminal interaction point; its generic mesh is provisional. */
UCLASS()
class ANOMALIAZPRIGIMALIA_API AAnomaliaZPrigimaliaBankTerminal : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaZPrigimaliaBankTerminal();
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Mesh;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UTextRenderComponent> Label;
};
