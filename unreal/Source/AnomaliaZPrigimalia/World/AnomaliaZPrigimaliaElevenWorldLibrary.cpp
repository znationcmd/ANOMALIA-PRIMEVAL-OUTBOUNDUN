#include "AnomaliaZPrigimaliaElevenWorldLibrary.h"
#include "AnomaliaZPrigimaliaElevenWorldHeights.h"
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
using namespace AnomaliaZPrigimaliaElevenWorlds;
EWorld ResolveRequested(const FString& Id) {
 if(Id==TEXT("YUDINAVIA"))return EWorld::Yudinavia;
 if(Id==TEXT("MOSCOVIE"))return EWorld::Moscovie;
 if(Id==TEXT("CORSIVIA"))return EWorld::Corsivia;
 if(Id==TEXT("BOT_SEVER"))return EWorld::BotSever;
 if(Id==TEXT("APOCALYPTIC_OUTBREAK"))return EWorld::ApocalypticOutbreak;
 if(Id==TEXT("MOROEDENACHTMERR"))return EWorld::Morodenachtmerr;
 if(Id==TEXT("NASDARAS"))return EWorld::Nasdaras;
 if(Id==TEXT("MOKUPUNAWAI"))return EWorld::Mokupunawai;
 if(Id==TEXT("FALC"))return EWorld::Falc;
 if(Id==TEXT("UNKNOWN_HORROR_X"))return EWorld::UnknownHorrorX;
 if(Id==TEXT("KONIGSBRUCK"))return EWorld::Konigsbruck;
 if(Id==TEXT("SKJAEROYAS"))return EWorld::Skjaeroyas;
 if(Id==TEXT("VALHALLA_EXTINCTION"))return EWorld::ValhallaExtinction;
 if(Id==TEXT("KIRYUMORI"))return EWorld::Kiryumori;
 if(Id==TEXT("ARANYAPURA"))return EWorld::Aranyapura;
 return EWorld::Invalid;
}
}
double UAnomaliaZPrigimaliaElevenWorldLibrary::NamedWorldHeight(const FString& Id,double East,double North) {
 return AnomaliaZPrigimaliaElevenWorlds::Height(ResolveRequested(Id),East,North);
}
AActor* UAnomaliaZPrigimaliaElevenWorldLibrary::CreateNamedWorldLandscape(const FString& Id) {
#if WITH_EDITOR
 using namespace AnomaliaZPrigimaliaElevenWorlds;
 const EWorld Kind=ResolveRequested(Id);
 const int32 Width=WidthMeters(Kind),Height=HeightMeters(Kind),Size=Resolution(Kind);
 if(Width<=0||Height<=0||Size<=1)return nullptr;
 UWorld* World=GEditor?GEditor->GetEditorWorldContext().World():nullptr;
 if(!World||World->GetPackage()->GetName()!=TEXT("/Game/Maps/PRIGIMALIA_")+Id)return nullptr;
 for(TActorIterator<ALandscapeProxy> It(World);It;++It)return nullptr;
 const double HalfWidth=double(Width)/2.,HalfHeight=double(Height)/2.;
 TArray<uint16> Samples;Samples.SetNumUninitialized(Size*Size);
 for(int32 Y=0;Y<Size;++Y)for(int32 X=0;X<Size;++X)
  Samples[Y*Size+X]=Encode(AnomaliaZPrigimaliaElevenWorlds::Height(Kind,-HalfWidth+double(Width)*X/(Size-1),HalfHeight-double(Height)*Y/(Size-1)));
 ALandscape* Land=World->SpawnActor<ALandscape>();
 if(!Land)return nullptr;
 Land->SetActorLabel(TEXT("PRIGIMALIA_")+Id+TEXT("_Landscape"));
 Land->SetActorLocation(FVector(-HalfWidth*100.,-HalfHeight*100.,0.));
 const double ScaleX=double(Width)*100./(Size-1),ScaleY=double(Height)*100./(Size-1);
 Land->SetActorScale3D(FVector(ScaleX,ScaleY,800.));
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
