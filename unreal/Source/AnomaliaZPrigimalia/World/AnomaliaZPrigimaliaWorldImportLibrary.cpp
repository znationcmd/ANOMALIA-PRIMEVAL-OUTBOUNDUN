#include "AnomaliaZPrigimaliaWorldImportLibrary.h"
#include "AnomaliaZPrigimaliaArchipelagoHeight.h"
#include "AnomaliaZPrigimaliaInhabitedHeight.h"
#include "AnomaliaZPrigimaliaExtraWorldHeights.h"
#if WITH_EDITOR
#include "Editor.h"
#include "Landscape.h"
#include "LandscapeInfo.h"
#include "LandscapeComponent.h"
#include "LandscapeSubsystem.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInterface.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "UObject/Package.h"
#include "WorldPartition/WorldPartitionBlueprintLibrary.h"
#include "UObject/StructOnScope.h"
#include "UObject/UnrealType.h"
#include "UObject/MetaData.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/StaticMesh.h"
#include "Components/StaticMeshComponent.h"
#endif

#if WITH_EDITOR
namespace
{
 // These Blueprint functions belong to a MinimalAPI engine class and are not
 // exported by installed UE builds. Invoke the reflected functions with native
 // owned parameter storage rather than retaining their structs in Python.
 bool CopyPartitionDescriptors(TArray<FActorDesc>& Output)
 {
  UClass* Library=UWorldPartitionBlueprintLibrary::StaticClass();
  UFunction* Function=Library->FindFunctionByName(TEXT("GetActorDescs"));
  if(!Function)return false;
  FArrayProperty* Array=FindFProperty<FArrayProperty>(Function,TEXT("OutActorDescs"));
  FBoolProperty* Returned=FindFProperty<FBoolProperty>(Function,TEXT("ReturnValue"));
  if(!Array || !Returned || Array->Inner->GetCPPType()!=TEXT("FActorDesc"))return false;
  FStructOnScope Parameters(Function);
  Library->GetDefaultObject()->ProcessEvent(Function,Parameters.GetStructMemory());
  if(!Returned->GetPropertyValue_InContainer(Parameters.GetStructMemory()))return false;
  Output=*Array->ContainerPtrToValuePtr<TArray<FActorDesc>>(Parameters.GetStructMemory());
  return true;
 }
 bool StreamPartitionActors(const TArray<FGuid>& Guids,bool bLoaded)
 {
  UClass* Library=UWorldPartitionBlueprintLibrary::StaticClass();
  UFunction* Function=Library->FindFunctionByName(bLoaded ? TEXT("LoadActors") : TEXT("UnloadActors"));
  if(!Function)return false;
  FArrayProperty* Array=FindFProperty<FArrayProperty>(Function,bLoaded ? TEXT("InActorsToLoad") : TEXT("InActorsToUnload"));
  if(!Array || Array->Inner->GetCPPType()!=TEXT("FGuid"))return false;
  FStructOnScope Parameters(Function);
  *Array->ContainerPtrToValuePtr<TArray<FGuid>>(Parameters.GetStructMemory())=Guids;
  Library->GetDefaultObject()->ProcessEvent(Function,Parameters.GetStructMemory());
  return true;
 }
 bool IsOwnedPartitionWorld()
 {
  const UWorld* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
  if(!World)return false;
  const FString Name=World->GetPackage()->GetName();
  return Name==TEXT("/Game/Maps/ANOMALIA_Archipelago_v2") ||
   Name==TEXT("/Game/Maps/ANOMALIA_Inhabited_v2") ||
   Name==TEXT("/Game/Maps/PRIGIMALIA_KARSKOV") ||
   Name==TEXT("/Game/Maps/PRIGIMALIA_VORGRAD") ||
   Name==TEXT("/Game/Maps/PRIGIMALIA_NEMORIS") ||
   Name==TEXT("/Game/Maps/PRIGIMALIA_DRAKHEIM") ||
   Name==TEXT("/Game/Maps/PRIGIMALIA_SOLYNACALYRA") ||
   Name==TEXT("/Game/Maps/PRIGIMALIA_NEXAVARKHOS") ||
   Name==TEXT("/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA");
 }
 bool IsOwnedDescriptor(const FActorDesc& Desc)
 {
  const FString NativeClass=Desc.NativeClass ? Desc.NativeClass->GetPathName() : FString();
  return Desc.Label.ToString().StartsWith(TEXT("ANOMALIA_")) ||
   Desc.Label.ToString().StartsWith(TEXT("PRIGIMALIA_")) ||
   NativeClass==TEXT("/Script/Landscape.Landscape") || NativeClass==TEXT("/Script/Landscape.LandscapeStreamingProxy");
 }
}
#endif

FString UAnomaliaZPrigimaliaWorldImportLibrary::GetArchipelagoActorDescriptors()
{
#if WITH_EDITOR
 if(!IsOwnedPartitionWorld())return TEXT("{\"state\":\"REFUSED_WRONG_WORLD\"}");
 TArray<FActorDesc> Descriptors;
 if(!CopyPartitionDescriptors(Descriptors))return TEXT("{\"state\":\"DESCRIPTORS_UNAVAILABLE\"}");
 TArray<TSharedPtr<FJsonValue>> Entries;
 for(const FActorDesc& Desc:Descriptors){
  TSharedRef<FJsonObject> Entry=MakeShared<FJsonObject>();
  Entry->SetStringField(TEXT("label"),Desc.Label.ToString());
  Entry->SetStringField(TEXT("guid"),Desc.Guid.ToString(EGuidFormats::DigitsWithHyphens));
  Entry->SetStringField(TEXT("nativeClass"),Desc.NativeClass ? Desc.NativeClass->GetPathName() : FString());
  Entry->SetBoolField(TEXT("owned"),IsOwnedDescriptor(Desc));
  // Plain saved bounds support placement clearance without loading borrowed
  // descriptor structs or every actor in the 48 km world into Python.
  Entry->SetBoolField(TEXT("boundsValid"),Desc.Bounds.IsValid!=0);
  if(Desc.Bounds.IsValid){
   TArray<TSharedPtr<FJsonValue>> Min,Max;
   for(int32 Axis=0;Axis<3;++Axis){Min.Add(MakeShared<FJsonValueNumber>(Desc.Bounds.Min[Axis]));Max.Add(MakeShared<FJsonValueNumber>(Desc.Bounds.Max[Axis]));}
   Entry->SetArrayField(TEXT("boundsMinCm"),Min);Entry->SetArrayField(TEXT("boundsMaxCm"),Max);
  }
  Entries.Add(MakeShared<FJsonValueObject>(Entry));
 }
 TSharedRef<FJsonObject> Result=MakeShared<FJsonObject>();
 Result->SetStringField(TEXT("state"),TEXT("COPIED_DESCRIPTOR_VALUES"));
 Result->SetArrayField(TEXT("actors"),Entries);
 FString Output;
 const TSharedRef<TJsonWriter<>> Writer=TJsonWriterFactory<>::Create(&Output);
 FJsonSerializer::Serialize(Result,Writer);
 return Output;
#else
 return TEXT("{\"state\":\"EDITOR_ONLY\"}");
#endif
}

