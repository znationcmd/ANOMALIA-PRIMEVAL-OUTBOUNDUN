#include "World/AnomaliaZPrigimaliaExtraWorldHeights.h"
#include <array>
#include <cerrno>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
int main(int argc,char** argv)
{
 using namespace AnomaliaZPrigimaliaExtraWorlds;
 if(argc!=2)throw std::runtime_error("Usage: export_four_topographic_heightmaps OUTDIR");
 const std::filesystem::path out(argv[1]);
 std::filesystem::create_directories(out);
 struct Spec{EWorld id;const char* name;};
 constexpr std::array<Spec,4> worlds={{{EWorld::Vorgrad,"VORGRAD"},
  {EWorld::Nexavarkhos,"NEXAVARKHOS"},{EWorld::Solynacalyra,"SOLYNACALYRA"},
  {EWorld::Drakheim,"DRAKHEIM"}}};
 for(const auto& entry:worlds)
 {
  const int side=SideMeters(entry.id),resolution=Resolution(entry.id);
  const auto path=out/(std::string("PRIGIMALIA_")+entry.name+"_ORIGINAL_TOPO.r16");
  if(std::filesystem::exists(path))
   throw std::runtime_error("Refusing overwrite of an existing terrain source");
  std::ofstream file(path,std::ios::binary|std::ios::out|std::ios::trunc);
  if(!file)throw std::runtime_error("Unable to open terrain source output");
  int dry=0,wet=0;
  double minz=1e10,maxz=-1e10;
  for(int row=0;row<resolution;++row)
  {
   const double north=side/2.-double(side)*row/double(resolution-1);
   for(int col=0;col<resolution;++col)
   {
    const double east=-side/2.+double(side)*col/double(resolution-1);
    const double z=Height(entry.id,east,north);
    if(!std::isfinite(z))throw std::runtime_error("Invalid native height sample");
    const std::uint16_t encoded=Encode(z);
    const char littleEndian[2]={char(encoded&255u),char((encoded>>8u)&255u)};
    file.write(littleEndian,2);
    minz=std::min(minz,z);maxz=std::max(maxz,z);
    if(z>0)++dry;else ++wet;
   }
  }
  file.close();
  if(!file || std::filesystem::file_size(path)!=2ull*resolution*resolution)
   throw std::runtime_error("Incomplete landscape source; refusing certification");
  if(dry<1000||maxz-minz<50.)
   throw std::runtime_error("Terrain failed land/highland geometry requirements");
  std::cout<<"ORIGINAL_FUSION_R16 "<<entry.name<<" sizeKm="<<(side/1000)
   <<" samples="<<resolution<<" drySamples="<<dry<<" waterSamples="<<wet
   <<" min="<<minz<<" max="<<maxz<<" bytes="<<std::filesystem::file_size(path)
   <<" state=SOURCE_NOT_UNREAL_UMAP\n";
 }
}
