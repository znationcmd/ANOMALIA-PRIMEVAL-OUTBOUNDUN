#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AnomaliaDogCompanion.generated.h"

class AAnomaliaSurvivor;
class UAnimSequence;
UENUM(BlueprintType)
enum class EAnomaliaDogCommand : uint8 { Follow, Stay, Sit, LieDown, Attack };

/** Native non-lethal companion. Only supplied locomotion clips are presented as available. */
UCLASS(Blueprintable)
class ANOMALIAPRIMEVAL_API AAnomaliaDogCompanion : public ACharacter
{
    GENERATED_BODY()
public:
    AAnomaliaDogCompanion();
    virtual void Tick(float DeltaSeconds) override;
    virtual void BeginPlay() override;
    virtual void FellOutOfWorld(const UDamageType& DamageType) override;
    virtual float TakeDamage(float Damage,const FDamageEvent& Event,AController* EventInstigator,AActor* Causer) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    /** Opt-in for isolated test scenes only; normal ownership is explicitly assigned by the server. */
    UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="ANOMALIA|Dog") bool bAutoAssignNearestSurvivor=false;
    UPROPERTY(Replicated,BlueprintReadOnly,Category="ANOMALIA|Dog") TObjectPtr<AAnomaliaSurvivor> SurvivorOwner;
    UPROPERTY(Replicated,BlueprintReadOnly,Category="ANOMALIA|Dog") EAnomaliaDogCommand Command=EAnomaliaDogCommand::Stay;
    UPROPERTY(Replicated,BlueprintReadOnly,Category="ANOMALIA|Dog") float Health=100.f;
    UPROPERTY(Replicated,BlueprintReadOnly,Category="ANOMALIA|Dog") bool bInjured=false;
    UPROPERTY(BlueprintReadOnly,Category="ANOMALIA|Dog") FString Status;
    UPROPERTY(BlueprintReadOnly,Category="ANOMALIA|Dog") FName Breed=TEXT("german_shepherd");
    UFUNCTION(BlueprintCallable,BlueprintAuthorityOnly,Category="ANOMALIA|Dog") bool AssignSurvivor(AAnomaliaSurvivor* Survivor);
    UFUNCTION(BlueprintCallable,Category="ANOMALIA|Dog") bool RequestCommand(EAnomaliaDogCommand NewCommand);
    UFUNCTION(BlueprintPure,Category="ANOMALIA|Dog") bool IsCommandAvailable(EAnomaliaDogCommand Value) const;
    /** Trusted gameplay treatment hook. There is no client RPC granting health. */
    UFUNCTION(BlueprintCallable,BlueprintAuthorityOnly,Category="ANOMALIA|Dog") bool TreatInjury(float Amount);
private:
    UFUNCTION(Server,Reliable) void ServerRequestCommand(EAnomaliaDogCommand NewCommand);
    bool IssueCommand(EAnomaliaDogCommand NewCommand);
    bool LoadBreed();
    void RefreshAnimation();
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> Idle;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> Walk;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> Run;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> CurrentAnimation;
    TArray<FVector> OwnerTrail;
    FVector LastOwnerSample=FVector::ZeroVector;
    bool bHasOwnerSample=false;
    double NextCommandTime=0;
    FVector LastSafeLocation=FVector::ZeroVector;
    bool bHasSafeLocation=false;
};
