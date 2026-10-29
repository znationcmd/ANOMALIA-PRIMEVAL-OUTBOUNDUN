#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaZPrigimaliaDoorActor.generated.h"

class USceneComponent;
class UBoxComponent;
class UStaticMeshComponent;
class AAnomaliaZPrigimaliaSurvivor;

/** Separate moving door leaf. Never turns a sealed exterior scan into an interior. */
UCLASS(Blueprintable)
class ANOMALIAZPRIGIMALIA_API AAnomaliaZPrigimaliaDoorActor : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaZPrigimaliaDoorActor();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Door")
    TObjectPtr<USceneComponent> Hinge;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Door")
    TObjectPtr<UBoxComponent> LeafCollision;
    /** Assign a licensed, separate door mesh. Align its pivot in the Blueprint. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Door")
    TObjectPtr<UStaticMeshComponent> LeafMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Door", meta=(ClampMin="40",ClampMax="400"))
    float WidthCm=118.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Door", meta=(ClampMin="100",ClampMax="500"))
    float HeightCm=218.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Door", meta=(ClampMin="2",ClampMax="30"))
    float ThicknessCm=5.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Door", meta=(ClampMin="-170",ClampMax="170"))
    float OpenAngleDegrees=90.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="ANOMALIA|Door", meta=(ClampMin="10",ClampMax="180"))
    float DegreesPerSecond=90.f;
    UPROPERTY(Replicated, VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Door")
    bool bLocked=false;
    UPROPERTY(ReplicatedUsing=OnRep_Door, VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Door")
    float DoorAngleDegrees=0.f;
    UPROPERTY(Replicated, VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|Door")
    bool bObstructed=false;
    /** Called by trusted server interaction only, with distance and line-of-sight checks. */
    bool TryToggle(AAnomaliaZPrigimaliaSurvivor* User);
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|Door")
    bool SetLockedOnServer(bool bNewLocked);
    virtual void Tick(float DeltaSeconds) override;
    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Props) const override;
private:
    UFUNCTION() void OnRep_Door();
    UPROPERTY(Replicated) bool bTargetOpen=false;
    bool IsPoseBlocked(float Angle) const;
};
