#include "unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaExtraWorldHeights.h"
#include <cassert>
#include <cmath>
#include <iostream>
using namespace AnomaliaZPrigimaliaExtraWorlds;
int main() {
 const EWorld worlds[]={EWorld::Kiryumori,EWorld::Aranyapura};
 for(const EWorld w:worlds){
  assert(SideMeters(w)==20000);
  assert(WidthMeters(w)==20000 && HeightMeters(w)==20000);
  assert(Resolution(w)==2017);
  assert(((Resolution(w)-1)/126)*((Resolution(w)-1)/126)==256);
  for(int y=-9000;y<=9000;y+=1500)
   for(int x=-9000;x<=9000;x+=1500){
    const double h=Height(w,x,y);
    assert(std::isfinite(h) && h>-400. && h<2400.);
    assert(Height(w,x,y)==h);
    assert(Encode(h)<=65535);
   }
  assert(Height(w,-10001,0)==-400.);
  assert(Height(w,10001,0)==-400.);
  assert(Height(w,0,-10001)==-400.);
  assert(Height(w,0,10001)==-400.);
 }
 // Independent heightfields, no accidental alias or overwrite.
 assert(std::abs(Height(EWorld::Kiryumori,2000,2500)-
    Height(EWorld::Aranyapura,2000,2500))>1.);
 assert(WidthMeters(EWorld::Nasdaras)==18000);
 assert(HeightMeters(EWorld::Nasdaras)==26000);
 assert(SideMeters(EWorld::Morodenachtmerr)==10000);
 assert(SideMeters(EWorld::ApocalypticOutbreak)==15000);
 std::cout<<"KIRYUMORI_ARANYAPURA_20KM_256_COMPONENTS_INDEPENDENT_HEIGHTFIELDS_VALID=1\n";
}