#pragma once
#include "CoreMinimal.h"
#include "Components/StaticMeshComponent.h"
#include "AnomaliaVehiclePanelComponent.generated.h"
class AAnomaliaSurvivor;

/** Separate hinge-centred mesh, moving collision, server-owned motion. */
UCLASS(ClassGroup=(Anomalia),meta=(BlueprintSpawnableComponent))
class ANOMALIAPRIMEVAL_API UAnomaliaVehiclePanelComponent : public UStaticMeshComponent
{
    GENERATED_BODY()
public:
    UAnomaliaVehiclePanelComponent();
    UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="ANOMALIA|Panel") FName PanelId=TEXT("driver_door");
    UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="ANOMALIA|Panel") float OpenAngleDegrees=-70.f;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="ANOMALIA|Panel") float DegreesPerSecond=80.f;
    UPROPERTY(Replicated,VisibleAnywhere,BlueprintReadOnly,Category="ANOMALIA|Panel") bool bOpen=false;
    UPROPERTY(Replicated,EditAnywhere,BlueprintReadOnly,Category="ANOMALIA|Panel") bool bLocked=false;
    UPROPERTY(Replicated,VisibleAnywhere,BlueprintReadOnly,Category="ANOMALIA|Panel") bool bObstructed=false;
    UPROPERTY(ReplicatedUsing=OnRep_Angle,VisibleAnywhere,BlueprintReadOnly,Category="ANOMALIA|Panel") float AngleDegrees=0.f;
    bool TryToggle(AAnomaliaSurvivor* User);
    virtual void TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* Function) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Props) const override;
private:
    UFUNCTION() void OnRep_Angle();
    bool IsPoseBlocked(float Angle) const;
    bool bReceivedAngle=false;
    float VisualAngle=0.f;
};