bool UAnomaliaZPrigimaliaWorldImportLibrary::SetArchipelagoActorsLoaded(const TArray<FString>& ActorGuids,bool bLoaded)
{
#if WITH_EDITOR
 if(!IsOwnedPartitionWorld() || ActorGuids.Num()>65536)return false;
 TArray<FActorDesc> Descriptors;
 if(!CopyPartitionDescriptors(Descriptors))return false;
 TSet<FGuid> Allowed;
 for(const FActorDesc& Desc:Descriptors)if(IsOwnedDescriptor(Desc))Allowed.Add(Desc.Guid);
 TArray<FGuid> Requested;
 TSet<FGuid> Seen;
 for(const FString& Text:ActorGuids){
  FGuid Guid;
  if(!FGuid::ParseExact(Text,EGuidFormats::DigitsWithHyphens,Guid) || !Allowed.Contains(Guid) || Seen.Contains(Guid))return false;
  Requested.Add(Guid);Seen.Add(Guid);
 }
 // Complete preflight above: never partially change streaming for a bad batch.
 if(!Requested.IsEmpty()){
  return StreamPartitionActors(Requested,bLoaded);
 }
 return true;
#else
 return false;
#endif
}

FString UAnomaliaZPrigimaliaWorldImportLibrary::AuditInhabitedResidential(const TArray<FString>& MeshPaths,const TArray<FString>& HouseLabels)
{
#if WITH_EDITOR
 UWorld* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
 if(!World || World->GetPackage()->GetName()!=TEXT("/Game/Maps/ANOMALIA_Inhabited_v2"))
  return TEXT("{\"state\":\"REFUSED_WRONG_WORLD\"}");
 if(MeshPaths.Num()!=3)return TEXT("{\"state\":\"REFUSED_MESH_COUNT\"}");
 TSharedRef<FJsonObject> Report=MakeShared<FJsonObject>();
 Report->SetStringField(TEXT("state"),TEXT("FAILED"));
 auto VectorValues=[](const FVector& V){
  TArray<TSharedPtr<FJsonValue>> Values;
  Values.Add(MakeShared<FJsonValueNumber>(V.X));Values.Add(MakeShared<FJsonValueNumber>(V.Y));Values.Add(MakeShared<FJsonValueNumber>(V.Z));
  return Values;
 };
 auto Finish=[&Report](){FString Json;auto Writer=TJsonWriterFactory<>::Create(&Json);FJsonSerializer::Serialize(Report,Writer);return Json;};
 TArray<TSharedPtr<FJsonValue>> Meshes;
 TSet<FString> UniqueMeshes;
 // Validate all paths before loading any assets. No arbitrary external content.
 for(const FString& Path:MeshPaths){
  if(!Path.StartsWith(TEXT("/Game/")) || UniqueMeshes.Contains(Path))return Finish();
  UniqueMeshes.Add(Path);
 }
 for(const FString& Path:MeshPaths){
  UStaticMesh* Mesh=LoadObject<UStaticMesh>(nullptr,*Path);
  if(!Mesh)return Finish();
  TSharedRef<FJsonObject> Row=MakeShared<FJsonObject>();
  Row->SetStringField(TEXT("path"),Mesh->GetPathName());
  Row->SetStringField(TEXT("sourceSha"),Mesh->GetOutermost()->GetMetaData().GetValue(Mesh,TEXT("AnomaliaZPrigimaliaWorldFeatureSha256")));
  Row->SetStringField(TEXT("originalSha"),Mesh->GetOutermost()->GetMetaData().GetValue(Mesh,TEXT("AnomaliaZPrigimaliaRealismSha256")));
  const FBoxSphereBounds Bounds=Mesh->GetBounds();
  Row->SetArrayField(TEXT("origin"),VectorValues(Bounds.Origin));Row->SetArrayField(TEXT("extent"),VectorValues(Bounds.BoxExtent));
  bool bMaterialsReady=!Mesh->GetStaticMaterials().IsEmpty();
  for(const FStaticMaterial& Slot:Mesh->GetStaticMaterials())if(!Slot.MaterialInterface)bMaterialsReady=false;
  Row->SetBoolField(TEXT("materialsReady"),bMaterialsReady);
  Meshes.Add(MakeShared<FJsonValueObject>(Row));
 }
 Report->SetArrayField(TEXT("meshes"),Meshes);
 TArray<FActorDesc> Descriptors;
 if(!CopyPartitionDescriptors(Descriptors))return Finish();
 TSet<FString> Expected;
 if(HouseLabels.Num()!=4760)return Finish();
 for(const FString& Label:HouseLabels){
  if(!Label.StartsWith(TEXT("ANOMALIA_Inhabited1_")) || Expected.Contains(Label))return Finish();
  Expected.Add(Label);
 }
 TArray<FActorDesc> Houses;TSet<FString> Labels;
 for(const FActorDesc& Desc:Descriptors)if(Expected.Contains(Desc.Label.ToString())){
  if(Labels.Contains(Desc.Label.ToString()))return Finish();
  Labels.Add(Desc.Label.ToString());Houses.Add(Desc);
 }
 // The Python verifier checks exact plan identities. Do not stream a partial population.
 if(Houses.Num()!=4760)return Finish();
 TSet<FGuid> InitiallyLoaded;
 for(TActorIterator<AActor> It(World);It;++It)InitiallyLoaded.Add(It->GetActorGuid());
 TArray<TSharedPtr<FJsonValue>> Actors;
 for(int32 Start=0;Start<Houses.Num();Start+=64){
  TArray<FGuid> Load,Unload;TSet<FGuid> Requested;
  for(int32 I=Start;I<FMath::Min(Start+64,Houses.Num());++I){
   const FGuid Guid=Houses[I].Guid;Load.Add(Guid);Requested.Add(Guid);
   if(!InitiallyLoaded.Contains(Guid))Unload.Add(Guid);
  }
  if(!StreamPartitionActors(Load,true)){StreamPartitionActors(Unload,false);return Finish();}
  int32 Found=0;
  // Only owned, short-lived native actor pointers exist inside this loop.
  for(TActorIterator<AActor> It(World);It;++It)if(Requested.Contains(It->GetActorGuid())){
   ++Found;AActor* Actor=*It;TSharedRef<FJsonObject> Row=MakeShared<FJsonObject>();
   Row->SetStringField(TEXT("label"),Actor->GetActorLabel());
   Row->SetArrayField(TEXT("location"),VectorValues(Actor->GetActorLocation()));
   Row->SetArrayField(TEXT("scale"),VectorValues(Actor->GetActorScale3D()));
   Row->SetNumberField(TEXT("yaw"),Actor->GetActorRotation().Yaw);
   TArray<TSharedPtr<FJsonValue>> Tags;
   for(const FName Tag:Actor->Tags)Tags.Add(MakeShared<FJsonValueString>(Tag.ToString()));
   Row->SetArrayField(TEXT("tags"),Tags);
   const AStaticMeshActor* House=Cast<AStaticMeshActor>(Actor);
   const UStaticMeshComponent* Component=House ? House->GetStaticMeshComponent() : nullptr;
   Row->SetStringField(TEXT("mesh"),Component && Component->GetStaticMesh() ? Component->GetStaticMesh()->GetPathName() : FString());
   bool bOverrides=false;
   if(Component)for(const auto& Material:Component->OverrideMaterials)if(Material)bOverrides=true;
   Row->SetBoolField(TEXT("materialOverrides"),bOverrides);
   Actors.Add(MakeShared<FJsonValueObject>(Row));
  }
  // Restore this batch even on a missing actor; no actor is saved or deleted.
  const bool bRestored=StreamPartitionActors(Unload,false);
  if(!bRestored || Found!=Load.Num())return Finish();
 }
 Report->SetArrayField(TEXT("actors"),Actors);
 Report->SetNumberField(TEXT("houseCount"),Actors.Num());
 Report->SetBoolField(TEXT("packagesSaved"),false);
 Report->SetBoolField(TEXT("terrainModified"),false);
 Report->SetStringField(TEXT("state"),TEXT("NATIVE_RESIDENTIAL_VALUES_COPIED"));
 return Finish();
#else
 return TEXT("{\"state\":\"EDITOR_ONLY\"}");
#endif
}

