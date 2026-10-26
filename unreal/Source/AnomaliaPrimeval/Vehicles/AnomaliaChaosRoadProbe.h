#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Dom/JsonValue.h"
#include "AnomaliaChaosRoadProbe.generated.h"
class AAnomaliaChaosRoadVehicle;
class AAnomaliaSurvivor;
class UPhysicalMaterial;
class UStaticMeshComponent;
class UAnomaliaVehiclePanelComponent;

/** Runs only with an explicit command line, isolated server ID and dedicated review map. */
UCLASS()
class ANOMALIAPRIMEVAL_API AAnomaliaChaosRoadProbe : public AActor
{
    GENERATED_BODY()
public:
    AAnomaliaChaosRoadProbe();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
private:
    bool bEnabled=false, bFinishing=false, bRecordFrames=false;
    bool bSignalSeenOn=false, bSignalSeenOff=false;
    bool bRearDriveObserved=false;
    bool bDriverDoorReviewed=false;
    bool bAdditionalPanelsReviewed=false;
    int32 AdditionalPanelIndex=0;
    TArray<FString> ValidatedAdditionalPanelIds;
    TWeakObjectPtr<UAnomaliaVehiclePanelComponent> PanelUnderReview;
    bool bIdleReviewed=false;
    double IdleStarted=0,LastIdleSample=0;
    FVector IdleStartLocation=FVector::ZeroVector;
    TArray<TSharedPtr<FJsonValue>> IdleSamples;
    FVector PanelReviewStart=FVector::ZeroVector;
    float PanelMaxDriftCm=0,PanelMaxSpeedCmPerSecond=0;
    FVector PanelAimInMeshCm=FVector::ZeroVector;
    FVector PanelApertureLocalCm=FVector::ZeroVector;
    FVector PanelTraceOutward=FVector::UpVector;
    FVector DoorApertureLocalCm=FVector(50,-90,110);
    float OriginalFuelConsumption=.045f;
    double BrakeMeasuredStarted=0, BrakePathCm=0;
    double AccelerationDuration=0;
    float MeasuredBrakeInitialSpeed=0, Dry80DistanceCm=0;
    FVector PreviousMeasuredBrakeLocation=FVector::ZeroVector;
    FVector PreviousVelocity=FVector::ZeroVector;
    bool bHasPreviousVelocity=false;
    UPROPERTY(Transient) TObjectPtr<UPhysicalMaterial> DrySurface;
    UPROPERTY(Transient) TObjectPtr<UPhysicalMaterial> LowGripSurface;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> ProvingSurface;
    TArray<TSharedPtr<FJsonValue>> BrakingMeasurements;
    double FinishAt=0, LastFrame=0;
    int32 FrameCount=0;
    FString PendingError;
    int32 Phase=0;
    double Started=0, PhaseStarted=0, LastSample=0, WallStarted=0;
    float StraightSpeed=0, TurnYaw=0, BrakeStartSpeed=0;
    float ExitVehicleSpeed=0, ObservedExitSpeed=0;
    UFUNCTION() void ObserveExitedMovement(float DeltaSeconds,FVector InitialLocation,FVector InitialVelocity);
    FVector StartLocation=FVector::ZeroVector;
    FVector EmptyTankLocation=FVector::ZeroVector;
    FString ReportFile;
    TWeakObjectPtr<AAnomaliaChaosRoadVehicle> Car;
    TWeakObjectPtr<AAnomaliaSurvivor> Survivor;
    TArray<TSharedPtr<FJsonValue>> Samples;
    TArray<FString> Checks;
    void Finish(const FString& Error=FString());
};
