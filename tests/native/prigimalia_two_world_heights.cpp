#include "World/AnomaliaZPrigimaliaExtraWorldHeights.h"
#include <cassert>
#include <cmath>
#include <iostream>

int main() {
 using namespace AnomaliaZPrigimaliaExtraWorlds;
 const EWorld worlds[]={EWorld::Solynacalyra,EWorld::Nexavarkhos};
 const int sides[]={15000,10000};
 const int resolution[]={1513,1009};
 for(int i=0;i<2;++i){
  assert(SideMeters(worlds[i])==sides[i]);
  assert(Resolution(worlds[i])==resolution[i]);
  assert((resolution[i]-1)%63==0);
  double minz=10000.,maxz=-10000.;
  int dry=0,wet=0;
  const int side=sides[i];
  for(int y=0;y<101;++y)for(int x=0;x<101;++x){
   const double east=-side/2.+side*x/100.;
   const double north=-side/2.+side*y/100.;
   const double z=Height(worlds[i],east,north);
   assert(std::isfinite(z));
   assert(z==Height(worlds[i],east,north));
   assert(Encode(z)<=65535);
   minz=std::min(minz,z);maxz=std::max(maxz,z);
   if(z>0.)++dry;else ++wet;
  }
  assert(dry>1000);
  assert(maxz-minz>65.);
  if(i==0)assert(wet>1000); // Paradise is an actual tropical island chain.
  assert(Height(worlds[i],side/2.+1,0)==-400.);
  std::cout<<"EXTRA_WORLD "<<i<<" side="<<side<<" samples="<<resolution[i]
           <<" drySampleCount="<<dry<<" seaSampleCount="<<wet
           <<" elevationMin="<<minz<<" elevationMax="<<maxz<<"\n";
 }
 assert(Height(worlds[0],0,0)!=Height(worlds[1],0,0));
 std::cout<<"TWO_NEW_WORLD_ORIGINAL_HEIGHTFIELDS_VERIFIED\n";
}