double UAnomaliaZPrigimaliaWorldImportLibrary::ArchipelagoHeight(double EastMeters,double NorthMeters)
{
 if(!FMath::IsFinite(EastMeters)||!FMath::IsFinite(NorthMeters))return 0;
 return AnomaliaZPrigimaliaArchipelago::Height(EastMeters,NorthMeters);
}
static AActor* CreateLandscape(bool bInhabited)
{
#if WITH_EDITOR
 UWorld* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
 if(!World)return nullptr;
 const FString Map=World->GetPackage()->GetName();
 if(bInhabited ? (Map!=TEXT("/Game/Maps/ANOMALIA_Inhabited_v1")&&Map!=TEXT("/Game/Maps/ANOMALIA_Inhabited_v2")) : Map!=TEXT("/Game/Maps/ANOMALIA_Archipelago_v2"))return nullptr;
 for(TActorIterator<ALandscape> It(World);It;++It)return nullptr; // Never overlay/replace existing terrain.
 constexpr int32 Size=3025;
 TArray<uint16> Samples; Samples.SetNumUninitialized(Size*Size);
 for(int32 Y=0;Y<Size;++Y)for(int32 X=0;X<Size;++X){
  const double East=-24000.+48000.*X/(Size-1);
  const double North=24000.-48000.*Y/(Size-1);
  Samples[Y*Size+X]=AnomaliaZPrigimaliaArchipelago::Encode(bInhabited?AnomaliaZPrigimaliaInhabited::Height(East,North):AnomaliaZPrigimaliaArchipelago::Height(East,North));
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


AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateDrazoviaTopoCandidateLandscape()
{
#if WITH_EDITOR
 UWorld* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
 constexpr int32 Size=3025;
 if(!World || World->GetPackage()->GetName()!=TEXT("/Game/Maps/ANOMALIA_DrazoviaTopo_Candidate"))
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA: wrong editor world; original v2 is protected"));
  return nullptr;
 }
 for(TActorIterator<ALandscapeProxy> It(World);It;++It)
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA: landscape already present; refusing to overlay"));
  return nullptr;
 }
 const FString Source=FPaths::Combine(FPaths::ProjectDir(),TEXT("TerrainSource"),TEXT("DRAZOVIA"),TEXT("DRAZOVIA.r16"));
 TArray<uint8> SourceBytes;
 constexpr int64 ExpectedBytes=int64(Size)*int64(Size)*2;
 if(!FFileHelper::LoadFileToArray(SourceBytes,*Source) || SourceBytes.Num()!=ExpectedBytes)
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA: missing/invalid image-derived raw heightmap: %s"),*Source);
  return nullptr;
 }
 TArray<uint16> HeightsU16;
 HeightsU16.SetNumUninitialized(Size*Size);
 // Windows x64 little-endian: matches the exported R16 stream.
 FMemory::Memcpy(HeightsU16.GetData(),SourceBytes.GetData(),SourceBytes.Num());
 ALandscape* Land=World->SpawnActor<ALandscape>();
 if(!Land)return nullptr;
 Land->SetActorLabel(TEXT("DRAZOVIA_TopographicCandidate_48km"));
 Land->SetActorLocation(FVector(-2400000.,-2400000.,0.));
 Land->SetActorScale3D(FVector(4800000./(Size-1),4800000./(Size-1),800.));
 TMap<FGuid,TArray<uint16>> Heights;
 Heights.Add(FGuid(),MoveTemp(HeightsU16));
 TMap<FGuid,TArray<FLandscapeImportLayerInfo>> Layers;
 Layers.Add(FGuid(),TArray<FLandscapeImportLayerInfo>());
 Land->Import(FGuid::NewGuid(),0,0,Size-1,Size-1,2,63,Heights,nullptr,Layers,
  ELandscapeImportAlphamapType::Additive,TArrayView<const FLandscapeLayer>());
 Land->CreateLandscapeInfo();
 Land->PostEditChange();
 if(Land->LandscapeComponents.Num()!=576)
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA: incomplete Landscape %d != 576"),
         Land->LandscapeComponents.Num());
  World->DestroyActor(Land);
  return nullptr;
 }
 if(ULandscapeSubsystem* Subsystem=World->GetSubsystem<ULandscapeSubsystem>())
  Subsystem->ChangeGridSize(Land->GetLandscapeInfo(),2);
 return Land;
