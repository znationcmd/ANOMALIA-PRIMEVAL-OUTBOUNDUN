// Exports the SAME height data consumed by the 11-world Unreal C++ library.
// An exact World Partition landscape source asset, not an already saved .umap.
#include "unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaElevenWorldHeights.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <stdexcept>
#include <cstdint>
using namespace AnomaliaZPrigimaliaElevenWorlds;
struct World{
  const char* id;
  EWorld kind;
};
int main(int argc,char**argv){
 try{
   if(argc!=2)throw std::runtime_error("Usage: exporter <empty output directory>");
   const std::filesystem::path out=std::filesystem::absolute(argv[1]);
   std::filesystem::create_directories(out);
   if(!std::filesystem::is_directory(out))throw std::runtime_error("Output path missing");
   const World maps[]={
    {"APOCALYPTIC_OUTBREAK",EWorld::ApocalypticOutbreak},
    {"MOROEDENACHTMERR",EWorld::Morodenachtmerr},
    {"MOKUPUNAWAI",EWorld::Mokupunawai},
    {"NASDARAS",EWorld::Nasdaras},
    {"KIRYUMORI",EWorld::Kiryumori},
    {"ARANYAPURA",EWorld::Aranyapura},
    {"FALC",EWorld::Falc},
    {"UNKNOWN_HORROR_X",EWorld::UnknownHorrorX},
    {"KONIGSBRUCK",EWorld::Konigsbruck},
    {"SKJAEROYAS",EWorld::Skjaeroyas},
    {"VALHALLA_EXTINCTION",EWorld::ValhallaExtinction}
   };
   constexpr std::size_t expected=11;
   std::size_t made=0;
   for(const auto& m:maps){
     const int w=WidthMeters(m.kind),h=HeightMeters(m.kind),res=Resolution(m.kind);
     if(w<1000 || h<1000 || (res!=1009&&res!=2017&&res!=3025))throw std::runtime_error("Unexpected world dimensions");
     const auto file=out/(std::string("PRIGIMALIA_")+m.id+"_R16.raw");
     if(std::filesystem::exists(file))throw std::runtime_error("Refuse overwriting "+file.string());
     std::ofstream s(file,std::ios::binary|std::ios::out|std::ios::trunc);
     if(!s)throw std::runtime_error("Cannot create "+file.string());
     std::vector<std::uint16_t> row(std::size_t(res),0u);
     const double hw=w/2., hh=h/2.;
     for(int y=0;y<res;++y){
       const double north=hh-double(h)*y/(res-1);
       for(int x=0;x<res;++x){
         const double east=-hw+double(w)*x/(res-1);
         row[std::size_t(x)]=Encode(Height(m.kind,east,north));
       }
       // Windows target is little-endian, as is the official Linux CI runner.
       s.write(reinterpret_cast<const char*>(row.data()),std::streamsize(row.size()*sizeof(std::uint16_t)));
       if(!s)throw std::runtime_error("Error writing "+file.string());
     }
     s.close();
     const auto expectedBytes=std::uintmax_t(res)*std::uintmax_t(res)*2u;
     if(std::filesystem::file_size(file)!=expectedBytes)throw std::runtime_error("Heightfield byte count mismatch");
     const auto meta=out/(std::string("PRIGIMALIA_")+m.id+"_R16.json");
     std::ofstream j(meta,std::ios::binary|std::ios::out|std::ios::trunc);
     j<<"{\n  \"id\": \""<<m.id<<"\",\n  \"widthMeters\": "<<w
      <<",\n  \"heightMeters\": "<<h
      <<",\n  \"resolution\": "<<res
      <<",\n  \"expectedLandscapeComponents\": "<<((res-1)/126)*((res-1)/126)
      <<",\n  \"format\": \"RAW16 unsigned little endian\",\n  \"layout\": \"Unreal landscape X increasing east, rows north to south\",\n  \"nativeUnrealMapAlreadySaved\": false,\n  \"existingMapsModified\": false\n}\n";
     j.close();
     if(!j)throw std::runtime_error("Metadata write error");
     std::cout<<"ANOMALIA_NATIVE_RAW16_EXPORTED id="<<m.id<<" bytes="<<expectedBytes<<" width="<<w
              <<" height="<<h<<" resolution="<<res<<"\n"<<std::flush;
     ++made;
   }
   if(made!=expected)throw std::runtime_error("Not all 11 landscape files exported");
   std::cout<<"ANOMALIA_ELEVEN_RAW16_EXPORTED_COUNT=11\n";
   return 0;
 }catch(const std::exception& e){
   std::cerr<<"ANOMALIA_RAW16_EXPORT_FAILED="<<e.what()<<"\n";
   return 2;
 }
}
