#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaBankTerminal.generated.h"
class UStaticMeshComponent;
class UTextRenderComponent;
/** Functional terminal interaction point; its generic mesh is provisional. */
UCLASS()
class ANOMALIAPRIMEVAL_API AAnomaliaBankTerminal : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaBankTerminal();
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Mesh;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UTextRenderComponent> Label;
};