#else
 return nullptr;
#endif
}

// Isolated third-party image-derived new reference; only safe on a new, empty candidate map.
AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateDrazoviaIzurviveCandidateLandscape()
{
#if WITH_EDITOR
 UWorld* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
 constexpr int32 Size=3025;
 if(!World || World->GetPackage()->GetName()!=TEXT("/Game/Maps/ANOMALIA_DrazoviaTopo_NewReference_Candidate"))
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA IZURVIVE: wrong editor world; original v2 is protected"));
  return nullptr;
 }
 for(TActorIterator<ALandscapeProxy> It(World);It;++It)
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA IZURVIVE: landscape already present; refusing to overlay"));
  return nullptr;
 }
 const FString Source=FPaths::Combine(FPaths::ProjectDir(),TEXT("TerrainSource"),TEXT("DRAZOVIA_NEW_REFERENCE"),TEXT("DRAZOVIA_NEW_TOPO_48KM_3025.r16"));
 TArray<uint8> SourceBytes;
 constexpr int64 ExpectedBytes=int64(Size)*int64(Size)*2;
 if(!FFileHelper::LoadFileToArray(SourceBytes,*Source) || SourceBytes.Num()!=ExpectedBytes)
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA IZURVIVE: missing/invalid image-derived raw heightmap: %s"),*Source);
  return nullptr;
 }
 TArray<uint16> HeightsU16;
 HeightsU16.SetNumUninitialized(Size*Size);
 // Windows x64 little-endian: matches the exported R16 stream.
 FMemory::Memcpy(HeightsU16.GetData(),SourceBytes.GetData(),SourceBytes.Num());
 ALandscape* Land=World->SpawnActor<ALandscape>();
 if(!Land)return nullptr;
 Land->SetActorLabel(TEXT("DRAZOVIA_Izurvive_NewReference_48km"));
 Land->SetActorLocation(FVector(-2400000.,-2400000.,0.));
 Land->SetActorScale3D(FVector(4800000./(Size-1),4800000./(Size-1),800.));
 TMap<FGuid,TArray<uint16>> Heights;
 Heights.Add(FGuid(),MoveTemp(HeightsU16));
 TMap<FGuid,TArray<FLandscapeImportLayerInfo>> Layers;
 Layers.Add(FGuid(),TArray<FLandscapeImportLayerInfo>());
 Land->Import(FGuid::NewGuid(),0,0,Size-1,Size-1,2,63,Heights,nullptr,Layers,
  ELandscapeImportAlphamapType::Additive,TArrayView<const FLandscapeLayer>());
 Land->CreateLandscapeInfo();
 Land->PostEditChange();
 if(Land->LandscapeComponents.Num()!=576)
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA IZURVIVE: incomplete Landscape %d != 576"),
         Land->LandscapeComponents.Num());
  World->DestroyActor(Land);
  return nullptr;
 }
 if(ULandscapeSubsystem* Subsystem=World->GetSubsystem<ULandscapeSubsystem>())
  Subsystem->ChangeGridSize(Land->GetLandscapeInfo(),2);
 return Land;
#else
 return nullptr;
#endif
}


