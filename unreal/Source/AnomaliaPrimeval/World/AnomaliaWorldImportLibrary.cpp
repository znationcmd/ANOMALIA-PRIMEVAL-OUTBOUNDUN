#include "AnomaliaWorldImportLibrary.h"
#include "AnomaliaArchipelagoHeight.h"
#include "AnomaliaInhabitedHeight.h"
#if WITH_EDITOR
#include "Editor.h"
#include "Landscape.h"
#include "LandscapeInfo.h"
#include "LandscapeComponent.h"
#include "LandscapeSubsystem.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInterface.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "UObject/Package.h"
#endif

double UAnomaliaWorldImportLibrary::ArchipelagoHeight(double EastMeters,double NorthMeters)
{
 if(!FMath::IsFinite(EastMeters)||!FMath::IsFinite(NorthMeters))return 0;
 return AnomaliaArchipelago::Height(EastMeters,NorthMeters);
}
static AActor* CreateLandscape(bool bInhabited)
{
#if WITH_EDITOR
 UWorld* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
 if(!World || World->GetPackage()->GetName()!=(bInhabited?TEXT("/Game/Maps/ANOMALIA_Inhabited_v1"):TEXT("/Game/Maps/ANOMALIA_Archipelago_v2")))return nullptr;
 for(TActorIterator<ALandscape> It(World);It;++It)return nullptr; // Never overlay/replace existing terrain.
 constexpr int32 Size=3025;
 TArray<uint16> Samples; Samples.SetNumUninitialized(Size*Size);
 for(int32 Y=0;Y<Size;++Y)for(int32 X=0;X<Size;++X){
  const double East=-24000.+48000.*X/(Size-1);
  const double North=24000.-48000.*Y/(Size-1);
  Samples[Y*Size+X]=AnomaliaArchipelago::Encode(bInhabited?AnomaliaInhabited::Height(East,North):AnomaliaArchipelago::Height(East,North));
 }
 ALandscape* Land=World->SpawnActor<ALandscape>();
 if(!Land)return nullptr;
 Land->SetActorLabel(bInhabited?TEXT("ANOMALIA_InhabitedArchipelago_48km"):TEXT("ANOMALIA_OriginalArchipelago_48km"));
 Land->SetActorLocation(FVector(-2400000,-2400000,0));
 Land->SetActorScale3D(FVector(4800000./(Size-1),4800000./(Size-1),800));
 TMap<FGuid,TArray<uint16>> Heights; Heights.Add(FGuid(),MoveTemp(Samples));
 TMap<FGuid,TArray<FLandscapeImportLayerInfo>> Layers; Layers.Add(FGuid(),TArray<FLandscapeImportLayerInfo>());
 Land->Import(FGuid::NewGuid(),0,0,Size-1,Size-1,2,63,Heights,nullptr,Layers,ELandscapeImportAlphamapType::Additive,TArrayView<const FLandscapeLayer>());
 Land->CreateLandscapeInfo();
 Land->PostEditChange();
 if(Land->LandscapeComponents.Num()!=576){UE_LOG(LogTemp,Error,TEXT("ANOMALIA unexpected terrain component count"));return nullptr;}
 if(ULandscapeSubsystem* Subsystem=World->GetSubsystem<ULandscapeSubsystem>())
  Subsystem->ChangeGridSize(Land->GetLandscapeInfo(),2);
 return Land;
#else
 return nullptr;
#endif
}

AActor* UAnomaliaWorldImportLibrary::CreateArchipelagoLandscape() { return CreateLandscape(false); }
AActor* UAnomaliaWorldImportLibrary::CreateInhabitedArchipelagoLandscape() { return CreateLandscape(true); }
TArray<FVector2D> UAnomaliaWorldImportLibrary::InhabitedSettlementSites()
{
 TArray<FVector2D> Result;
 for(const auto& Site:AnomaliaInhabited::Sites)Result.Add(FVector2D(Site[0],Site[1]));
 return Result;
}
double UAnomaliaWorldImportLibrary::InhabitedArchipelagoHeight(double EastMeters,double NorthMeters)
{
 if(!FMath::IsFinite(EastMeters)||!FMath::IsFinite(NorthMeters))return 0;
 return AnomaliaInhabited::Height(EastMeters,NorthMeters);
}

