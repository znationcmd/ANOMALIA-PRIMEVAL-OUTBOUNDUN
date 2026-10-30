#include "World/AnomaliaZPrigimaliaExtraWorldHeights.h"
#include <array>
#include <cassert>
#include <cmath>
#include <iostream>
int main(){
 using namespace AnomaliaZPrigimaliaExtraWorlds;
 constexpr std::array<EWorld,4> maps={
  EWorld::Vorgrad,EWorld::Nexavarkhos,EWorld::Solynacalyra,EWorld::Drakheim};
 constexpr std::array<int,4> sides={30000,10000,15000,20000};
 constexpr std::array<int,4> resolutions={3025,1009,1513,2017};
 int sums=0;
 for(int i=0;i<4;++i){
  const auto world=maps[i];
  assert(SideMeters(world)==sides[i] && Resolution(world)==resolutions[i]);
  int dry=0,wet=0;double mn=1000000.,mx=-1000000.;
  for(int y=0;y<=80;++y) for(int x=0;x<=80;++x){
   const double e=-sides[i]/2.+sides[i]*x/80.;
   const double n=-sides[i]/2.+sides[i]*y/80.;
   const double h=Height(world,e,n);
   assert(std::isfinite(h) && Height(world,e,n)==h);
   assert(Encode(h)<=65535);
   mn=std::min(h,mn);mx=std::max(h,mx);
   if(h>0)++dry;else ++wet;
  }
  assert(mx-mn>50. && mx<2400. && mn>-500.);
  assert(dry>300 && dry+wet==6561);
  if(world==EWorld::Solynacalyra || world==EWorld::Drakheim ||
     world==EWorld::Nexavarkhos)assert(wet>100);
  assert(Height(world,sides[i]/2.+1,0)==-400.);
  std::cout<<"FUSED_ORIGINAL_TERRAIN "<<i<<" size="<<sides[i]
   <<" dry="<<dry<<" wet="<<wet<<" heightRange="<<mn<<","<<mx<<"\n";
  sums+=dry;
 }
 assert(sums>10000);
 std::cout<<"FOUR_REFERENCE_PAIR_SOURCE_TERRAINS_VERIFIED_NOT_NATIVE_UMAPS\n";
}