// New candidate V2, isolated after prior native import succeeded but Python enumeration failed.
AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateDrazoviaIzurviveCandidateV2Landscape()
{
#if WITH_EDITOR
 UWorld* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
 constexpr int32 Size=3025;
 if(!World || World->GetPackage()->GetName()!=TEXT("/Game/Maps/ANOMALIA_DrazoviaTopo_NewReferenceV2_Candidate"))
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA IZURVIVE V2: wrong editor world; original v2 is protected"));
  return nullptr;
 }
 for(TActorIterator<ALandscapeProxy> It(World);It;++It)
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA IZURVIVE V2: landscape already present; refusing to overlay"));
  return nullptr;
 }
 const FString Source=FPaths::Combine(FPaths::ProjectDir(),TEXT("TerrainSource"),TEXT("DRAZOVIA_NEW_REFERENCE"),TEXT("DRAZOVIA_NEW_TOPO_48KM_3025.r16"));
 TArray<uint8> SourceBytes;
 constexpr int64 ExpectedBytes=int64(Size)*int64(Size)*2;
 if(!FFileHelper::LoadFileToArray(SourceBytes,*Source) || SourceBytes.Num()!=ExpectedBytes)
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA IZURVIVE V2: missing/invalid image-derived raw heightmap: %s"),*Source);
  return nullptr;
 }
 TArray<uint16> HeightsU16;
 HeightsU16.SetNumUninitialized(Size*Size);
 // Windows x64 little-endian: matches the exported R16 stream.
 FMemory::Memcpy(HeightsU16.GetData(),SourceBytes.GetData(),SourceBytes.Num());
 ALandscape* Land=World->SpawnActor<ALandscape>();
 if(!Land)return nullptr;
 Land->SetActorLabel(TEXT("DRAZOVIA_Izurvive_NewReferenceV2_48km"));
 Land->SetActorLocation(FVector(-2400000.,-2400000.,0.));
 Land->SetActorScale3D(FVector(4800000./(Size-1),4800000./(Size-1),800.));
 TMap<FGuid,TArray<uint16>> Heights;
 Heights.Add(FGuid(),MoveTemp(HeightsU16));
 TMap<FGuid,TArray<FLandscapeImportLayerInfo>> Layers;
 Layers.Add(FGuid(),TArray<FLandscapeImportLayerInfo>());
 Land->Import(FGuid::NewGuid(),0,0,Size-1,Size-1,2,63,Heights,nullptr,Layers,
  ELandscapeImportAlphamapType::Additive,TArrayView<const FLandscapeLayer>());
 Land->CreateLandscapeInfo();
 Land->PostEditChange();
 if(Land->LandscapeComponents.Num()!=576)
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA IZURVIVE V2: incomplete Landscape %d != 576"),
         Land->LandscapeComponents.Num());
  World->DestroyActor(Land);
  return nullptr;
 }
 if(ULandscapeSubsystem* Subsystem=World->GetSubsystem<ULandscapeSubsystem>())
  Subsystem->ChangeGridSize(Land->GetLandscapeInfo(),2);
 return Land;
#else
 return nullptr;
#endif
}

int32 UAnomaliaZPrigimaliaWorldImportLibrary::InspectDrazoviaIzurviveCandidateV2Components(AActor* Candidate)
{
#if WITH_EDITOR
 ALandscape* Land=Cast<ALandscape>(Candidate);
 if(!Land || !Land->GetWorld() ||
    Land->GetWorld()->GetPackage()->GetName()!=TEXT("/Game/Maps/ANOMALIA_DrazoviaTopo_NewReferenceV2_Candidate"))
  return -1;
 const int32 N=Land->LandscapeComponents.Num();
 if(N!=576 || !Land->GetLandscapeInfo())
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA V2 native inspection: invalid component count %d or missing LandscapeInfo"),N);
  return -1;
 }
 for(const ULandscapeComponent* Component : Land->LandscapeComponents)
 {
  if(!IsValid(Component) || Component->GetOwner()!=Land)
  {
   UE_LOG(LogTemp,Error,TEXT("DRAZOVIA V2 native inspection: null/foreign LandscapeComponent"));
   return -1;
  }
 }
 UE_LOG(LogTemp,Display,TEXT("DRAZOVIA V2 native inspection: validated %d native LandscapeComponents"),N);
 return N;
#else
 return -1;
#endif
}

// Verified preliminary import: retain native components, defer landscape streaming split.
AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateDrazoviaIzurviveCandidateV3Landscape()
{
#if WITH_EDITOR
 UWorld* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
 constexpr int32 Size=3025;
 if(!World || World->GetPackage()->GetName()!=TEXT("/Game/Maps/ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate"))
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA IZURVIVE V3: wrong editor world; original v2 is protected"));
  return nullptr;
 }
 for(TActorIterator<ALandscapeProxy> It(World);It;++It)
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA IZURVIVE V3: landscape already present; refusing to overlay"));
  return nullptr;
 }
 const FString Source=FPaths::Combine(FPaths::ProjectDir(),TEXT("TerrainSource"),TEXT("DRAZOVIA_NEW_REFERENCE"),TEXT("DRAZOVIA_NEW_TOPO_48KM_3025.r16"));
 TArray<uint8> SourceBytes;
 constexpr int64 ExpectedBytes=int64(Size)*int64(Size)*2;
 if(!FFileHelper::LoadFileToArray(SourceBytes,*Source) || SourceBytes.Num()!=ExpectedBytes)
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA IZURVIVE V3: missing/invalid image-derived raw heightmap: %s"),*Source);
  return nullptr;
 }
 TArray<uint16> HeightsU16;
 HeightsU16.SetNumUninitialized(Size*Size);
 // Windows x64 little-endian: matches the exported R16 stream.
 FMemory::Memcpy(HeightsU16.GetData(),SourceBytes.GetData(),SourceBytes.Num());
 ALandscape* Land=World->SpawnActor<ALandscape>();
 if(!Land)return nullptr;
 Land->SetActorLabel(TEXT("DRAZOVIA_Izurvive_NewReferenceV3_48km"));
 Land->SetActorLocation(FVector(-2400000.,-2400000.,0.));
 Land->SetActorScale3D(FVector(4800000./(Size-1),4800000./(Size-1),800.));
 TMap<FGuid,TArray<uint16>> Heights;
 Heights.Add(FGuid(),MoveTemp(HeightsU16));
 TMap<FGuid,TArray<FLandscapeImportLayerInfo>> Layers;
 Layers.Add(FGuid(),TArray<FLandscapeImportLayerInfo>());
 Land->Import(FGuid::NewGuid(),0,0,Size-1,Size-1,2,63,Heights,nullptr,Layers,
  ELandscapeImportAlphamapType::Additive,TArrayView<const FLandscapeLayer>());
 Land->CreateLandscapeInfo();
 Land->PostEditChange();
 if(Land->LandscapeComponents.Num()!=576)
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA IZURVIVE V3: incomplete Landscape %d != 576"),
         Land->LandscapeComponents.Num());
  World->DestroyActor(Land);
  return nullptr;
 }
 // V3: DO NOT partition the Landscape here. ChangeGridSize previously migrated the
 // 576 components away from the root actor, causing V1/V2's post-import checks
 // to observe zero. Save and verify the actual terrain before any later grid split.
 UE_LOG(LogTemp,Display,TEXT("DRAZOVIA V3: 576 root components verified; Landscape grid partitioning deferred"));
 return Land;
#else
 return nullptr;
