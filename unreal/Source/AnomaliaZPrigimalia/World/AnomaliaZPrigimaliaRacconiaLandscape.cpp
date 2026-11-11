#include "AnomaliaZPrigimaliaRacconiaLandscape.h"
#if WITH_EDITOR
#include "Editor.h"
#include "Landscape.h"
#include "LandscapeInfo.h"
#include "LandscapeSubsystem.h"
#include "LandscapeComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#endif

AActor* UAnomaliaZPrigimaliaRacconiaLandscape::CreateRacconiaVerifiedLandscape()
{
#if WITH_EDITOR
    constexpr int32 Side = 1009;
    constexpr int32 Components = 64;
    constexpr double SideCm = 1600000.0;
    constexpr double HalfCm = 800000.0;
    constexpr double ZScaleCm = 2500.0;

    const FString Project = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir());
    FString Normalized = Project;
    FPaths::NormalizeDirectoryName(Normalized);
    if (!Normalized.Equals(TEXT("C:/ANOMALIAZ_SKARVIK_STAGE_41188816555/unreal"), ESearchCase::IgnoreCase))
    {
        UE_LOG(LogTemp,Error,TEXT("RACCONIA refuses non-isolated native project"));
        return nullptr;
    }
    FString Marker;
    if (!FFileHelper::LoadFileToString(Marker,*FPaths::Combine(Project,TEXT(".skarvik-ci-stage-marker"))))
    {
        return nullptr;
    }
    Marker.TrimStartAndEndInline();
    if (!Marker.Equals(TEXT("41188816555")))return nullptr;

    UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
    const FString Expected = TEXT("/Game/Maps/PRIGIMALIA_RACCONIA_VARKOVIA_16KM_v1");
    if (!World || World->GetPackage()->GetName()!=Expected)return nullptr;
    for (TActorIterator<ALandscapeProxy> It(World);It;++It)return nullptr;

    const FString Source=FPaths::Combine(Project,
        TEXT("SourceAssets/Racconia16km_20261111/RACCONIA_UE5_READY_1009_north_up.r16"));
    TArray<uint8> Bytes;
    if (!FFileHelper::LoadFileToArray(Bytes,*Source) || Bytes.Num()!=Side*Side*2)
    {
        UE_LOG(LogTemp,Error,TEXT("RACCONIA original corrected RAW16 missing or invalid: %s"),*Source);
        return nullptr;
    }

    TArray<uint16> Elevation;
    Elevation.SetNumUninitialized(Side*Side);
    for (int32 i=0;i<Side*Side;++i)
    {
        Elevation[i]=uint16(Bytes[i*2]) | (uint16(Bytes[i*2+1])<<8);
    }
    // First source raster row is geographic NORTH. In ANOMALIA the world Y
    // axis points SOUTH: native Y=-800000 maps geographic north +8km.
    ALandscape* Terrain=World->SpawnActor<ALandscape>();
    if (!Terrain)return nullptr;
    Terrain->SetActorLabel(TEXT("RACCONIA_VARKOVIA_16KM_ORIGINAL_TERRAIN_29_SITES"));
    Terrain->SetActorLocation(FVector(-HalfCm,-HalfCm,0.0));
    Terrain->SetActorScale3D(FVector(SideCm/double(Side-1),
        SideCm/double(Side-1),ZScaleCm));
    TMap<FGuid,TArray<uint16>> Raster;
    Raster.Add(FGuid(),MoveTemp(Elevation));
    TMap<FGuid,TArray<FLandscapeImportLayerInfo>> Layers;
    Layers.Add(FGuid(),TArray<FLandscapeImportLayerInfo>());
    Terrain->Import(FGuid::NewGuid(),0,0,Side-1,Side-1,2,63,Raster,nullptr,Layers,
        ELandscapeImportAlphamapType::Additive,TArrayView<const FLandscapeLayer>());
    Terrain->CreateLandscapeInfo();
    Terrain->PostEditChange();
    if (Terrain->LandscapeComponents.Num()!=Components)
    {
        UE_LOG(LogTemp,Error,TEXT("RACCONIA refuses invalid terrain component count: %d"),
            Terrain->LandscapeComponents.Num());
        Terrain->Destroy();
        return nullptr;
    }
    if (ULandscapeSubsystem* Subsystem=World->GetSubsystem<ULandscapeSubsystem>())
    {
        Subsystem->ChangeGridSize(Terrain->GetLandscapeInfo(),2);
    }
    return Terrain;
#else
    return nullptr;
#endif
}
