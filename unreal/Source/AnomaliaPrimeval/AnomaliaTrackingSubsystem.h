#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "AnomaliaTrackingSubsystem.generated.h"

UENUM(BlueprintType)
enum class EAnomaliaTrackKind : uint8 { Footprint, Blood };

USTRUCT(BlueprintType)
struct FAnomaliaTrackClue
{
 GENERATED_BODY()
 UPROPERTY(BlueprintReadOnly) EAnomaliaTrackKind Kind = EAnomaliaTrackKind::Footprint;
 UPROPERTY(BlueprintReadOnly) FString ActorId;
 UPROPERTY(BlueprintReadOnly) FVector Location = FVector::ZeroVector;
 UPROPERTY(BlueprintReadOnly) FRotator Direction = FRotator::ZeroRotator;
 UPROPERTY(BlueprintReadOnly) FName Terrain = TEXT("soil");
 UPROPERTY(BlueprintReadOnly) float Severity = 1.f;
 UPROPERTY(BlueprintReadOnly) double SpawnTimeSeconds = 0.;
};

UCLASS()
class ANOMALIAPRIMEVAL_API UAnomaliaTrackingSubsystem : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable, Category="Anomalia|Tracking")
 void AddClue(EAnomaliaTrackKind Kind, const FString& ActorId, FVector Location, FRotator Direction, FName Terrain, float Severity);
 UFUNCTION(BlueprintCallable, Category="Anomalia|Tracking")
 TArray<FAnomaliaTrackClue> FindNearby(FVector Origin, float Radius, float RainIntensity, const FString& ActorFilter) const;
 virtual void Tick(float DeltaTime) override;
 virtual TStatId GetStatId() const override;
 virtual bool DoesSupportWorldType(EWorldType::Type WorldType) const override;
private:
 UPROPERTY() TArray<FAnomaliaTrackClue> Clues;
 double ClockSeconds = 0.;
 float CleanupAccumulator = 0.f;
 double Lifespan(const FAnomaliaTrackClue& Clue, float RainIntensity) const;
};