#endif
}

int32 UAnomaliaZPrigimaliaWorldImportLibrary::InspectDrazoviaIzurviveCandidateV3Components(AActor* Candidate)
{
#if WITH_EDITOR
 ALandscape* Land=Cast<ALandscape>(Candidate);
 if(!Land || !Land->GetWorld() ||
    Land->GetWorld()->GetPackage()->GetName()!=TEXT("/Game/Maps/ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate"))
  return -1;
 const int32 N=Land->LandscapeComponents.Num();
 if(N!=576 || !Land->GetLandscapeInfo())
 {
  UE_LOG(LogTemp,Error,TEXT("DRAZOVIA V3 native inspection: invalid component count %d or missing LandscapeInfo"),N);
  return -1;
 }
 for(const ULandscapeComponent* Component : Land->LandscapeComponents)
 {
  if(!IsValid(Component) || Component->GetOwner()!=Land)
  {
   UE_LOG(LogTemp,Error,TEXT("DRAZOVIA V3 native inspection: null/foreign LandscapeComponent"));
   return -1;
  }
 }
 UE_LOG(LogTemp,Display,TEXT("DRAZOVIA V3 native inspection: validated %d native LandscapeComponents"),N);
 return N;
#else
 return -1;
#endif
}


// Dedicated F.A.L.C reference importer; no premature Landscape partitioning.
AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateFalcReferenceLandscape()
{
#if WITH_EDITOR
 UWorld* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
 constexpr int32 Size=2017;
 if(!World || World->GetPackage()->GetName()!=TEXT("/Game/Maps/PRIGIMALIA_FALC"))
 {
  UE_LOG(LogTemp,Error,TEXT("FALC REFERENCE: wrong editor world; original v2 is protected"));
  return nullptr;
 }
 for(TActorIterator<ALandscapeProxy> It(World);It;++It)
 {
  UE_LOG(LogTemp,Error,TEXT("FALC REFERENCE: landscape already present; refusing to overlay"));
  return nullptr;
 }
 const FString Source=FPaths::Combine(FPaths::ProjectDir(),TEXT("TerrainSource"),TEXT("FALC"),TEXT("FALC_26_5KM_MASTER_2017.r16"));
 TArray<uint8> SourceBytes;
 constexpr int64 ExpectedBytes=int64(Size)*int64(Size)*2;
 if(!FFileHelper::LoadFileToArray(SourceBytes,*Source) || SourceBytes.Num()!=ExpectedBytes)
 {
  UE_LOG(LogTemp,Error,TEXT("FALC REFERENCE: missing/invalid image-derived raw heightmap: %s"),*Source);
  return nullptr;
 }
 TArray<uint16> HeightsU16;
 HeightsU16.SetNumUninitialized(Size*Size);
 // Windows x64 little-endian: matches the exported R16 stream.
 FMemory::Memcpy(HeightsU16.GetData(),SourceBytes.GetData(),SourceBytes.Num());
 ALandscape* Land=World->SpawnActor<ALandscape>();
 if(!Land)return nullptr;
 Land->SetActorLabel(TEXT("FALC_Reference_26_5km"));
 Land->SetActorLocation(FVector(-1325000.,-1325000.,0.));
 Land->SetActorScale3D(FVector(2650000./(Size-1),2650000./(Size-1),800.));
 TMap<FGuid,TArray<uint16>> Heights;
 Heights.Add(FGuid(),MoveTemp(HeightsU16));
 TMap<FGuid,TArray<FLandscapeImportLayerInfo>> Layers;
 Layers.Add(FGuid(),TArray<FLandscapeImportLayerInfo>());
 Land->Import(FGuid::NewGuid(),0,0,Size-1,Size-1,2,63,Heights,nullptr,Layers,
  ELandscapeImportAlphamapType::Additive,TArrayView<const FLandscapeLayer>());
 Land->CreateLandscapeInfo();
 Land->PostEditChange();
 if(Land->LandscapeComponents.Num()!=256)
 {
  UE_LOG(LogTemp,Error,TEXT("FALC REFERENCE: incomplete Landscape %d != 256"),
         Land->LandscapeComponents.Num());
  World->DestroyActor(Land);
  return nullptr;
 }
 // V3: DO NOT partition the Landscape here. ChangeGridSize previously migrated the
 // 576 components away from the root actor, causing V1/V2's post-import checks
 // to observe zero. Save and verify the actual terrain before any later grid split.
 UE_LOG(LogTemp,Display,TEXT("FALC REFERENCE: 256 root components verified; Landscape grid partitioning deferred"));
 return Land;
#else
 return nullptr;
#endif
}

int32 UAnomaliaZPrigimaliaWorldImportLibrary::InspectFalcReferenceComponents(AActor* Candidate)
{
#if WITH_EDITOR
 ALandscape* Land=Cast<ALandscape>(Candidate);
 if(!Land || !Land->GetWorld() ||
    Land->GetWorld()->GetPackage()->GetName()!=TEXT("/Game/Maps/PRIGIMALIA_FALC"))
  return -1;
 const int32 N=Land->LandscapeComponents.Num();
 if(N!=256 || !Land->GetLandscapeInfo())
 {
  UE_LOG(LogTemp,Error,TEXT("FALC REFERENCE native inspection: invalid component count %d or missing LandscapeInfo"),N);
  return -1;
 }
 for(const ULandscapeComponent* Component : Land->LandscapeComponents)
 {
  if(!IsValid(Component) || Component->GetOwner()!=Land)
  {
   UE_LOG(LogTemp,Error,TEXT("FALC REFERENCE native inspection: null/foreign LandscapeComponent"));
   return -1;
  }
 }
 UE_LOG(LogTemp,Display,TEXT("FALC REFERENCE native inspection: validated %d native LandscapeComponents"),N);
 return N;
#else
 return -1;
#endif
}



AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateArchipelagoLandscape() { return CreateLandscape(false); }
AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateInhabitedArchipelagoLandscape() { return CreateLandscape(true); }

