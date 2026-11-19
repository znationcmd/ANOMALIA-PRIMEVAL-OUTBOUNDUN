#include "unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaElevenWorldHeights.h"
#include <cassert>
#include <cmath>
#include <iostream>
using namespace AnomaliaZPrigimaliaElevenWorlds;
struct Spec{ EWorld kind; int width, height, resolution; };
int main(){
 const Spec all[]={
  {EWorld::ApocalypticOutbreak,15000,15000,1009},
  {EWorld::Morodenachtmerr,10000,10000,1009},
  {EWorld::Mokupunawai,21000,21000,2017},
  {EWorld::Nasdaras,18000,26000,2017},
  {EWorld::Kiryumori,20000,20000,2017},
  {EWorld::Aranyapura,20000,20000,2017},
  {EWorld::Falc,32000,22000,2017},
  {EWorld::UnknownHorrorX,12000,12000,1009},
  {EWorld::Konigsbruck,30000,30000,3025},
  {EWorld::Skjaeroyas,15000,15000,1009},
  {EWorld::ValhallaExtinction,24000,24000,2017}
 };
 for(const auto& s:all){
  assert(WidthMeters(s.kind)==s.width);
  assert(HeightMeters(s.kind)==s.height);
  assert(Resolution(s.kind)==s.resolution);
  const int components=(s.resolution-1)/126;
  assert(components==8 || components==16 || components==24);
  for(int iy=-4;iy<=4;++iy)for(int ix=-4;ix<=4;++ix){
    const double x=double(ix)*s.width/11, y=double(iy)*s.height/11;
    double z=Height(s.kind,x,y);
    assert(std::isfinite(z)&&z>-500.&&z<3200.);
    assert(Height(s.kind,x,y)==z);
    const auto encoded=Encode(z);
    assert(encoded<=65535);
  }
  assert(Height(s.kind,s.width/2.+1,0)==-400.);
  assert(Height(s.kind,0,s.height/2.+1)==-400.);
 }
 assert(WidthMeters(EWorld::Karskov)==30000);
 assert(WidthMeters(EWorld::Moscovie)==10000);
 assert(WidthMeters(EWorld::BotSever)==50000);
 std::cout<<"ANOMALIA_ELEVEN_MISSING_MAP_HEIGHTFIELDS_AND_DIMENSIONS_VALID=1\n";
}