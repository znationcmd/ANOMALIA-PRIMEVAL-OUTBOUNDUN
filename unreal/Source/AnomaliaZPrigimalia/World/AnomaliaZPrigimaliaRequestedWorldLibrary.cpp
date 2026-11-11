#include "AnomaliaZPrigimaliaRequestedWorldLibrary.h"
#include "AnomaliaZPrigimaliaRequestedWorldHeights.h"
#if WITH_EDITOR
#include "Editor.h"
#include "Landscape.h"
#include "LandscapeInfo.h"
#include "LandscapeComponent.h"
#include "LandscapeSubsystem.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "UObject/Package.h"
#endif
namespace {
using namespace AnomaliaZPrigimaliaExtraWorlds;
EWorld ResolveRequested(const FString& Id) {
 if(Id==TEXT("YUDINAVIA"))return EWorld::Yudinavia;
 if(Id==TEXT("MOSCOVIE"))return EWorld::Moscovie;
 if(Id==TEXT("CORSIVIA"))return EWorld::Corsivia;
 if(Id==TEXT("BOT_SEVER"))return EWorld::BotSever;
 return EWorld::Invalid;
}
}
double UAnomaliaZPrigimaliaRequestedWorldLibrary::NamedWorldHeight(const FString& Id,double East,double North) {
 return AnomaliaZPrigimaliaExtraWorlds::Height(ResolveRequested(Id),East,North);
}
AActor* UAnomaliaZPrigimaliaRequestedWorldLibrary::CreateNamedWorldLandscape(const FString& Id) {
#if WITH_EDITOR
 using namespace AnomaliaZPrigimaliaExtraWorlds;
 const EWorld Kind=ResolveRequested(Id);
 const int32 Side=SideMeters(Kind),Size=Resolution(Kind);
 if(Side<=0||Size<=1)return nullptr;
 UWorld* World=GEditor?GEditor->GetEditorWorldContext().World():nullptr;
 if(!World||World->GetPackage()->GetName()!=TEXT("/Game/Maps/PRIGIMALIA_")+Id)return nullptr;
 for(TActorIterator<ALandscapeProxy> It(World);It;++It)return nullptr;
 const double Half=double(Side)/2.;
 TArray<uint16> Samples;Samples.SetNumUninitialized(Size*Size);
 for(int32 Y=0;Y<Size;++Y)for(int32 X=0;X<Size;++X)
  Samples[Y*Size+X]=Encode(Height(Kind,-Half+double(Side)*X/(Size-1),Half-double(Side)*Y/(Size-1)));
 ALandscape* Land=World->SpawnActor<ALandscape>();
 if(!Land)return nullptr;
 Land->SetActorLabel(TEXT("PRIGIMALIA_")+Id+TEXT("_Landscape"));
 Land->SetActorLocation(FVector(-Half*100.,-Half*100.,0.));
 const double Scale=double(Side)*100./(Size-1);
 Land->SetActorScale3D(FVector(Scale,Scale,800.));
 TMap<FGuid,TArray<uint16>> Heights;Heights.Add(FGuid(),MoveTemp(Samples));
 TMap<FGuid,TArray<FLandscapeImportLayerInfo>> Layers;Layers.Add(FGuid(),TArray<FLandscapeImportLayerInfo>());
 Land->Import(FGuid::NewGuid(),0,0,Size-1,Size-1,2,63,Heights,nullptr,Layers,
  ELandscapeImportAlphamapType::Additive,TArrayView<const FLandscapeLayer>());
 Land->CreateLandscapeInfo();Land->PostEditChange();
 const int32 Expected=((Size-1)/126)*((Size-1)/126);
 if(Land->LandscapeComponents.Num()!=Expected)return nullptr;
 if(ULandscapeSubsystem* System=World->GetSubsystem<ULandscapeSubsystem>())
  System->ChangeGridSize(Land->GetLandscapeInfo(),2);
 return Land;
#else
 return nullptr;
#endif
}
