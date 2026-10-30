#include "AnomaliaZPrigimaliaChaosRoadProbe.h"
#include "AnomaliaZPrigimaliaVehicleSurvival.h"
#include "../AnomaliaZPrigimaliaInventoryComponent.h"
#include "AnomaliaZPrigimaliaChaosRoadVehicle.h"
#include "AnomaliaZPrigimaliaVehiclePanelComponent.h"
#include "Engine/StaticMesh.h"
#include "../AnomaliaZPrigimaliaGameMode.h"
#include "../AnomaliaZPrigimaliaSurvivor.h"
#include "ChaosWheeledVehicleMovementComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/FloatingPawnMovement.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "PhysicalMaterials/PhysicalMaterial.h"
#include "PhysicsEngine/BodyInstance.h"
#include "PhysicsEngine/PhysicsSettings.h"
#include "Engine/SkeletalMesh.h"
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
#include "HAL/IConsoleManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace
{
bool ReadPanelFixtureVector(const TSharedPtr<FJsonObject>& Object,const TCHAR* Key,FVector& Out)
{
    const TArray<TSharedPtr<FJsonValue>>* Values=nullptr;
    if(!Object.IsValid() || !Object->TryGetArrayField(Key,Values) || !Values || Values->Num()!=3)return false;
    Out=FVector((*Values)[0]->AsNumber(),(*Values)[1]->AsNumber(),(*Values)[2]->AsNumber());
    return !Out.ContainsNaN() && Out.GetAbsMax()<1000;
}

bool PlaceReviewSurvivor(AAnomaliaZPrigimaliaSurvivor* Survivor,const FVector& Destination)
{
    if(!Survivor || !Survivor->GetActorEnableCollision())return false;
    // Fixture relocation only, never a gameplay move. Recreate the character's
    // collision at the destination rather than moving its kinematic body across
    // the car between successive sides. The vehicle is never moved or reset.
    Survivor->SetActorEnableCollision(false);
    Survivor->GetCharacterMovement()->StopMovementImmediately();
    Survivor->SetBase(static_cast<UPrimitiveComponent*>(nullptr));
    const bool Placed=Survivor->SetActorLocationAndRotation(Destination,FRotator::ZeroRotator,
        false,nullptr,ETeleportType::TeleportPhysics);
    Survivor->SetActorEnableCollision(true);
    return Placed;
}

}