FString UAnomaliaWorldImportLibrary::RefreshArchipelagoRenderResources(bool bRefresh)
{
#if WITH_EDITOR
 UWorld* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
 if(!World || World->GetPackage()->GetName()!=TEXT("/Game/Maps/ANOMALIA_Archipelago_v2"))
  return TEXT("{\"state\":\"REFUSED_WRONG_WORLD\"}");
 TArray<ULandscapeComponent*> Components;
 for(TActorIterator<ALandscapeProxy> It(World);It;++It)
  for(ULandscapeComponent* Component:It->LandscapeComponents)
   if(Component)Components.Add(Component);
 // Refuse incomplete worlds before any refresh, preserving their streaming state.
 if(Components.Num()!=576)return TEXT("{\"state\":\"REFUSED_INCOMPLETE_LANDSCAPE\"}");
 // Edit-layer merging needs a real rendering device. The source map was imported
 // under NullRHI; its saved collision has relief but all visual bounds are -2048m.
 // Re-evaluate existing layers only in memory, never recreate or save the map.
 int32 MergedLandscapes=0;
 if(bRefresh)for(TActorIterator<ALandscape> It(World);It;++It){
  if(ULandscapeInfo* Info=It->GetLandscapeInfo()){
   Info->ForceLayersFullUpdate();
   It->ForceUpdateLayersContent();
   ++MergedLandscapes;
  }
 }
 TArray<TSharedPtr<FJsonValue>> Entries;
 TSet<UTexture2D*> Refreshed;
 int32 MissingHeightmaps=0;
 for(ULandscapeComponent* Component:Components){
  TSharedRef<FJsonObject> Entry=MakeShared<FJsonObject>();
  Entry->SetStringField(TEXT("component"),Component->GetPathName());
  Entry->SetBoolField(TEXT("registered"),Component->IsRegistered());
  Entry->SetBoolField(TEXT("visible"),Component->IsVisible());
  Entry->SetNumberField(TEXT("boundsCenterZCm"),Component->Bounds.Origin.Z);
  Entry->SetNumberField(TEXT("boundsMinZCm"),Component->Bounds.Origin.Z-Component->Bounds.BoxExtent.Z);
  Entry->SetNumberField(TEXT("boundsMaxZCm"),Component->Bounds.Origin.Z+Component->Bounds.BoxExtent.Z);
  Entry->SetStringField(TEXT("bounds"),Component->Bounds.Origin.ToString()+TEXT(" extent=")+Component->Bounds.BoxExtent.ToString());
  UTexture2D* Heightmap=Component->GetHeightmap(false);
  if(Heightmap){
   Entry->SetStringField(TEXT("heightmap"),Heightmap->GetPathName());
   Entry->SetNumberField(TEXT("textureWidth"),Heightmap->GetSizeX());
   Entry->SetNumberField(TEXT("textureHeight"),Heightmap->GetSizeY());
   Entry->SetNumberField(TEXT("sourceWidth"),Heightmap->Source.GetSizeX());
   Entry->SetNumberField(TEXT("sourceHeight"),Heightmap->Source.GetSizeY());
   Entry->SetBoolField(TEXT("resourceBefore"),Heightmap->GetResource()!=nullptr);
   if(!Refreshed.Contains(Heightmap)){if(bRefresh)Heightmap->UpdateResource();Refreshed.Add(Heightmap);}
  }else{++MissingHeightmaps;}
  UMaterialInterface* Material=Component->GetMaterial(0);
  Entry->SetStringField(TEXT("materialBefore"),Material?Material->GetPathName():TEXT("NONE"));
  // Rebuild transient scene/material resources after a NullRHI-created import.
  // No height data, transform, collision or package is replaced or saved here.
  if(bRefresh){
  Component->UpdateMaterialInstances();
  Component->SetVisibility(true);
  Component->SetRenderInMainPass(true);
  Component->UpdateBounds();
  Component->MarkRenderStateDirty();
  }
  Entries.Add(MakeShared<FJsonValueObject>(Entry));
 }
 TSharedRef<FJsonObject> Report=MakeShared<FJsonObject>();
 Report->SetStringField(TEXT("state"),bRefresh?TEXT("REFRESHED_IN_MEMORY_NOT_VISUALLY_VALIDATED"):TEXT("INSPECTED_WITHOUT_FORCED_REBUILD"));
 Report->SetNumberField(TEXT("componentCount"),Components.Num());
 Report->SetNumberField(TEXT("landscapesLayerMergeRequested"),MergedLandscapes);
 Report->SetNumberField(TEXT("uniqueHeightmaps"),Refreshed.Num());
 Report->SetNumberField(TEXT("missingHeightmaps"),MissingHeightmaps);
 Report->SetArrayField(TEXT("components"),Entries);
 FString Json;auto Writer=TJsonWriterFactory<>::Create(&Json);
 FJsonSerializer::Serialize(Report,Writer);return Json;
#else
 return TEXT("{\"state\":\"EDITOR_ONLY\"}");
#endif
}