namespace
{
 AnomaliaZPrigimaliaExtraWorlds::EWorld ResolveAdditionalWorld(const FString& MapIdentifier)
 {
  using namespace AnomaliaZPrigimaliaExtraWorlds;
  if(MapIdentifier==TEXT("KARSKOV"))return EWorld::Karskov;
  if(MapIdentifier==TEXT("VORGRAD"))return EWorld::Vorgrad;
  if(MapIdentifier==TEXT("NEMORIS"))return EWorld::Nemoris;
  if(MapIdentifier==TEXT("DRAKHEIM"))return EWorld::Drakheim;
  if(MapIdentifier==TEXT("SOLYNACALYRA"))return EWorld::Solynacalyra;
  if(MapIdentifier==TEXT("NEXAVARKHOS"))return EWorld::Nexavarkhos;
  return EWorld::Invalid;
 }
}
double UAnomaliaZPrigimaliaWorldImportLibrary::NamedWorldHeight(const FString& MapIdentifier,double EastMeters,double NorthMeters)
{
 using namespace AnomaliaZPrigimaliaExtraWorlds;
 if(!FMath::IsFinite(EastMeters)||!FMath::IsFinite(NorthMeters))return -400.;
 return Height(ResolveAdditionalWorld(MapIdentifier),EastMeters,NorthMeters);
}
AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateNamedWorldLandscape(const FString& MapIdentifier)
{
#if WITH_EDITOR
 using namespace AnomaliaZPrigimaliaExtraWorlds;
 const EWorld Kind=ResolveAdditionalWorld(MapIdentifier);
 const int32 Side=SideMeters(Kind),Size=Resolution(Kind);
 if(Side==0 || Size==0)return nullptr;
 UWorld* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
 if(!World || World->GetPackage()->GetName()!=TEXT("/Game/Maps/PRIGIMALIA_")+MapIdentifier+TEXT("_TerrainPreview"))return nullptr;
 for(TActorIterator<ALandscapeProxy> It(World);It;++It)return nullptr; // Never overlay existing terrain.
 TArray<uint16> Samples;Samples.SetNumUninitialized(Size*Size);
 const double Half=double(Side)/2.;
 // The user supplied merged topo is an independently-authored synthetic R16
 // reconstruction. Explicit opt-in prevents silently overwriting old source.
 const bool bUsePhotoR16=FParse::Param(FCommandLine::Get(),TEXT("ANOMALIAUseUserTopoR16"));
 if(bUsePhotoR16)
 {
  const FString Source=FPaths::Combine(FPaths::ProjectDir(),TEXT("TerrainSource"),MapIdentifier,MapIdentifier+TEXT(".r16"));
  TArray<uint8> SourceBytes;
  const int64 ExpectedBytes=int64(Size)*int64(Size)*int64(sizeof(uint16));
  if(!FFileHelper::LoadFileToArray(SourceBytes,*Source) || int64(SourceBytes.Num())!=ExpectedBytes)
  {
   UE_LOG(LogTemp,Error,TEXT("ANOMALIA user photo-driven source missing or invalid: %s (%lld bytes required)"),*Source,(long long)ExpectedBytes);
   return nullptr; // Do not substitute unrelated procedural terrain!
  }
  // Native Windows Win64 is little endian, matching the R16 export.
  FMemory::Memcpy(Samples.GetData(),SourceBytes.GetData(),SourceBytes.Num());
  UE_LOG(LogTemp,Display,TEXT("ANOMALIA user-provided R16 terrain selected for %s (%d samples per axis)"),*MapIdentifier,Size);
 }
 else
 {
  for(int32 Y=0;Y<Size;++Y)for(int32 X=0;X<Size;++X)
  {
   const double East=-Half+double(Side)*X/(Size-1);
   const double North=Half-double(Side)*Y/(Size-1);
   Samples[Y*Size+X]=Encode(Height(Kind,East,North));
  }
 }
 ALandscape* Land=World->SpawnActor<ALandscape>();
 if(!Land)return nullptr;
 Land->SetActorLabel(TEXT("PRIGIMALIA_")+MapIdentifier+TEXT("_Landscape"));
 Land->SetActorLocation(FVector(-Half*100.,-Half*100.,0.));
 const double CmPerSample=double(Side)*100./(Size-1);
 Land->SetActorScale3D(FVector(CmPerSample,CmPerSample,800.));
 TMap<FGuid,TArray<uint16>> Heights;Heights.Add(FGuid(),MoveTemp(Samples));
 TMap<FGuid,TArray<FLandscapeImportLayerInfo>> Layers;Layers.Add(FGuid(),TArray<FLandscapeImportLayerInfo>());
 Land->Import(FGuid::NewGuid(),0,0,Size-1,Size-1,2,63,Heights,nullptr,Layers,
  ELandscapeImportAlphamapType::Additive,TArrayView<const FLandscapeLayer>());
 Land->CreateLandscapeInfo();
 Land->PostEditChange();
 const int32 Expected=(Size==3025)?576:(Size==2017)?256:(Size==1513)?144:(Size==1009)?64:0;
 if(Land->LandscapeComponents.Num()!=Expected)
 {
  UE_LOG(LogTemp,Error,TEXT("PRIGIMALIA %s terrain components mismatch: %d != %d"),
   *MapIdentifier,Land->LandscapeComponents.Num(),Expected);
  return nullptr;
 }
 // Verified V3 fix: keep root Landscape components until map is durably saved.
 // Terrain streaming grid/proxy migration must be tested as an independent later operation.
 UE_LOG(LogTemp,Display,TEXT("PRIGIMALIA terrain preview: native components retained before save"));
 return Land;
#else
 return nullptr;
#endif
}


