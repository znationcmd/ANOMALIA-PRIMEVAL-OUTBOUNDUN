#include "AnomaliaChaosRoadProbe.h"
#include "AnomaliaChaosRoadVehicle.h"
#include "../AnomaliaGameMode.h"
#include "../AnomaliaSurvivor.h"
#include "ChaosWheeledVehicleMovementComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/FloatingPawnMovement.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "Engine/World.h"
#include "CollisionQueryParams.h"
#include "EngineUtils.h"
#include "UnrealClient.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

AAnomaliaChaosRoadProbe::AAnomaliaChaosRoadProbe() { PrimaryActorTick.bCanEverTick=true; }
void AAnomaliaChaosRoadProbe::BeginPlay()
{
    Super::BeginPlay();
#if !UE_BUILD_SHIPPING
    const auto* Mode=GetWorld()->GetAuthGameMode<AAnomaliaGameMode>();
    bEnabled=Mode && GetNetMode()==NM_Standalone && Mode->ServerId.StartsWith(TEXT("chaos-smoke-")) &&
        GetWorld()->GetMapName().EndsWith(TEXT("ANOMALIA_ChaosRoadReview_v2")) &&
        FParse::Value(FCommandLine::Get(),TEXT("AnomaliaChaosProbe="),ReportFile) && !ReportFile.IsEmpty();
#endif
    SetActorTickEnabled(bEnabled);
    Started=PhaseStarted=GetWorld()->GetTimeSeconds();
    WallStarted=FPlatformTime::Seconds();
    bRecordFrames=FParse::Param(FCommandLine::Get(),TEXT("AnomaliaRecordDriving"));
    if(bEnabled && bRecordFrames)IFileManager::Get().MakeDirectory(*FPaths::Combine(FPaths::GetPath(ReportFile),TEXT("frames")),true);
}
void AAnomaliaChaosRoadProbe::Finish(const FString& Error)
{
    if(!bFinishing)
    {
        bFinishing=true;PendingError=Error;FinishAt=FPlatformTime::Seconds()+2;
        FScreenshotRequest::RequestScreenshot(FPaths::Combine(FPaths::GetPath(ReportFile),TEXT("actual-final-viewport.png")),false,false);
        return;
    }
    if(FPlatformTime::Seconds()<FinishAt)return;
    auto Report=MakeShared<FJsonObject>();
    Report->SetStringField(TEXT("state"),Error.IsEmpty()?TEXT("CHAOS_ROAD_PHYSICS_DRIVE_PASSED"):TEXT("FAILED"));
    Report->SetStringField(TEXT("error"),Error);
    Report->SetStringField(TEXT("map"),GetWorld()->GetMapName());
    Report->SetStringField(TEXT("buildCommit"),TEXT(ANOMALIA_BUILD_COMMIT));
    Report->SetNumberField(TEXT("recordedViewportFrames"),FrameCount);
    Report->SetNumberField(TEXT("captureFramesPerSecond"),5);
    Report->SetStringField(TEXT("physicsPhaseClock"),TEXT("world_simulation_seconds"));
    Report->SetNumberField(TEXT("wallElapsedSeconds"),FPlatformTime::Seconds()-WallStarted);
    Report->SetBoolField(TEXT("packagedGameTested"),false);
    Report->SetBoolField(TEXT("multiplayerTested"),false);
    Report->SetBoolField(TEXT("entryAnimationTested"),false);
    Report->SetNumberField(TEXT("phase"),Phase);
    TArray<TSharedPtr<FJsonValue>> Rows;
    for(const auto& Check:Checks) Rows.Add(MakeShared<FJsonValueString>(Check));
    Report->SetArrayField(TEXT("checks"),Rows); Report->SetArrayField(TEXT("physicsSamples"),Samples);
    FString Raw; FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Raw));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(ReportFile),true);
    FFileHelper::SaveStringToFile(Raw,*ReportFile);
    bEnabled=false; SetActorTickEnabled(false); FPlatformMisc::RequestExit(false);
}
void AAnomaliaChaosRoadProbe::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if(!bEnabled) return;
    const double Now=GetWorld()->GetTimeSeconds();
    if(bFinishing){Finish(PendingError);return;}
    // Capture only the actual Unreal viewport, after physical acceleration passed.
    // Never capture the user's desktop, and never synthesize a demonstration.
    if(bRecordFrames && Phase>=2 && Now-LastFrame>=.2)
    {
        FScreenshotRequest::RequestScreenshot(FPaths::Combine(FPaths::GetPath(ReportFile),TEXT("frames"),FString::Printf(TEXT("frame-%05d.png"),FrameCount++)),false,false);
        LastFrame=Now;
    }
    if(Now-Started>75 || FPlatformTime::Seconds()-WallStarted>240)
    { Finish(TEXT("Actual Chaos driving timed out")); return; }
    auto* PC=GetWorld()->GetFirstPlayerController();
    if(!PC) return;
    if(Phase==0)
    {
        if(Now-PhaseStarted<4) return;
        auto* S=Cast<AAnomaliaSurvivor>(PC->GetPawn());
        if(!S) return;
        for(TActorIterator<AAnomaliaChaosRoadVehicle> It(GetWorld());It;++It)
        { if(Car.IsValid()) { Finish(TEXT("Review vehicle is not unique")); return; } Car=*It; }
        auto* V=Car.Get();
        if(!V || !V->IsChaosDriveReady()) { Finish(TEXT("Actual skeletal rig/Chaos physics is not ready")); return; }
        if(V->Movement->IsComponentTickEnabled()) { Finish(TEXT("Legacy floating movement is still enabled")); return; }
        // Fixture setup only. Driving below never assigns actor transforms or velocities.
        S->TeleportTo(V->GetActorLocation()+FVector(0,-350,150),FRotator::ZeroRotator,false,true);
        Survivor=S;
        if(!V->EnterVehicle(PC,S) || PC->GetPawn()!=V) { Finish(TEXT("Existing crew possession failed")); return; }
        AddTickPrerequisiteActor(PC);
        V->AddTickPrerequisiteActor(this);
        V->CameraBoom->SetRelativeLocation(FVector(0,0,120));
        PC->SetControlRotation(FRotator(-12,0,0));
        Checks.Add(TEXT("real_skeletal_rig_and_four_Chaos_wheels_no_floating_movement"));
        Checks.Add(TEXT("existing_character_and_inventory_preserved_on_entry"));
        StartLocation=V->GetActorLocation(); Phase=1; PhaseStarted=Now;
    }
    auto* V=Car.Get();
    if(!V || PC->GetPawn()!=V) { Finish(TEXT("Vehicle possession was lost")); return; }
    auto* Physics=V->ChaosMovement.Get();
    const float Speed=Physics->GetForwardSpeed();
    int32 Contacts=0; float Rotation=0;
    for(const auto& Wheel:Physics->Wheels) if(Wheel) { if(!Wheel->IsInAir()) ++Contacts; Rotation+=FMath::Abs(Wheel->GetWheelAngularVelocity()); }
    if(Now-LastSample>.2)
    {
        auto Sample=MakeShared<FJsonObject>(); Sample->SetNumberField(TEXT("seconds"),Now-Started);
        Sample->SetNumberField(TEXT("frameDeltaSeconds"),DeltaSeconds);
        Sample->SetNumberField(TEXT("wallElapsedSeconds"),FPlatformTime::Seconds()-WallStarted);
        Sample->SetNumberField(TEXT("phase"),Phase); Sample->SetNumberField(TEXT("speedCmPerSecond"),Speed);
        Sample->SetNumberField(TEXT("gear"),Physics->GetCurrentGear()); Sample->SetNumberField(TEXT("wheelContacts"),Contacts);
        Sample->SetNumberField(TEXT("summedWheelAngularSpeed"),Rotation);
        Sample->SetNumberField(TEXT("yaw"),V->GetActorRotation().Yaw);
        Sample->SetNumberField(TEXT("distanceCm"),FVector::Dist2D(StartLocation,V->GetActorLocation()));
        Sample->SetNumberField(TEXT("fuelPercent"),V->FuelPercent);
        Sample->SetNumberField(TEXT("chassisZ"),V->GetActorLocation().Z);
        Sample->SetNumberField(TEXT("pitch"),V->GetActorRotation().Pitch);
        Sample->SetNumberField(TEXT("roll"),V->GetActorRotation().Roll);
        Sample->SetNumberField(TEXT("physicalMassKg"),V->Chassis->GetMass());
        TArray<TSharedPtr<FJsonValue>> WheelGeometry;
        for(const FName Bone:V->WheelBones)
        {
            const FVector Hub=V->Chassis->GetSocketLocation(Bone);
            FHitResult Floor;FCollisionQueryParams Query;Query.AddIgnoredActor(V);Query.AddIgnoredActor(Survivor.Get());
            const bool bHit=GetWorld()->LineTraceSingleByChannel(Floor,Hub+FVector(0,0,100),Hub-FVector(0,0,600),ECC_Visibility,Query);
            auto Row=MakeShared<FJsonObject>();Row->SetStringField(TEXT("bone"),Bone.ToString());
            Row->SetNumberField(TEXT("hubZ"),Hub.Z);Row->SetBoolField(TEXT("floorHit"),bHit);
            Row->SetNumberField(TEXT("floorZ"),Floor.Location.Z);Row->SetStringField(TEXT("floorActor"),GetNameSafe(Floor.GetActor()));
            WheelGeometry.Add(MakeShared<FJsonValueObject>(Row));
        }
        Sample->SetArrayField(TEXT("wheelGeometry"),WheelGeometry);
        Samples.Add(MakeShared<FJsonValueObject>(Sample)); LastSample=Now;
    }
    const double Elapsed=Now-PhaseStarted;
    float Throttle=0,Steering=0,Brake=0;
    if(Phase==1)
    {
        Throttle=.8f;
        if(Elapsed>6)
        {
            if(Speed<500.f || FVector::Dist2D(StartLocation,V->GetActorLocation())<500.f || Contacts<3 || Rotation<1.f)
            { Finish(TEXT("Physical acceleration/wheel contact/rotation failed")); return; }
            Checks.Add(TEXT("physical_acceleration_translation_and_rotating_contact_wheels"));
            FScreenshotRequest::RequestScreenshot(FPaths::Combine(FPaths::GetPath(ReportFile),TEXT("chaos-actual-driving.png")),false,false);
            StraightSpeed=Speed; TurnYaw=V->GetActorRotation().Yaw; Phase=2; PhaseStarted=Now;
        }
    }
    else if(Phase==2)
    {
        Throttle=.4f; Steering=.5f;
        if(Elapsed>2.5)
        {
            if(FMath::Abs(FMath::FindDeltaAngleDegrees(TurnYaw,V->GetActorRotation().Yaw))<5.f)
            { Finish(TEXT("Physical steering did not change trajectory")); return; }
            Checks.Add(TEXT("physical_steering_changes_vehicle_heading"));
            BrakeStartSpeed=FMath::Abs(Speed); Phase=3; PhaseStarted=Now;
        }
    }
    else if(Phase==3 || Phase==5)
    {
        Brake=1.f;
        if(Elapsed>2 && FMath::Abs(Speed)<50.f && V->Chassis->GetPhysicsLinearVelocity().Size()<100.f)
        {
            if(Phase==3)
            {
                if(BrakeStartSpeed<200.f || FMath::Abs(Speed)>BrakeStartSpeed*.25f)
                { Finish(TEXT("Service brake did not reduce physical speed")); return; }
                Checks.Add(TEXT("service_brake_stops_the_physical_chassis")); Phase=4; PhaseStarted=Now;
            }
            else
            {
                if(!V->ExitDriverOnServer(PC) || PC->GetPawn()!=Survivor.Get())
                { Finish(TEXT("Safe crew exit did not restore original survivor")); return; }
                Checks.Add(TEXT("safe_exit_restores_same_survivor")); Finish(); return;
            }
        }
        else if(Elapsed>8) { Finish(TEXT("Physical braking exceeded stopping deadline")); return; }
    }
    else if(Phase==4)
    {
        Throttle=-.6f;
        if(Elapsed>4)
        {
            if(Physics->GetCurrentGear()!=-1 || Speed> -150.f)
            { Finish(TEXT("Physical reverse gear failed")); return; }
            Checks.Add(TEXT("reverse_gear_drives_chassis_backwards")); Phase=5; PhaseStarted=Now;
        }
    }
    if(!V->SetDriverControlsOnServer(PC,Throttle,Steering,Brake)) Finish(TEXT("Authoritative control input rejected"));
}