AAnomaliaZPrigimaliaChaosRoadProbe::AAnomaliaZPrigimaliaChaosRoadProbe() { PrimaryActorTick.bCanEverTick=true; }
void AAnomaliaZPrigimaliaChaosRoadProbe::ObserveExitedMovement(float DeltaSeconds,FVector InitialLocation,FVector InitialVelocity)
{
    if(!bEnabled || Phase!=14 || !Survivor.IsValid() || DeltaSeconds<=0)return;
    // Observe the actual movement update that consumes LaunchCharacter, before
    // later ground friction naturally slows the character. Do not inject motion.
    ObservedExitSpeed=FMath::Max(ObservedExitSpeed,float(InitialVelocity.Size2D()));
    ObservedExitSpeed=FMath::Max(ObservedExitSpeed,float(Survivor->GetCharacterMovement()->Velocity.Size2D()));
    ObservedExitSpeed=FMath::Max(ObservedExitSpeed,float(FVector::Dist2D(InitialLocation,Survivor->GetActorLocation())/DeltaSeconds));
}
void AAnomaliaZPrigimaliaChaosRoadProbe::BeginPlay()
{
    Super::BeginPlay();
#if !UE_BUILD_SHIPPING
    const auto* Mode=GetWorld()->GetAuthGameMode<AAnomaliaZPrigimaliaGameMode>();
    bEnabled=Mode && GetNetMode()==NM_Standalone && Mode->ServerId.StartsWith(TEXT("chaos-smoke-")) &&
        (GetWorld()->GetMapName().EndsWith(TEXT("ANOMALIA_ChaosRoadReview_v2")) ||
         GetWorld()->GetMapName().EndsWith(TEXT("ANOMALIA_SedanDriveReview_v1")) ||
         GetWorld()->GetMapName().EndsWith(TEXT("ANOMALIA_E39DriveReview_v1"))) &&
        FParse::Value(FCommandLine::Get(),TEXT("AnomaliaZPrigimaliaChaosProbe="),ReportFile) && !ReportFile.IsEmpty();
#endif
    SetActorTickEnabled(bEnabled);
    if(bEnabled)
    {
        // Observe a process-local startup override; never modify the shared
        // project/engine configuration or disable suspension forces themselves.
        if(FParse::Param(FCommandLine::Get(),TEXT("AnomaliaZPrigimaliaForceSuspensionReview")))
        {
            const auto* Setting=IConsoleManager::Get().FindConsoleVariable(TEXT("p.Vehicle.DisableConstraintSuspension"));
            if(!Setting || Setting->GetInt()!=1)
            {Finish(TEXT("Requested force-suspension comparison is not active"));return;}
        }
        DrySurface=NewObject<UPhysicalMaterial>(this);DrySurface->Friction=.9f;DrySurface->StaticFriction=.9f;DrySurface->Restitution=0;
        LowGripSurface=NewObject<UPhysicalMaterial>(this);LowGripSurface->Friction=.45f;LowGripSurface->StaticFriction=.45f;LowGripSurface->Restitution=0;
        for(TActorIterator<AStaticMeshActor> It(GetWorld());It;++It)
            if(It->Tags.Contains(FName(TEXT("ANOMALIA_ChaosRoadReview_v2"))) || It->Tags.Contains(FName(TEXT("ANOMALIA_SedanDriveReview_v1"))) ||
               It->Tags.Contains(FName(TEXT("ANOMALIA_E39DriveReview_v1"))))
            {
                if(ProvingSurface){Finish(TEXT("Review ground is not unique"));return;}
                ProvingSurface=It->GetStaticMeshComponent();ProvingSurface->SetPhysMaterialOverride(DrySurface);
            }
        if(!ProvingSurface){Finish(TEXT("Owned physics proving surface missing"));return;}
    }
    Started=PhaseStarted=GetWorld()->GetTimeSeconds();
    WallStarted=FPlatformTime::Seconds();
    bRecordFrames=FParse::Param(FCommandLine::Get(),TEXT("AnomaliaZPrigimaliaRecordDriving"));
    if(bEnabled && bRecordFrames)IFileManager::Get().MakeDirectory(*FPaths::Combine(FPaths::GetPath(ReportFile),TEXT("frames")),true);
}
void AAnomaliaZPrigimaliaChaosRoadProbe::Finish(const FString& Error)
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
    Report->SetNumberField(TEXT("exitVehicleSpeedCmPerSecond"),ExitVehicleSpeed);
    Report->SetNumberField(TEXT("observedExitCharacterSpeedCmPerSecond"),ObservedExitSpeed);
    Report->SetArrayField(TEXT("brakingMeasurements"),BrakingMeasurements);
    Report->SetBoolField(TEXT("driverDoorReviewed"),bDriverDoorReviewed);
    TArray<TSharedPtr<FJsonValue>> PanelIds;
    for(const auto& Id:ValidatedAdditionalPanelIds)PanelIds.Add(MakeShared<FJsonValueString>(Id));
    Report->SetArrayField(TEXT("validatedAdditionalPanelIds"),PanelIds);
    Report->SetNumberField(TEXT("panelMaxChassisDriftCm"),PanelMaxDriftCm);
    Report->SetNumberField(TEXT("panelMaxChassisSpeedCmPerSecond"),PanelMaxSpeedCmPerSecond);
    if(const auto* Setting=IConsoleManager::Get().FindConsoleVariable(TEXT("p.Vehicle.DisableConstraintSuspension")))
        Report->SetNumberField(TEXT("constraintSuspensionDisabled"),Setting->GetInt());
    if(Car.IsValid())
    {
        Report->SetBoolField(TEXT("reviewFixtureInitializedClosed"),IdleStarted>0);
        Report->SetBoolField(TEXT("reviewKeyboardInputIsolated"),true);
        TArray<TSharedPtr<FJsonValue>> LeafStates;
        TArray<UAnomaliaZPrigimaliaVehiclePanelComponent*> Leaves={Car->DriverDoor.Get()};
        for(const auto& Leaf:Car->AdditionalPanels)Leaves.Add(Leaf.Get());
        for(const auto* Leaf:Leaves)if(Leaf)
        {
            auto State=MakeShared<FJsonObject>();State->SetStringField(TEXT("id"),Leaf->PanelId.ToString());
            State->SetBoolField(TEXT("open"),Leaf->bOpen);State->SetBoolField(TEXT("obstructed"),Leaf->bObstructed);
            State->SetNumberField(TEXT("angleDegrees"),Leaf->AngleDegrees);
            State->SetStringField(TEXT("relativeRotation"),Leaf->GetRelativeRotation().ToString());
            LeafStates.Add(MakeShared<FJsonValueObject>(State));
        }
        Report->SetArrayField(TEXT("finalPanelStates"),LeafStates);
        auto Profile=MakeShared<FJsonObject>();
        Profile->SetNumberField(TEXT("massKg"),Car->Chassis->GetMass());
        Profile->SetNumberField(TEXT("peakTorqueNm"),Car->ChaosMovement->EngineSetup.MaxTorque);
        Profile->SetNumberField(TEXT("dragCoefficient"),Car->ChaosMovement->DragCoefficient);
        Profile->SetBoolField(TEXT("rearWheelDriveObserved"),bRearDriveObserved);
        Profile->SetNumberField(TEXT("linearDamping"),Car->Chassis->GetLinearDamping());
        Profile->SetNumberField(TEXT("angularDamping"),Car->Chassis->GetAngularDamping());
        Profile->SetStringField(TEXT("rootBindTransform"),Car->RoadMesh->GetRefSkeleton().GetRefBonePose()[0].ToString());
        TArray<TSharedPtr<FJsonValue>> SuspensionConfig;
        for(auto& Wheel:Car->ChaosMovement->Wheels)
        {
            if(!Wheel)continue;
            const auto& Config=Wheel->GetPhysicsSuspensionConfig();
            auto Row=MakeShared<FJsonObject>();
            Row->SetNumberField(TEXT("wheelSpringRateProperty"),Wheel->SpringRate);
            Row->SetNumberField(TEXT("convertedSpringRate"),Config.SpringRate);
            Row->SetNumberField(TEXT("convertedSpringPreload"),Config.SpringPreload);
            Row->SetNumberField(TEXT("dampingRatio"),Config.DampingRatio);
            Row->SetNumberField(TEXT("expectedEvenStaticLoadEngineUnits"),Car->Chassis->GetMass()*FMath::Abs(GetWorld()->GetGravityZ())/4.f);
            SuspensionConfig.Add(MakeShared<FJsonValueObject>(Row));
        }
        Profile->SetArrayField(TEXT("suspensionConfiguration"),SuspensionConfig);
        Report->SetObjectField(TEXT("vehicleProfile"),Profile);
    }
    TArray<TSharedPtr<FJsonValue>> Rows;
    for(const auto& Check:Checks) Rows.Add(MakeShared<FJsonValueString>(Check));
    Report->SetArrayField(TEXT("checks"),Rows); Report->SetArrayField(TEXT("physicsSamples"),Samples);
    Report->SetArrayField(TEXT("stationarySamples"),IdleSamples);
    Report->SetArrayField(TEXT("panelSamples"),PanelSamples);
    Report->SetBoolField(TEXT("stationaryReviewed"),bIdleReviewed);
    Report->SetBoolField(TEXT("asyncPhysics"),UPhysicsSettings::Get()->bTickPhysicsAsync);
    Report->SetNumberField(TEXT("asyncFixedTimeStepSize"),UPhysicsSettings::Get()->AsyncFixedTimeStepSize);
    FString Raw; FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Raw));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(ReportFile),true);
    FFileHelper::SaveStringToFile(Raw,*ReportFile);
    bEnabled=false; SetActorTickEnabled(false); FPlatformMisc::RequestExit(false);
}
void AAnomaliaZPrigimaliaChaosRoadProbe::Tick(float DeltaSeconds)
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
    if(Now-Started>150 || FPlatformTime::Seconds()-WallStarted>360)
    { Finish(TEXT("Actual Chaos driving timed out")); return; }
    auto* PC=GetWorld()->GetFirstPlayerController();
    if(!PC) return;
    // This actor is enabled only on the explicit isolated standalone test map.
    // Native server actions below supply the test commands. Live host keyboard
    // input must not change a leaf while its closed state is being measured.
    if(PC->GetPawn())PC->GetPawn()->DisableInput(PC);
    if(!PC->IsLookInputIgnored())PC->SetIgnoreLookInput(true);
    if(Phase==14)
    {
        if(Now-PhaseStarted<.25)return;
        if(PC->GetPawn()!=Survivor.Get() || ObservedExitSpeed<1000.f)
        { Finish(TEXT("High speed exit did not retain the original character and vehicle momentum")); return; }
        Checks.Add(TEXT("high_speed_exit_restores_original_survivor_with_vehicle_momentum"));
        Finish();return;
    }
    if(Phase==42)
    {
        auto* V=Car.Get();auto* S=Cast<AAnomaliaZPrigimaliaSurvivor>(PC->GetPawn());
        if(!V || !S){Finish(TEXT("Closed-trunk walking review lost its actors"));return;}
        const float Drift=FVector::Dist(V->GetActorLocation(),PanelReviewStart);
        if(Drift>50.f || V->Chassis->GetPhysicsLinearVelocity().Size()>100.f)
        {Finish(TEXT("Walking into the closed trunk destabilized the chassis"));return;}
        if(Now-PhaseStarted<1.5)
        {S->AddMovementInput(-PanelTraceOutward.GetSafeNormal());return;}
        const float Walked=FVector::Dist2D(S->GetActorLocation(),PanelAimInMeshCm);
        const FVector Local=V->Chassis->GetComponentTransform().InverseTransformPosition(S->GetActorLocation());
        if(Walked<25.f || Walked>180.f || Local.X>PanelApertureLocalCm.X-5.f ||
            S->GetCharacterMovement()->Velocity.Size2D()>10.f)
        {Finish(FString::Printf(TEXT("Character did not actually walk and stop at the closed trunk: moved=%.2f local=%s velocity=%s"),
            Walked,*Local.ToString(),*S->GetCharacterMovement()->Velocity.ToString()));return;}
        S->GetCharacterMovement()->StopMovementImmediately();
        Checks.Add(TEXT("survivor_walks_into_closed_trunk_without_launching_chassis"));
        bAdditionalPanelsReviewed=true;Phase=0;PhaseStarted=Now-4;
    }
    if(Phase==40 || Phase==41)
    {
        auto* V=Car.Get();auto* S=Cast<AAnomaliaZPrigimaliaSurvivor>(PC->GetPawn());auto* Panel=PanelUnderReview.Get();
        if(!V || !S || !Panel){Finish(TEXT("Additional E39 panel review lost its real actor"));return;}
        PanelMaxDriftCm=FMath::Max(PanelMaxDriftCm,float(FVector::Dist(V->GetActorLocation(),PanelReviewStart)));
        PanelMaxSpeedCmPerSecond=FMath::Max(PanelMaxSpeedCmPerSecond,float(V->Chassis->GetPhysicsLinearVelocity().Size()));
        // Retain the actual contact/force output before the stability gate,
        // including the failing frame. Never reset velocity or relax limits.
        auto PanelSample=MakeShared<FJsonObject>();
        PanelSample->SetStringField(TEXT("panel"),Panel->PanelId.ToString());
        PanelSample->SetNumberField(TEXT("phase"),Phase);
        PanelSample->SetNumberField(TEXT("seconds"),Now-PhaseStarted);
        PanelSample->SetNumberField(TEXT("frameDeltaSeconds"),DeltaSeconds);
        PanelSample->SetNumberField(TEXT("angleDegrees"),Panel->AngleDegrees);
        const FBodyInstance* RawPanelBody=Panel->GetBodyInstance(NAME_None,false);
        const FBodyInstance* EffectivePanelBody=Panel->GetBodyInstance();
        PanelSample->SetBoolField(TEXT("nativePanelBodyWelded"),RawPanelBody && RawPanelBody->WeldParent!=nullptr);
        PanelSample->SetStringField(TEXT("nativePanelBodyOwner"),RawPanelBody?GetNameSafe(RawPanelBody->OwnerComponent.Get()):TEXT("None"));
        PanelSample->SetStringField(TEXT("effectivePanelBodyOwner"),EffectivePanelBody?GetNameSafe(EffectivePanelBody->OwnerComponent.Get()):TEXT("None"));
        PanelSample->SetStringField(TEXT("location"),V->GetActorLocation().ToString());
        PanelSample->SetStringField(TEXT("velocity"),V->Chassis->GetPhysicsLinearVelocity().ToString());
        PanelSample->SetNumberField(TEXT("driftCm"),FVector::Dist(V->GetActorLocation(),PanelReviewStart));
        PanelSample->SetStringField(TEXT("survivorLocation"),S->GetActorLocation().ToString());
        PanelSample->SetStringField(TEXT("survivorVelocity"),S->GetCharacterMovement()->Velocity.ToString());
        PanelSample->SetStringField(TEXT("survivorMovementBase"),GetNameSafe(S->GetMovementBase()));
        PanelSample->SetBoolField(TEXT("characterAutoPhysicsPushEnabled"),S->GetCharacterMovement()->bEnablePhysicsInteraction);
        TArray<TSharedPtr<FJsonValue>> WheelSamples;
        for(int32 Index=0;Index<V->ChaosMovement->Wheels.Num();++Index)
        {
            const FWheelStatus& Status=V->ChaosMovement->GetWheelState(Index);
            auto WheelSample=MakeShared<FJsonObject>();
            WheelSample->SetNumberField(TEXT("wheel"),Index);
            WheelSample->SetBoolField(TEXT("contact"),Status.bInContact);
            WheelSample->SetNumberField(TEXT("springForce"),Status.SpringForce);
            WheelSample->SetNumberField(TEXT("suspensionLengthNormalized"),Status.NormalizedSuspensionLength);
            WheelSamples.Add(MakeShared<FJsonValueObject>(WheelSample));
        }
        PanelSample->SetArrayField(TEXT("wheels"),WheelSamples);
        PanelSamples.Add(MakeShared<FJsonValueObject>(PanelSample));
        if(PanelMaxDriftCm>50.f || PanelMaxSpeedCmPerSecond>100.f)
        {Finish(FString::Printf(TEXT("Panel review destabilized chassis: %s drift=%.2f cm speed=%.2f cm/s vehicle=%s survivor=%s"),
            *Panel->PanelId.ToString(),PanelMaxDriftCm,PanelMaxSpeedCmPerSecond,*V->GetActorLocation().ToString(),*S->GetActorLocation().ToString()));return;}
        if(Now-PhaseStarted<1.5)return;
        const FVector Point=V->Chassis->GetComponentTransform().TransformPosition(PanelApertureLocalCm);
        const FVector Outward=V->Chassis->GetComponentTransform().TransformVectorNoScale(PanelTraceOutward).GetSafeNormal();
        FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaZPrigimaliaAdditionalPanelReview),false);Query.AddIgnoredActor(S);FHitResult Hit;
        const bool bHit=GetWorld()->LineTraceSingleByChannel(Hit,Point+Outward*180,Point-Outward*50,ECC_Visibility,Query);
        FHitResult PawnHit;
        const bool bPawnHit=GetWorld()->SweepSingleByChannel(PawnHit,Point+Outward*180,Point-Outward*50,FQuat::Identity,
            ECC_Pawn,FCollisionShape::MakeCapsule(5.f,10.f),Query);
        const FString Id=Panel->PanelId.ToString();
        if(Phase==40)
        {
            const FQuat Expected(Panel->LocalHingeAxis.GetSafeNormal(),FMath::DegreesToRadians(Panel->OpenAngleDegrees));
            if(!Panel->bOpen || Panel->bObstructed || FMath::Abs(Panel->AngleDegrees-Panel->OpenAngleDegrees)>1.f ||
               !Panel->GetRelativeTransform().GetRotation().Equals(Expected,.01f) || !Panel->IsVisible() || (bHit && Hit.GetComponent()==Panel) || (bPawnHit && PawnHit.GetComponent()==Panel))
            {Finish(TEXT("Additional panel failed real axis/open-aperture check: ")+Id);return;}
            if(V->SurvivalSystems->bEnabled && (Id==TEXT("hood") || Id==TEXT("trunk")))
            {
                auto* Systems=V->SurvivalSystems.Get();FString ServiceError;
                if(!Systems->State.bKeyIssued && !Systems->Execute(S,EAnomaliaZPrigimaliaVehicleServiceAction::TakeInitialKey,0,0,ServiceError))
                {Finish(TEXT("Physical vehicle key claim failed: ")+ServiceError);return;}
                if(!Systems->HasPhysicalKey(S) || !Systems->CanStart(S))
                {Finish(TEXT("Matching carried key and complete parts must permit ignition"));return;}
                if(Id==TEXT("hood"))
                {
                    for(const auto Pair:{TPair<EAnomaliaZPrigimaliaVehicleServiceAction,EAnomaliaZPrigimaliaVehicleServiceAction>(EAnomaliaZPrigimaliaVehicleServiceAction::RemoveRadiator,EAnomaliaZPrigimaliaVehicleServiceAction::InstallRadiator),
                        TPair<EAnomaliaZPrigimaliaVehicleServiceAction,EAnomaliaZPrigimaliaVehicleServiceAction>(EAnomaliaZPrigimaliaVehicleServiceAction::RemoveSparkPlug,EAnomaliaZPrigimaliaVehicleServiceAction::InstallSparkPlug)})
                    {
                        if(!Systems->Execute(S,Pair.Key,0,0,ServiceError) || Systems->CanStart(S) ||
                           !Systems->Execute(S,Pair.Value,0,0,ServiceError) || !Systems->CanStart(S))
                        {Finish(TEXT("Real inventory removal/reinstallation did not gate ignition: ")+ServiceError);return;}
                    }
                    if(!S->InventoryComponent->TryAddItem(TEXT("water"),4)){Finish(TEXT("Coolant review water does not fit"));return;}
                    for(int32 Fill=0;Fill<4;++Fill)if(!Systems->Execute(S,EAnomaliaZPrigimaliaVehicleServiceAction::FillCoolant,0,0,ServiceError))
                    {Finish(TEXT("Radiator refill inventory exchange failed: ")+ServiceError);return;}
                    Checks.Add(TEXT("hood_open_inventory_radiator_and_spark_plug_removal_blocks_real_ignition"));
                }
                else
                {
                    if(!Systems->Execute(S,EAnomaliaZPrigimaliaVehicleServiceAction::RemoveBattery,0,0,ServiceError) || Systems->CanStart(S) ||
                       !Systems->Execute(S,EAnomaliaZPrigimaliaVehicleServiceAction::InstallBattery,0,0,ServiceError) || !Systems->CanStart(S))
                    {Finish(TEXT("Boot battery removal/reinstallation did not gate ignition: ")+ServiceError);return;}
                    if(!S->InventoryComponent->TryAddItem(TEXT("wood"),1)){Finish(TEXT("Cargo review item does not fit"));return;}
                    const auto* Item=S->InventoryComponent->Stacks.FindByPredicate([](const auto& Stack){return Stack.ItemId==TEXT("wood");});
                    if(!Item || !Systems->Execute(S,EAnomaliaZPrigimaliaVehicleServiceAction::Deposit,Item->StackId,Item->Count,ServiceError))
                    {Finish(TEXT("Open boot deposit failed: ")+ServiceError);return;}
                    const float CargoMass=V->CargoInventory->GetCurrentWeightKg();
                    const float ExpectedMass=V->GetUnladenMassKg()+CargoMass;
                    if(CargoMass<=0.f || !FMath::IsNearlyEqual(V->Chassis->GetMass(),ExpectedMass,.1f) ||
                       !FMath::IsNearlyEqual(V->ChaosMovement->Mass,ExpectedMass,.1f))
                    {Finish(FString::Printf(TEXT("Cargo mass mismatch: physical=%.3f chaos=%.3f dry=%.3f cargo=%.3f"),
                        V->Chassis->GetMass(),V->ChaosMovement->Mass,V->GetUnladenMassKg(),CargoMass));return;}
                    V->CargoInventory->OnInventoryUpdated.Broadcast();
                    if(!FMath::IsNearlyEqual(V->Chassis->GetMass(),ExpectedMass,.1f))
                    {Finish(TEXT("Repeated cargo notification accumulated extra chassis mass"));return;}
                    const auto* Stored=V->CargoInventory->Stacks.FindByPredicate([](const auto& Stack){return Stack.ItemId==TEXT("wood");});
                    if(!Stored || !Systems->Execute(S,EAnomaliaZPrigimaliaVehicleServiceAction::Withdraw,Stored->StackId,Stored->Count,ServiceError) || V->CargoInventory->Stacks.Num()!=0)
                    {Finish(TEXT("Open boot withdrawal failed or duplicated cargo: ")+ServiceError);return;}
                    if(!FMath::IsNearlyEqual(V->Chassis->GetMass(),V->GetUnladenMassKg(),.1f))
                    {Finish(TEXT("Empty cargo did not restore the actual chassis mass"));return;}
                    if(!S->InventoryComponent->TryRemoveItem(TEXT("wood"),1)){Finish(TEXT("Restored cargo item missing from survivor"));return;}
                    Checks.Add(TEXT("trunk_open_inventory_battery_and_journaled_cargo_exchange_verified"));
                }
            }
            Checks.Add(TEXT("panel_")+Id+TEXT("_rotates_on_authored_axis_and_clears_access"));
            FScreenshotRequest::RequestScreenshot(FPaths::Combine(FPaths::GetPath(ReportFile),TEXT("actual-panel-")+Id+TEXT("-open.png")),false,false);
            FVector Eye;FRotator View;S->GetActorEyesViewPoint(Eye,View);PC->SetControlRotation((Panel->GetComponentTransform().TransformPosition(PanelAimInMeshCm)-Eye).Rotation());
            if(!Panel->TryToggle(S))
            {
                FCollisionQueryParams AimQuery(SCENE_QUERY_STAT(AnomaliaZPrigimaliaPanelCloseDiagnostic),true);AimQuery.AddIgnoredActor(S);FHitResult AimHit;
                const FVector Aim=Panel->GetComponentTransform().TransformPosition(PanelAimInMeshCm);
                GetWorld()->LineTraceSingleByChannel(AimHit,Eye,Eye+(Aim-Eye).GetSafeNormal()*300.f,ECC_Visibility,AimQuery);
                Finish(FString::Printf(TEXT("Targeted server panel close rejected: %s eye=%s aim=%s hit=%s distance=%.2f cm"),
                    *Id,*Eye.ToString(),*Aim.ToString(),*GetNameSafe(AimHit.GetComponent()),FVector::Dist(S->GetActorLocation(),Panel->Bounds.Origin)));return;
            }
            Phase=41;PhaseStarted=Now;return;
        }
        if(Panel->bOpen || Panel->bObstructed || FMath::Abs(Panel->AngleDegrees)>1.f ||
           !Panel->GetRelativeTransform().GetRotation().Equals(FQuat::Identity,.01f) || !bHit || Hit.GetComponent()!=Panel || !bPawnHit || PawnHit.GetComponent()!=Panel)
        {Finish(TEXT("Additional panel failed closed collision restoration: ")+Id);return;}
        Checks.Add(TEXT("panel_")+Id+TEXT("_closes_and_restores_real_collision"));
        ValidatedAdditionalPanelIds.Add(Id);++AdditionalPanelIndex;
        if(AdditionalPanelIndex==5)
        {
            // Actual normal walking input, not a trace-only collision claim.
            PanelReviewStart=V->GetActorLocation();PanelAimInMeshCm=S->GetActorLocation();
            Phase=42;PhaseStarted=Now;return;
        }
        Phase=0;PhaseStarted=Now-4;
    }
    if(Phase==32 || Phase==33)
    {
        auto* V=Car.Get();
        if(!V || PC->GetPawn()!=V){Finish(TEXT("Driver door control lost its valid driver"));return;}
        if(Now-PhaseStarted<1.5)return;
        auto* Door=V->DriverDoor.Get();
        const float Expected=Phase==32?Door->OpenAngleDegrees:0.f;
        if(Door->bObstructed || FMath::Abs(Door->AngleDegrees-Expected)>1.f)
        {Finish(TEXT("Current driver could not operate the real hinged door"));return;}
        if(Phase==32)
        {
            if(!V->ExecuteRoadActionOnServer(PC,EAnomaliaZPrigimaliaRoadAction::DriverDoor))
            {Finish(TEXT("Current driver door-close command rejected"));return;}
            Phase=33;PhaseStarted=Now;return;
        }
        Checks.Add(TEXT("current_driver_opens_and_closes_real_door_from_seat"));
        Phase=10;PhaseStarted=Now;
    }
    if(Phase==30 || Phase==31)
    {
        auto* V=Car.Get();auto* S=Cast<AAnomaliaZPrigimaliaSurvivor>(PC->GetPawn());
        if(!V || !S || !V->DriverDoorMesh){Finish(TEXT("Door review lost the real survivor or imported mesh"));return;}
        if(Now-PhaseStarted<1.5)return;
        auto* Door=V->DriverDoor.Get();
        const FVector Opening=V->Chassis->GetComponentTransform().TransformPosition(DoorApertureLocalCm);
        FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaZPrigimaliaDoorApertureReview),false);Query.AddIgnoredActor(S);
        FHitResult Hit;const bool bHit=GetWorld()->LineTraceSingleByChannel(Hit,Opening-V->GetActorRightVector()*180,
            Opening+V->GetActorRightVector()*50,ECC_Visibility,Query);
        if(Phase==30)
        {
            if(!Door->bOpen || Door->bObstructed || FMath::Abs(Door->AngleDegrees-Door->OpenAngleDegrees)>1.f ||
               (bHit && Hit.GetComponent()==Door) || !Door->IsVisible())
            {Finish(TEXT("Real driver door did not rotate open and clear the original aperture"));return;}
            Checks.Add(TEXT("driver_door_rotates_at_hinge_and_collision_leaves_aperture"));
            FScreenshotRequest::RequestScreenshot(FPaths::Combine(FPaths::GetPath(ReportFile),TEXT("actual-driver-door-open.png")),false,false);
            FVector Eye;FRotator View;S->GetActorEyesViewPoint(Eye,View);PC->SetControlRotation((Door->Bounds.Origin-Eye).Rotation());
            if(!Door->TryToggle(S)){Finish(TEXT("Server targeted interaction could not close open driver door"));return;}
            Phase=31;PhaseStarted=Now;return;
        }
        if(Door->bOpen || Door->bObstructed || FMath::Abs(Door->AngleDegrees)>1.f || !bHit || Hit.GetComponent()!=Door)
        {Finish(TEXT("Closed driver door did not restore actual collision"));return;}
        Checks.Add(TEXT("driver_door_closes_and_restores_actual_collision"));
        bDriverDoorReviewed=true;Phase=0;
    }
    if(Phase==0)
    {
        if(Now-PhaseStarted<4) return;
        auto* S=Cast<AAnomaliaZPrigimaliaSurvivor>(PC->GetPawn());
        if(!S) return;
        if(!Car.IsValid())for(TActorIterator<AAnomaliaZPrigimaliaChaosRoadVehicle> It(GetWorld());It;++It)
        { if(Car.IsValid()) { Finish(TEXT("Review vehicle is not unique")); return; } Car=*It; }
        auto* V=Car.Get();
        if(!V || !V->IsChaosDriveReady()) { Finish(TEXT("Actual skeletal rig/Chaos physics is not ready")); return; }
        if(FVector::DotProduct(V->Chassis->GetUpVector(),FVector::UpVector)<.85f)
        {Finish(TEXT("Review chassis did not settle upright before driving"));return;}
        if(V->Movement->IsComponentTickEnabled()) { Finish(TEXT("Legacy floating movement is still enabled")); return; }
        if(!bIdleReviewed)
        {
            if(!UPhysicsSettings::Get()->bTickPhysicsAsync || !FMath::IsNearlyEqual(UPhysicsSettings::Get()->AsyncFixedTimeStepSize,1.f/120.f,.000001f))
            {Finish(TEXT("Fixed asynchronous physics cadence is not configured"));return;}
            if(IdleStarted==0)
            {
                // Fixture initialization, before twenty seconds of observation.
                // Every measured cycle still uses targeted server interactions.
                TArray<UAnomaliaZPrigimaliaVehiclePanelComponent*> Leaves={V->DriverDoor.Get()};
                for(const auto& Leaf:V->AdditionalPanels)Leaves.Add(Leaf.Get());
                for(auto* Leaf:Leaves)if(Leaf)
                {
                    Leaf->bOpen=false;Leaf->bLocked=false;Leaf->bObstructed=false;
                    Leaf->AngleDegrees=0.f;Leaf->SetRelativeRotation(FQuat::Identity,false,nullptr,ETeleportType::TeleportPhysics);
                }
                IdleStarted=Now;IdleStartLocation=V->GetActorLocation();
            }
            const FVector Velocity=V->Chassis->GetPhysicsLinearVelocity();
            if(Now-LastIdleSample>=.2)
            {
                auto Sample=MakeShared<FJsonObject>();Sample->SetNumberField(TEXT("seconds"),Now-IdleStarted);
                Sample->SetNumberField(TEXT("frameDeltaSeconds"),DeltaSeconds);
                Sample->SetStringField(TEXT("location"),V->GetActorLocation().ToString());
                Sample->SetStringField(TEXT("velocity"),Velocity.ToString());
                Sample->SetNumberField(TEXT("speedCmPerSecond"),Velocity.Size());
                Sample->SetNumberField(TEXT("driftCm"),FVector::Dist(V->GetActorLocation(),IdleStartLocation));
                IdleSamples.Add(MakeShared<FJsonValueObject>(Sample));LastIdleSample=Now;
            }
            if(Velocity.Size()>100.f || FVector::Dist(V->GetActorLocation(),IdleStartLocation)>50.f)
            {Finish(FString::Printf(TEXT("Unoccupied stationary chassis is unstable before opening panels: velocity=%s location=%s"),
                *Velocity.ToString(),*V->GetActorLocation().ToString()));return;}
            if(Now-IdleStarted<20)return;
            Checks.Add(TEXT("unoccupied_chassis_stable_for_20_seconds_with_fixed_async_physics"));bIdleReviewed=true;
        }
        if(V->DriverDoorMesh && !bDriverDoorReviewed)
        {
            auto* Door=V->DriverDoor.Get();
            if(Door->GetStaticMesh()!=V->DriverDoorMesh || Door->GetCollisionEnabled()!=ECollisionEnabled::QueryOnly || Door->IsSimulatingPhysics() || Door->BodyInstance.bAutoWeld ||
               Door->GetCollisionObjectType()!=ECC_GameTraceChannel1 ||
               V->ChaosMovement->WheelTraceCollisionResponses.GetResponse(ECC_GameTraceChannel1)!=ECR_Ignore ||
               !Door->GetRelativeLocation().Equals(V->DriverDoorPivotCm,.1f))
            {Finish(TEXT("Actual hinge-centred imported driver door is not installed"));return;}
            Checks.AddUnique(TEXT("separate_licensed_driver_door_mesh_installed"));
            FString ManifestText;TSharedPtr<FJsonObject> Manifest;
            const TSharedPtr<FJsonObject>* Bounds=nullptr;
            const TArray<TSharedPtr<FJsonValue>> *Minimum=nullptr,*Maximum=nullptr;
            const bool bE39Review=GetWorld()->GetMapName().EndsWith(TEXT("ANOMALIA_E39DriveReview_v1"));
            const TCHAR* ManifestRelative=bE39Review?TEXT("SourceAssets/BMWE39Review_v7/manifest.json"):TEXT("SourceAssets/NativeDemoSedan_v3/manifest.json");
            if(!FFileHelper::LoadFileToString(ManifestText,*FPaths::Combine(FPaths::ProjectDir(),ManifestRelative)) ||
               !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(ManifestText),Manifest) || !Manifest.IsValid() ||
               !Manifest->TryGetObjectField(TEXT("closedBodyBoundsCm"),Bounds) || !Bounds || !Bounds->IsValid() ||
               !(*Bounds)->TryGetArrayField(TEXT("min"),Minimum) || !(*Bounds)->TryGetArrayField(TEXT("max"),Maximum) ||
               !Minimum || !Maximum || Minimum->Num()!=3 || Maximum->Num()!=3)
            {Finish(TEXT("Original closed body bounds are unavailable for recomposition verification"));return;}
            const FVector ExpectedMin((*Minimum)[0]->AsNumber(),(*Minimum)[1]->AsNumber(),(*Minimum)[2]->AsNumber());
            const FVector ExpectedMax((*Maximum)[0]->AsNumber(),(*Maximum)[1]->AsNumber(),(*Maximum)[2]->AsNumber());
            FBox ClosedBox=V->RoadBodyMesh->GetBounds().GetBox();
            ClosedBox+=V->DriverDoorMesh->GetBounds().GetBox().ShiftBy(V->DriverDoorPivotCm);
            for(const auto& Panel:V->AdditionalPanels)if(Panel && Panel->GetStaticMesh())
                ClosedBox+=Panel->GetStaticMesh()->GetBounds().GetBox().ShiftBy(Panel->GetRelativeLocation());
            if(!ClosedBox.Min.Equals(ExpectedMin,1.f) || !ClosedBox.Max.Equals(ExpectedMax,1.f))
            {Finish(TEXT("Closed door does not recompose the original body bounds: wrong hinge side or pivot"));return;}
            Checks.AddUnique(TEXT("closed_driver_door_recomposes_original_body_bounds"));
            // Only fixture positioning: opening and closing use the same targeted
            // server interaction as the survivor's E key, never assigned angles.
            FVector StandLocalCm(240,-240,100);
            if(bE39Review)
            {
                const TArray<TSharedPtr<FJsonValue>>* Panels=nullptr;
                if(!Manifest->TryGetArrayField(TEXT("panels"),Panels) || !Panels || Panels->Num()!=6)
                {Finish(TEXT("E39 six-panel review configuration missing"));return;}
                TSharedPtr<FJsonObject> Panel;
                for(const auto& Value:*Panels)
                {
                    const auto Object=Value->AsObject();FString Id;
                    if(Object.IsValid() && Object->TryGetStringField(TEXT("id"),Id) && Id==TEXT("door_driver"))Panel=Object;
                }
                if(!ReadPanelFixtureVector(Panel,TEXT("apertureCm"),DoorApertureLocalCm) ||
                   !ReadPanelFixtureVector(Panel,TEXT("fixtureStandCm"),StandLocalCm))
                {Finish(TEXT("E39 driver leaf fixture vectors invalid"));return;}
            }
            if(PanelUnderReview.Get()!=Door)
            {
                PanelUnderReview=Door;PanelReviewStart=V->GetActorLocation();
                const FVector Stand=V->Chassis->GetComponentTransform().TransformPosition(StandLocalCm);
                if(!PlaceReviewSurvivor(S,Stand)){Finish(TEXT("Driver fixture relocation failed"));return;}
                // Phase 0 requires four seconds before re-entering this block.
                // All character collision is enabled throughout that interval.
                PhaseStarted=Now;return;
            }
            if(FVector::Dist(V->GetActorLocation(),PanelReviewStart)>50.f || V->Chassis->GetPhysicsLinearVelocity().Size()>100.f)
            {Finish(TEXT("Driver fixture relocation destabilized chassis before any opening command"));return;}
            Checks.AddUnique(TEXT("driver_fixture_settled_with_character_collision_before_opening"));
            FVector Eye;FRotator View;S->GetActorEyesViewPoint(Eye,View);PC->SetControlRotation((Door->Bounds.Origin-Eye).Rotation());
            const FVector Opening=V->Chassis->GetComponentTransform().TransformPosition(DoorApertureLocalCm);
            FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaZPrigimaliaClosedPanelReview),false);Query.AddIgnoredActor(S);FHitResult Hit;
            if(!GetWorld()->LineTraceSingleByChannel(Hit,Opening-V->GetActorRightVector()*180,
               Opening+V->GetActorRightVector()*50,ECC_Visibility,Query) || Hit.GetComponent()!=Door)
            {Finish(FString::Printf(TEXT("Closed real driver door does not block the aperture trace: open=%d angle=%.2f rotation=%s hit=%s"),
                Door->bOpen,Door->AngleDegrees,*Door->GetRelativeRotation().ToString(),*GetNameSafe(Hit.GetComponent())));return;}
            Checks.Add(TEXT("closed_driver_door_has_actual_collision"));
            Door->bLocked=true;
            if(Door->TryToggle(S) || Door->bOpen){Finish(TEXT("Locked driver door accepted opening"));return;}
            Door->bLocked=false;Checks.Add(TEXT("locked_driver_door_rejects_server_interaction"));
            if(!Door->TryToggle(S)){Finish(TEXT("Server targeted driver door opening rejected"));return;}
            Phase=30;PhaseStarted=Now;return;
        }
        if(GetWorld()->GetMapName().EndsWith(TEXT("ANOMALIA_E39DriveReview_v1")) && !bAdditionalPanelsReviewed)
        {
            FString Text;TSharedPtr<FJsonObject> Manifest;const TArray<TSharedPtr<FJsonValue>>* Configs=nullptr;
            if(!FFileHelper::LoadFileToString(Text,*FPaths::Combine(FPaths::ProjectDir(),TEXT("SourceAssets/BMWE39Review_v7/manifest.json"))) ||
               !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Manifest) || !Manifest.IsValid() ||
               !Manifest->TryGetArrayField(TEXT("panels"),Configs) || !Configs || Configs->Num()!=6)
            {Finish(TEXT("E39 complete panel review manifest missing"));return;}
            TArray<TSharedPtr<FJsonObject>> Additional;
            for(const auto& Value:*Configs)
            {
                const auto Config=Value->AsObject();FString Id;
                if(!Config.IsValid() || !Config->TryGetStringField(TEXT("id"),Id)){Finish(TEXT("Invalid E39 panel identity"));return;}
                if(Id!=TEXT("door_driver"))Additional.Add(Config);
            }
            if(Additional.Num()!=5){Finish(TEXT("Five extra E39 panel definitions required"));return;}
            if(AdditionalPanelIndex>=Additional.Num())bAdditionalPanelsReviewed=true;
            else
            {
                const auto Config=Additional[AdditionalPanelIndex];const FName Id(*Config->GetStringField(TEXT("id")));
                UAnomaliaZPrigimaliaVehiclePanelComponent* Panel=nullptr;
                for(const auto& Candidate:V->AdditionalPanels)if(Candidate && Candidate->PanelId==Id)Panel=Candidate;
                FVector StandLocal,Axis,Pivot,Aim;
                if(!Panel || !Panel->GetStaticMesh() || Panel->GetCollisionEnabled()!=ECollisionEnabled::QueryOnly || Panel->IsSimulatingPhysics() || Panel->BodyInstance.bAutoWeld ||
                   Panel->GetCollisionObjectType()!=ECC_GameTraceChannel1 ||
                   !ReadPanelFixtureVector(Config,TEXT("apertureCm"),PanelApertureLocalCm) ||
                   !ReadPanelFixtureVector(Config,TEXT("traceOutward"),PanelTraceOutward) || PanelTraceOutward.IsNearlyZero() ||
                   !ReadPanelFixtureVector(Config,TEXT("fixtureStandCm"),StandLocal) ||
                   !ReadPanelFixtureVector(Config,TEXT("fixtureAimCm"),Aim) ||
                   !ReadPanelFixtureVector(Config,TEXT("hingeAxis"),Axis) || !ReadPanelFixtureVector(Config,TEXT("pivotCm"),Pivot) ||
                   !Panel->LocalHingeAxis.Equals(Axis.GetSafeNormal(),.001f) || !Panel->GetRelativeLocation().Equals(Pivot,.1f))
                {Finish(TEXT("Authored E39 panel/axis/fixture missing: ")+Id.ToString());return;}
                PanelAimInMeshCm=Aim-Pivot;
                if(PanelUnderReview.Get()!=Panel)
                {
                    PanelUnderReview=Panel;PanelReviewStart=V->GetActorLocation();
                    const FVector Stand=V->Chassis->GetComponentTransform().TransformPosition(StandLocal);
                    if(!PlaceReviewSurvivor(S,Stand)){Finish(TEXT("Panel fixture relocation failed"));return;}
                    PhaseStarted=Now;return;
                }
                if(FVector::Dist(V->GetActorLocation(),PanelReviewStart)>50.f || V->Chassis->GetPhysicsLinearVelocity().Size()>100.f)
                {Finish(TEXT("Panel fixture relocation destabilized chassis before opening: ")+Id.ToString());return;}
                Checks.Add(TEXT("panel_")+Id.ToString()+TEXT("_fixture_settled_with_character_collision_before_opening"));
                Checks.Add(TEXT("panel_")+Id.ToString()+TEXT("_installed_with_authored_hinge_axis"));
                FVector Eye;FRotator View;S->GetActorEyesViewPoint(Eye,View);PC->SetControlRotation((Panel->GetComponentTransform().TransformPosition(PanelAimInMeshCm)-Eye).Rotation());
                const FVector Point=V->Chassis->GetComponentTransform().TransformPosition(PanelApertureLocalCm);
                const FVector Outward=V->Chassis->GetComponentTransform().TransformVectorNoScale(PanelTraceOutward).GetSafeNormal();
                FCollisionQueryParams Query(SCENE_QUERY_STAT(AnomaliaZPrigimaliaAdditionalPanelClosed),false);Query.AddIgnoredActor(S);FHitResult Hit;
                if(!GetWorld()->LineTraceSingleByChannel(Hit,Point+Outward*180,Point-Outward*50,ECC_Visibility,Query) || Hit.GetComponent()!=Panel)
                {Finish(TEXT("Closed panel does not block the authored access trace: ")+Id.ToString());return;}
                FHitResult PawnHit;
                if(!GetWorld()->SweepSingleByChannel(PawnHit,Point+Outward*180,Point-Outward*50,FQuat::Identity,
                    ECC_Pawn,FCollisionShape::MakeCapsule(5.f,10.f),Query) || PawnHit.GetComponent()!=Panel)
                {Finish(TEXT("Closed panel does not block a character collision sweep: ")+Id.ToString());return;}
                Panel->bLocked=true;
                if(Panel->TryToggle(S) || Panel->bOpen){Finish(TEXT("Locked panel accepted targeted opening"));return;}
                Panel->bLocked=false;Checks.Add(TEXT("panel_")+Id.ToString()+TEXT("_closed_collision_and_server_lock_verified"));
                if(!Panel->TryToggle(S)){Finish(TEXT("Targeted server panel opening rejected: ")+Id.ToString());return;}
                Phase=40;PhaseStarted=Now;return;
            }
        }
        if(V->SurvivalSystems->bEnabled)
        {
            auto* Systems=V->SurvivalSystems.Get();FString ServiceError;
            if(!Systems->Execute(S,EAnomaliaZPrigimaliaVehicleServiceAction::ToggleLock,0,0,ServiceError) || !Systems->State.bLocked || !V->DriverDoor->bLocked || Systems->CanStart(S) ||
               !Systems->Execute(S,EAnomaliaZPrigimaliaVehicleServiceAction::ToggleLock,0,0,ServiceError) || Systems->State.bLocked || V->DriverDoor->bLocked || !Systems->CanStart(S) ||
               Systems->Execute(S,EAnomaliaZPrigimaliaVehicleServiceAction::Deposit,1,1,ServiceError))
            {Finish(TEXT("Carried key locking or closed boot access gate failed: ")+ServiceError);return;}
            Checks.Add(TEXT("matching_physical_key_locks_actual_panels_and_closed_boot_blocks_cargo"));
        }
        // Fixture setup only. Driving below never assigns actor transforms or velocities.
        S->TeleportTo(V->GetActorLocation()+FVector(0,-350,150),FRotator::ZeroRotator,false,true);
        Survivor=S;
        OriginalFuelConsumption=V->FuelConsumptionPerSecond;
        S->OnCharacterMovementUpdated.AddDynamic(this,&AAnomaliaZPrigimaliaChaosRoadProbe::ObserveExitedMovement);
        if(!V->EnterVehicle(PC,S) || PC->GetPawn()!=V) { Finish(TEXT("Existing crew possession failed")); return; }
        if(V->bEngineRunning) { Finish(TEXT("Parked review engine started without driver ignition")); return; }
        AddTickPrerequisiteActor(PC);
        V->AddTickPrerequisiteActor(this);
        V->CameraBoom->SetRelativeLocation(FVector(0,0,120));
        PC->SetControlRotation(FRotator(-12,0,0));
        Checks.Add(TEXT("real_skeletal_rig_and_four_Chaos_wheels_no_floating_movement"));
        Checks.Add(TEXT("existing_character_and_inventory_preserved_on_entry"));
        StartLocation=V->GetActorLocation(); Phase=10; PhaseStarted=Now;
        if(!V->ExecuteRoadActionOnServer(PC,EAnomaliaZPrigimaliaRoadAction::Headlights) || !V->bHeadlightsOn || V->Headlights.Num()!=2 ||
           !V->Headlights[0]->IsVisible() || V->Headlights[0]->Intensity<=0.f)
        { Finish(TEXT("Real headlight components did not activate")); return; }
        Checks.Add(TEXT("driver_activates_real_headlight_components"));
        V->ExecuteRoadActionOnServer(PC,EAnomaliaZPrigimaliaRoadAction::HazardLights);
        if(!V->ExecuteRoadActionOnServer(PC,EAnomaliaZPrigimaliaRoadAction::GearUp) ||
           !V->ExecuteRoadActionOnServer(PC,EAnomaliaZPrigimaliaRoadAction::GearUp) ||
           !V->ExecuteRoadActionOnServer(PC,EAnomaliaZPrigimaliaRoadAction::GearDown) || !V->bManualGears || V->ChaosMovement->GetUseAutoGears())
        { Finish(TEXT("Manual gear selection failed")); return; }
        if(V->DriverDoorMesh)
        {
            if(!V->ExecuteRoadActionOnServer(PC,EAnomaliaZPrigimaliaRoadAction::DriverDoor))
            {Finish(TEXT("Current driver door-open command rejected"));return;}
            Phase=32;PhaseStarted=Now;return;
        }
    }
    auto* V=Car.Get();
    if(!V || PC->GetPawn()!=V) { Finish(TEXT("Vehicle possession was lost")); return; }
    if(!V->AreWheelVisualsUpright()) { Finish(TEXT("Visible tire axle is not aligned with the vehicle lateral plane")); return; }
    auto* Physics=V->ChaosMovement.Get();
    if(V->IndicatorLights.Num()==4 && V->IndicatorMode==3)
    {
        bSignalSeenOn|=V->IndicatorLights[0]->IsVisible();bSignalSeenOff|=!V->IndicatorLights[0]->IsVisible();
    }
    const float Speed=Physics->GetForwardSpeed();
    const FVector Velocity=V->Chassis->GetPhysicsLinearVelocity();
    const FVector Acceleration=bHasPreviousVelocity && DeltaSeconds>0?(Velocity-PreviousVelocity)/DeltaSeconds:FVector::ZeroVector;
    PreviousVelocity=Velocity;bHasPreviousVelocity=true;
    if(Phase==1 && Physics->Wheels.Num()==4)
    {
        const float FrontTorque=FMath::Abs(Physics->GetWheelState(0).DriveTorque)+FMath::Abs(Physics->GetWheelState(1).DriveTorque);
        const float RearTorque=FMath::Abs(Physics->GetWheelState(2).DriveTorque)+FMath::Abs(Physics->GetWheelState(3).DriveTorque);
        if(FrontTorque>1.f){Finish(TEXT("Propulsion profile unexpectedly drives front wheels"));return;}
        bRearDriveObserved|=RearTorque>1.f;
    }
    int32 Contacts=0; float Rotation=0;
    for(const auto& Wheel:Physics->Wheels) if(Wheel) { if(!Wheel->IsInAir()) ++Contacts; Rotation+=FMath::Abs(Wheel->GetWheelAngularVelocity()); }
    if(Now-LastSample>.2)
    {
        auto Sample=MakeShared<FJsonObject>(); Sample->SetNumberField(TEXT("seconds"),Now-Started);
        Sample->SetNumberField(TEXT("frameDeltaSeconds"),DeltaSeconds);
        Sample->SetNumberField(TEXT("wallElapsedSeconds"),FPlatformTime::Seconds()-WallStarted);
        Sample->SetNumberField(TEXT("phase"),Phase); Sample->SetNumberField(TEXT("speedCmPerSecond"),Speed);
        Sample->SetNumberField(TEXT("gear"),Physics->GetCurrentGear()); Sample->SetNumberField(TEXT("wheelContacts"),Contacts);
        Sample->SetBoolField(TEXT("automaticTransmissionActive"),Physics->GetUseAutoGears());
        Sample->SetNumberField(TEXT("engineRpm"),Physics->GetEngineRotationSpeed());
        Sample->SetNumberField(TEXT("dragMagnitudeEngineUnits"),Physics->DebugDragMagnitude);
        Sample->SetNumberField(TEXT("summedWheelAngularSpeed"),Rotation);
        Sample->SetNumberField(TEXT("yaw"),V->GetActorRotation().Yaw);
        Sample->SetNumberField(TEXT("distanceCm"),FVector::Dist2D(StartLocation,V->GetActorLocation()));
        Sample->SetNumberField(TEXT("fuelPercent"),V->FuelPercent);
        Sample->SetNumberField(TEXT("appliedThrottle"),Physics->GetThrottleInput());
        Sample->SetBoolField(TEXT("engineRunning"),V->bEngineRunning);
        Sample->SetBoolField(TEXT("manualGears"),V->bManualGears);
        Sample->SetBoolField(TEXT("handbrakeInput"),Physics->GetHandbrakeInput());
        Sample->SetBoolField(TEXT("headlightsOn"),V->bHeadlightsOn);
        Sample->SetNumberField(TEXT("chassisZ"),V->GetActorLocation().Z);
        Sample->SetNumberField(TEXT("pitch"),V->GetActorRotation().Pitch);
        Sample->SetNumberField(TEXT("roll"),V->GetActorRotation().Roll);
        Sample->SetNumberField(TEXT("physicalMassKg"),V->Chassis->GetMass());
        if(auto* Body=V->Chassis->GetBodyInstance())
        {
            const FBox Bounds=Body->GetBodyBounds();
            Sample->SetNumberField(TEXT("physicsBodyBottomZ"),Bounds.Min.Z);
            Sample->SetNumberField(TEXT("physicsBodyTopZ"),Bounds.Max.Z);
            Sample->SetNumberField(TEXT("physicsCenterOfMassZ"),Body->GetCOMPosition().Z);
        }
        Sample->SetNumberField(TEXT("longitudinalAccelerationG"),FVector::DotProduct(Acceleration,V->GetActorForwardVector())/980.665);
        Sample->SetNumberField(TEXT("lateralAccelerationG"),FVector::DotProduct(Acceleration,V->GetActorRightVector())/980.665);
        Sample->SetBoolField(TEXT("visibleTireAxlesUpright"),V->AreWheelVisualsUpright());
        TArray<TSharedPtr<FJsonValue>> WheelGeometry;
        for(int32 WheelIndex=0;WheelIndex<V->WheelBones.Num();++WheelIndex)
        {
            const FName Bone=V->WheelBones[WheelIndex];
            const FVector Hub=V->Chassis->GetSocketLocation(Bone);
            FHitResult Floor;FCollisionQueryParams Query;Query.AddIgnoredActor(V);Query.AddIgnoredActor(Survivor.Get());
            const bool bHit=GetWorld()->LineTraceSingleByChannel(Floor,Hub+FVector(0,0,100),Hub-FVector(0,0,600),ECC_Visibility,Query);
            auto Row=MakeShared<FJsonObject>();Row->SetStringField(TEXT("bone"),Bone.ToString());
            Row->SetNumberField(TEXT("hubZ"),Hub.Z);Row->SetBoolField(TEXT("floorHit"),bHit);
            Row->SetNumberField(TEXT("floorZ"),Floor.Location.Z);Row->SetStringField(TEXT("floorActor"),GetNameSafe(Floor.GetActor()));
            const FWheelStatus& Status=Physics->GetWheelState(WheelIndex);
            Row->SetBoolField(TEXT("chaosContact"),Status.bInContact);
            Row->SetBoolField(TEXT("chaosStateValid"),Status.bIsValid);
            Row->SetNumberField(TEXT("springForce"),Status.SpringForce);
            Row->SetNumberField(TEXT("suspensionLengthNormalized"),Status.NormalizedSuspensionLength);
            Row->SetNumberField(TEXT("brakeTorque"),Status.BrakeTorque);
            Row->SetNumberField(TEXT("driveTorque"),Status.DriveTorque);
            Row->SetBoolField(TEXT("absActivated"),Status.bABSActivated);
            Row->SetNumberField(TEXT("surfaceFriction"),Status.PhysMaterial.IsValid()?Status.PhysMaterial->Friction:-1.f);
            Row->SetNumberField(TEXT("slipAngle"),Status.SlipAngle);
            Row->SetBoolField(TEXT("slipping"),Status.bIsSlipping);
            Row->SetBoolField(TEXT("skidding"),Status.bIsSkidding);
            if(Physics->Wheels.IsValidIndex(WheelIndex) && Physics->Wheels[WheelIndex])
            {
                const auto* Wheel=Physics->Wheels[WheelIndex].Get();
                Row->SetNumberField(TEXT("wheelLoadRatio"),Wheel->WheelLoadRatio);
                Row->SetNumberField(TEXT("debugTireLoadEngineUnits"),Wheel->DebugTireLoad);
                Row->SetNumberField(TEXT("debugLongForceEngineUnits"),Wheel->DebugLongForce);
                Row->SetNumberField(TEXT("debugLatForceEngineUnits"),Wheel->DebugLatForce);
                Row->SetNumberField(TEXT("steerAngleDegrees"),Wheel->GetSteerAngle());
                Row->SetBoolField(TEXT("tractionControlEnabled"),Wheel->bTractionControlEnabled);
            }
            WheelGeometry.Add(MakeShared<FJsonValueObject>(Row));
        }
        Sample->SetArrayField(TEXT("wheelGeometry"),WheelGeometry);
        Samples.Add(MakeShared<FJsonValueObject>(Sample)); LastSample=Now;
    }
    const double Elapsed=Now-PhaseStarted;
    float Throttle=0,Steering=0,Brake=0;
    if(Phase==10)
    {
        Throttle=1.f;
        if(Physics->GetThrottleInput()>.01f || FMath::Abs(Speed)>100.f || V->FuelPercent<100.f)
        { Finish(TEXT("Switched-off engine propels the vehicle or consumes fuel")); return; }
        if(Elapsed>2)
        {
            float SupportForce=0.f;
            for(int32 WheelIndex=0;WheelIndex<Physics->Wheels.Num();++WheelIndex)
            {
                const auto& Wheel=Physics->GetWheelState(WheelIndex);
                if(!Wheel.bInContact || Wheel.NormalizedSuspensionLength<.05f || Wheel.NormalizedSuspensionLength>.95f ||
                   !FMath::IsFinite(Wheel.SpringForce) || Wheel.SpringForce<=0.f)
                {Finish(TEXT("Parked suspension is not supporting four loaded wheels within travel"));return;}
                SupportForce+=Wheel.SpringForce;
            }
            const float Weight=V->Chassis->GetMass()*FMath::Abs(GetWorld()->GetGravityZ());
            if(Physics->Wheels.Num()!=4 || FMath::Abs(SupportForce-Weight)>Weight*.15f)
            {Finish(TEXT("Settled spring forces do not balance actual chassis weight"));return;}
            Checks.Add(TEXT("settled_spring_forces_balance_actual_chassis_weight"));
            Checks.Add(TEXT("engine_off_blocks_full_accelerator_without_fuel_consumption"));
            if(!V->SetEngineRunningOnServer(PC,true)) { Finish(TEXT("Driver ignition failed")); return; }
            Checks.Add(TEXT("current_driver_can_start_engine_on_server")); Phase=1; PhaseStarted=Now;
        }
    }
    else if(Phase==1)
    {
        Throttle=.8f;
        if(Elapsed>6)
        {
            if(Speed<500.f || FVector::Dist2D(StartLocation,V->GetActorLocation())<500.f || Contacts<3 || Rotation<1.f)
            { Finish(TEXT("Physical acceleration/wheel contact/rotation failed")); return; }
            Checks.Add(TEXT("physical_acceleration_translation_and_rotating_contact_wheels"));
            if(!V->bManualGears || Physics->GetCurrentGear()!=1 || !V->ExecuteRoadActionOnServer(PC,EAnomaliaZPrigimaliaRoadAction::GearUp))
            { Finish(TEXT("Actual manual first gear driving or upshift failed")); return; }
            Checks.Add(TEXT("manual_first_gear_drives_physical_vehicle"));
            if(!bRearDriveObserved){Finish(TEXT("Rear axle engine torque was not observed"));return;}
            Checks.Add(TEXT("rear_wheel_drive_observed_in_actual_wheel_torques"));
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
            if(Physics->GetCurrentGear()!=2 || !bSignalSeenOn || !bSignalSeenOff)
            { Finish(TEXT("Actual second gear or blinking signal components not observed")); return; }
            Checks.Add(TEXT("manual_upshift_changes_actual_Chaos_gear"));
            Checks.Add(TEXT("hazard_light_components_flash_on_and_off"));
            BrakeStartSpeed=FMath::Abs(Speed); Phase=3; PhaseStarted=Now;
        }
    }
    else if(Phase==3 || Phase==5 || Phase==9)
    {
        Brake=Phase==5?0.f:1.f;
        if(Elapsed>2 && FMath::Abs(Speed)<50.f && V->Chassis->GetPhysicsLinearVelocity().Size()<100.f)
        {
            if(Phase==3)
            {
                if(BrakeStartSpeed<200.f || FMath::Abs(Speed)>BrakeStartSpeed*.25f)
                { Finish(TEXT("Service brake did not reduce physical speed")); return; }
                Checks.Add(TEXT("service_brake_stops_the_physical_chassis")); Phase=4; PhaseStarted=Now;
                V->ExecuteRoadActionOnServer(PC,EAnomaliaZPrigimaliaRoadAction::ToggleGearMode);
            }
            else if(Phase==5)
            {
                if(!Physics->GetHandbrakeInput()) { Finish(TEXT("Rear handbrake input was not applied")); return; }
                Checks.Add(TEXT("rear_wheel_handbrake_stops_physical_vehicle"));
                V->ExecuteRoadActionOnServer(PC,EAnomaliaZPrigimaliaRoadAction::HandbrakeOff);
                // Isolated fixture tuning only: exhaust real server fuel while
                // holding the physical brake, then challenge the empty engine.
                if(!V->ConfigureRuntimeTuning(.15f,1.f,1.f))
                { Finish(TEXT("Isolated fuel depletion setup was refused")); return; }
                Phase=6; PhaseStarted=Now;
            }
            else
            {
                if(!V->ExitDriverOnServer(PC) || PC->GetPawn()!=Survivor.Get())
                { Finish(TEXT("Safe crew exit did not restore original survivor")); return; }
                Checks.Add(TEXT("safe_exit_restores_same_survivor"));
                if(!V->EnterVehicle(PC,Survivor.Get()) || !V->SetEngineRunningOnServer(PC,true))
                { Finish(TEXT("Re-entry for high-speed exit validation failed")); return; }
                if(!V->ConfigureRuntimeTuning(V->FuelPercent,OriginalFuelConsumption,V->SpeedMultiplier))
                { Finish(TEXT("Cannot restore isolated fuel consumption after depletion test"));return; }
                Phase=20;PhaseStarted=Now;
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
            V->ExecuteRoadActionOnServer(PC,EAnomaliaZPrigimaliaRoadAction::HandbrakeOn);
        }
    }
    else if(Phase==6)
    {
        Throttle=.8f; Brake=1.f;
        if(Elapsed>2)
        {
            if(V->HasFuel() || V->FuelPercent!=0.f || Physics->GetThrottleInput()>.01f || V->bEngineRunning ||
                V->SetEngineRunningOnServer(PC,true))
            { Finish(TEXT("Real fuel depletion did not cut Chaos throttle")); return; }
            Checks.Add(TEXT("server_fuel_consumption_reaches_zero_and_cuts_Chaos_throttle"));
            EmptyTankLocation=V->GetActorLocation(); Phase=7; PhaseStarted=Now;
        }
    }
    else if(Phase==7)
    {
        Throttle=1.f;
        if(Physics->GetThrottleInput()>.01f || FMath::Abs(Speed)>100.f ||
            FVector::Dist2D(EmptyTankLocation,V->GetActorLocation())>100.f)
        { Finish(TEXT("Empty tank still propels the physical vehicle")); return; }
        if(Elapsed>3)
        {
            Checks.Add(TEXT("empty_tank_cannot_accelerate_under_full_driver_input"));
            if(V->RefuelOnServer(-1.f) || V->RefuelOnServer(0.f) || V->FuelPercent!=0.f)
            { Finish(TEXT("Invalid refuel amount changed the empty tank")); return; }
            if(!V->RefuelOnServer(25.f) || !FMath::IsNearlyEqual(V->FuelPercent,25.f))
            { Finish(TEXT("Authoritative refuel did not restore the requested fuel")); return; }
            Checks.Add(TEXT("server_refuel_rejects_invalid_amounts_and_restores_fuel"));
            Phase=11; PhaseStarted=Now;
        }
    }
    else if(Phase==11)
    {
        Throttle=1.f;
        if(V->bEngineRunning || Physics->GetThrottleInput()>.01f || FMath::Abs(Speed)>100.f || V->FuelPercent!=25.f)
        { Finish(TEXT("Refueling restarted the stalled engine without ignition")); return; }
        if(Elapsed>2)
        {
            Checks.Add(TEXT("refuel_requires_explicit_driver_restart_after_stall"));
            if(!V->SetEngineRunningOnServer(PC,true)) { Finish(TEXT("Driver restart after refuel failed")); return; }
            Phase=8; PhaseStarted=Now;
        }
    }
    else if(Phase==8)
    {
        Throttle=.8f;
        if(Elapsed>4)
        {
            if(Speed<500.f || Contacts<3 || Rotation<1.f || V->FuelPercent>=25.f || !V->HasFuel())
            { Finish(TEXT("Refuel did not restore actual wheel-driven acceleration and fuel consumption")); return; }
            Checks.Add(TEXT("refuel_restores_physical_acceleration_and_fuel_consumption"));
            if(!V->SetEngineRunningOnServer(PC,false) || V->bEngineRunning)
            { Finish(TEXT("Driver could not switch off the engine")); return; }
            Checks.Add(TEXT("current_driver_can_switch_engine_off"));
            Phase=9; PhaseStarted=Now;
        }
    }
    else if(Phase==20 || Phase==22 || Phase==24)
    {
        Throttle=1.f;
        const float Target=Phase==20?50.f/0.036f:80.f/0.036f;
        if(Speed>=Target && Contacts>=3)
        {
            MeasuredBrakeInitialSpeed=Speed;BrakePathCm=0;BrakeMeasuredStarted=Now;
            AccelerationDuration=Elapsed;
            PreviousMeasuredBrakeLocation=V->GetActorLocation();++Phase;PhaseStarted=Now;
            Throttle=0;Brake=1.f;
        }
        else if(Elapsed>20){Finish(TEXT("Simulation profile failed to reach measured braking speed"));return;}
    }
    else if(Phase==21 || Phase==23 || Phase==25)
    {
        Brake=1.f;
        BrakePathCm+=FVector::Dist2D(PreviousMeasuredBrakeLocation,V->GetActorLocation());
        PreviousMeasuredBrakeLocation=V->GetActorLocation();
        if(FMath::Abs(Speed)<30.f && Velocity.Size()<50.f)
        {
            const double MeanG=FMath::Square(double(MeasuredBrakeInitialSpeed))/(2*FMath::Max(1.,BrakePathCm)*980.665);
            auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("initialKmh"),MeasuredBrakeInitialSpeed*.036);
            Row->SetNumberField(TEXT("distanceMetres"),BrakePathCm/100);
            Row->SetNumberField(TEXT("seconds"),Now-BrakeMeasuredStarted);Row->SetNumberField(TEXT("meanDecelerationG"),MeanG);
            Row->SetNumberField(TEXT("accelerationSecondsToTarget"),AccelerationDuration);
            Row->SetNumberField(TEXT("surfaceFriction"),Phase==25?.45:.9);
            BrakingMeasurements.Add(MakeShared<FJsonValueObject>(Row));
            const double MinimumMeanG=Phase==25?.25:.5;
            if(MeanG<MinimumMeanG || MeanG>1.2 || Contacts<3)
            {Finish(TEXT("Measured road braking is outside the declared sedan envelope"));return;}
            if(Phase==21){Checks.Add(TEXT("measured_dry_braking_from_50_kmh"));Phase=22;}
            else if(Phase==23)
            {
                if(BrakePathCm<BrakingMeasurements[0]->AsObject()->GetNumberField(TEXT("distanceMetres"))*100*1.5)
                {Finish(TEXT("Higher speed did not increase physical stopping distance"));return;}
                Dry80DistanceCm=BrakePathCm;Checks.Add(TEXT("measured_dry_braking_from_80_kmh"));
                ProvingSurface->SetPhysMaterialOverride(LowGripSurface);Phase=24;
            }
            else
            {
                if(BrakePathCm<Dry80DistanceCm*1.3)
                {Finish(TEXT("Lower surface friction did not increase actual stopping distance"));return;}
                Checks.Add(TEXT("lower_grip_increases_actual_80_kmh_stopping_distance"));
                ProvingSurface->SetPhysMaterialOverride(DrySurface);Phase=12;
            }
            PhaseStarted=Now;
        }
        else if(Elapsed>12){Finish(TEXT("Measured braking did not physically stop the sedan"));return;}
    }
    else if(Phase==12)
    {
        Throttle=1.f;
        if(Elapsed>8 && Speed>=2200.f)
        {
            ExitVehicleSpeed=Speed;
            if(Speed<2200.f || Contacts<3 || !V->ExitDriverOnServer(PC) || PC->GetPawn()!=Survivor.Get())
            { Finish(TEXT("Exit at actual high speed failed")); return; }
            Phase=14;PhaseStarted=Now;return; // Allow the character to consume its pending launch.
        }
        else if(Elapsed>20){Finish(TEXT("Simulation profile did not reach high-speed exit test speed"));return;}
    }
    if(!V->SetDriverControlsOnServer(PC,Throttle,Steering,Brake)) Finish(TEXT("Authoritative control input rejected"));
}