int32 UAnomaliaZPrigimaliaWorldImportLibrary::InspectNamedWorldPreviewComponents(AActor* Candidate,const FString& MapIdentifier)
{
#if WITH_EDITOR
 using namespace AnomaliaZPrigimaliaExtraWorlds;
 ALandscape* Land=Cast<ALandscape>(Candidate);
 const EWorld Kind=ResolveAdditionalWorld(MapIdentifier);
 const int32 Size=Resolution(Kind);
 const int32 Expected=(Size==3025)?576:(Size==2017)?256:(Size==1513)?144:(Size==1009)?64:0;
 if(!Land || Size==0 || !Land->GetWorld() ||
    Land->GetWorld()->GetPackage()->GetName()!=TEXT("/Game/Maps/PRIGIMALIA_")+MapIdentifier+TEXT("_TerrainPreview"))
  return -1;
 const int32 Actual=Land->LandscapeComponents.Num();
 if(Actual!=Expected || !Land->GetLandscapeInfo())
 {
  UE_LOG(LogTemp,Error,TEXT("PRIGIMALIA preview %s component verification failed: %d expected %d"),
   *MapIdentifier,Actual,Expected);
  return -1;
 }
 for(ULandscapeComponent* Component:Land->LandscapeComponents)
  if(!IsValid(Component) || Component->GetOwner()!=Land)return -1;
 UE_LOG(LogTemp,Display,TEXT("PRIGIMALIA preview %s native components validated: %d"),*MapIdentifier,Actual);
 return Actual;
#else
 return -1;
#endif
}

AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateChernaskaluxriaLandscapeTile(int32 Col,int32 Row)
{
#if WITH_EDITOR
 if(Col<0 || Col>=20 || Row<0 || Row>=20)return nullptr;
 UWorld* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
 if(!World || World->GetPackage()->GetName()!=TEXT("/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA"))
  return nullptr;
 const FString Name=FString::Printf(TEXT("CHERNASKALUXRIA_x%02d_y%02d"),Col,Row);
 const FString Source=FPaths::Combine(FPaths::ProjectDir(),TEXT("TerrainSource"),TEXT("CHERNASKALUXRIA"),Name+TEXT(".r16"));
 TArray<uint8> Bytes;
 if(!FFileHelper::LoadFileToArray(Bytes,*Source) || Bytes.Num()!=253*253*2)
 {
  UE_LOG(LogTemp,Error,TEXT("CHERNASKALUXRIA missing/corrupt source tile %s"),*Source);
  return nullptr;
 }
 // Duplicate protection across loaded landscape actors. The native launch
 // script additionally checks persistent tile receipts before calling.
 for(TActorIterator<ALandscapeProxy> It(World);It;++It)
  if(It->GetActorLabel()==Name)
  {
   UE_LOG(LogTemp,Error,TEXT("CHERNASKALUXRIA tile already exists: %s"),*Name);
   return nullptr;
  }
 TArray<uint16> Samples;
 Samples.SetNumUninitialized(253*253);
 FMemory::Memcpy(Samples.GetData(),Bytes.GetData(),Bytes.Num()); // Generated LE u16; Win64 is little endian.
 const double West=-50000.+5000.*Col;
 const double North=50000.-5000.*Row;
 ALandscape* Land=World->SpawnActor<ALandscape>();
 if(!Land)return nullptr;
 Land->SetActorLabel(Name);
 Land->SetActorLocation(FVector(West*100.,-North*100.,0.));
 Land->SetActorScale3D(FVector(500000./252.,500000./252.,800.));
 TMap<FGuid,TArray<uint16>> Heights;
 Heights.Add(FGuid(),MoveTemp(Samples));
 TMap<FGuid,TArray<FLandscapeImportLayerInfo>> Layers;
 Layers.Add(FGuid(),TArray<FLandscapeImportLayerInfo>());
 Land->Import(FGuid::NewGuid(),0,0,252,252,2,63,Heights,nullptr,Layers,
  ELandscapeImportAlphamapType::Additive,TArrayView<const FLandscapeLayer>());
 Land->CreateLandscapeInfo();
 Land->PostEditChange();
 if(Land->LandscapeComponents.Num()!=4)
 {
  UE_LOG(LogTemp,Error,TEXT("CHERNASKALUXRIA incomplete tile landscape: %s"),*Name);
  return nullptr;
 }
 // Keep the actual four native components on this Landscape until the
 // independent map is durably saved; grid/proxy migration is a later step.
 UE_LOG(LogTemp,Display,TEXT("CHERNASKALUXRIA: native tile components retained for safe save"));
 return Land;
#else
 return nullptr;
#endif
}

int32 UAnomaliaZPrigimaliaWorldImportLibrary::InspectChernaskaluxriaTileComponents(AActor* Candidate)
{
#if WITH_EDITOR
 ALandscape* Land=Cast<ALandscape>(Candidate);
 if(!Land || !Land->GetWorld() ||
    Land->GetWorld()->GetPackage()->GetName()!=TEXT("/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA"))
  return -1;
 if(Land->LandscapeComponents.Num()!=4 || !Land->GetLandscapeInfo())
  return -1;
 for(ULandscapeComponent* Component:Land->LandscapeComponents)
  if(!IsValid(Component) || Component->GetOwner()!=Land)return -1;
 UE_LOG(LogTemp,Display,TEXT("CHERNASKALUXRIA native tile components verified: 4"));
 return 4;
#else
 return -1;
#endif
}

TArray<FVector2D> UAnomaliaZPrigimaliaWorldImportLibrary::InhabitedSettlementSites()
{
 TArray<FVector2D> Result;
 for(const auto& Site:AnomaliaZPrigimaliaInhabited::Sites)Result.Add(FVector2D(Site[0],Site[1]));
 return Result;
}
double UAnomaliaZPrigimaliaWorldImportLibrary::InhabitedArchipelagoHeight(double EastMeters,double NorthMeters)
{
 if(!FMath::IsFinite(EastMeters)||!FMath::IsFinite(NorthMeters))return 0;
 return AnomaliaZPrigimaliaInhabited::Height(EastMeters,NorthMeters);
}

FString UAnomaliaZPrigimaliaWorldImportLibrary::RefreshArchipelagoRenderResources(bool bRefresh)
{
#if WITH_EDITOR
 UWorld* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
 if(!World || (World->GetPackage()->GetName()!=TEXT("/Game/Maps/ANOMALIA_Archipelago_v2") &&
               World->GetPackage()->GetName()!=TEXT("/Game/Maps/ANOMALIA_Inhabited_v2")))
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
