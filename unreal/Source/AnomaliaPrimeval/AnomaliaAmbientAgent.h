#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AnomaliaAmbientAgent.generated.h"

class USphereComponent;
class UStaticMeshComponent;

/** Provisional ambient agents: server-driven wandering, fleeing and pursuit, not final skeletal AI. */
UENUM(BlueprintType)
enum class EAnomaliaAmbientKind : uint8
{
    Deer, Boar, Wolf, Dinosaur, Civilian, Guard
};

UCLASS(Blueprintable)
class ANOMALIAPRIMEVAL_API AAnomaliaAmbientAgent : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaAmbientAgent();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|AI")
    TObjectPtr<USphereComponent> Collision;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|AI")
    TObjectPtr<UStaticMeshComponent> PrototypeVisual;

    UPROPERTY(ReplicatedUsing=OnRep_Kind, VisibleAnywhere, BlueprintReadOnly, Category="ANOMALIA|AI")
    EAnomaliaAmbientKind Kind = EAnomaliaAmbientKind::Deer;

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="ANOMALIA|AI")
    void ConfigureKind(EAnomaliaAmbientKind NewKind);

    virtual void Tick(float DeltaTime) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    virtual void BeginPlay() override;

    UFUNCTION()
    void OnRep_Kind();

private:
    void UpdatePrototypeVisual();
    float DecisionCountdown = 0.f;
    FVector TravelDirection = FVector::ForwardVector;
};
