#include "unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaExtraWorldHeights.h"
#include <cassert>
using namespace AnomaliaZPrigimaliaExtraWorlds;
int main(){
 for(auto w:{EWorld::Yudinavia,EWorld::Moscovie,EWorld::Corsivia}){
  assert(Resolution(w)==1009);
  const int side=SideMeters(w);assert(side>0);
  for(int x=-side/2;x<=side/2;x+=137)for(int y=-side/2;y<=side/2;y+=149){
   double h=Height(w,x,y);assert(std::isfinite(h));assert(h>-2048 && h<2047);
   assert(std::abs((double(Encode(h))-32768.)/16.-h)<=.032);
  }
 }
 assert(SideMeters(EWorld::Yudinavia)==12500);
 assert(SideMeters(EWorld::Moscovie)==10000);
 assert(SideMeters(EWorld::Corsivia)==15000);
 for(int i=-7500;i<=7500;i+=50){
  assert(Height(EWorld::Corsivia,i,-7500)<0);assert(Height(EWorld::Corsivia,i,7500)<0);
  assert(Height(EWorld::Corsivia,-7500,i)<0);assert(Height(EWorld::Corsivia,7500,i)<0);
 }
 assert(SideMeters(EWorld::Invalid)==0);
}
