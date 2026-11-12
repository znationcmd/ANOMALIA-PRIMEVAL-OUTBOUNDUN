#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaCityBlock.generated.h"
class UStaticMesh;
class UMaterialInterface;
class USceneComponent;

USTRUCT(BlueprintType)
struct FAnomaliaCityMeshBatch
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="City") TObjectPtr<UStaticMesh> Mesh;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="City") TArray<TObjectPtr<UMaterialInterface>> Materials;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="City") TArray<FTransform> Instances;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="City") bool bVisible=true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="City") bool bCollision=true;
};

/** Original City Sample geometry, materials and authored component transforms. */
UCLASS()
class ANOMALIAPRIMEVAL_API AAnomaliaCityBlock : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaCityBlock();
    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void BeginPlay() override;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="City") TArray<FAnomaliaCityMeshBatch> Batches;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="City") FString SourceWorld;
    UFUNCTION(BlueprintCallable, CallInEditor, Category="City") void RebuildCity();
    UFUNCTION(BlueprintPure, Category="City") int32 GetOriginalInstanceCount() const;
private:
    UPROPERTY(VisibleAnywhere, Category="City") TObjectPtr<USceneComponent> CityRoot;
    UPROPERTY(Transient) TArray<TObjectPtr<USceneComponent>> GeneratedComponents;
};
