#include "World/AnomaliaZPrigimaliaExtraWorldHeights.h"
#include <cmath>
#include <iostream>
#include <iomanip>

int main() {
 using namespace AnomaliaZPrigimaliaExtraWorlds;
 const EWorld worlds[] = {EWorld::Karskov,EWorld::Vorgrad,EWorld::Nemoris,EWorld::Drakheim};
 const char* names[] = {"KARSKOV","VORGRAD","NEMORIS","DRAKHEIM"};
 constexpr double cell=50.;
 for(int i=0;i<4;++i) {
  const int side=SideMeters(worlds[i]);const int n=side/int(cell);
  unsigned long long dry=0,clear=0;
  for(int y=0;y<n;++y)for(int x=0;x<n;++x) {
   const double e=-side/2.+(x+.5)*cell,north=-side/2.+(y+.5)*cell;
   const double h=Height(worlds[i],e,north);
   if(h>0.)++dry;
   // Potential building parcel means land >5 metres and slope under 10 degrees
   // on a 20m cross. No legal/access/actor/mesh, navigation or PIE guarantee.
   if(h>5.){
    const double hx1=Height(worlds[i],e+10.,north),hx2=Height(worlds[i],e-10.,north);
    const double hy1=Height(worlds[i],e,north+10.),hy2=Height(worlds[i],e,north-10.);
    const double grade=std::hypot((hx1-hx2)/20.,(hy1-hy2)/20.);
    if(grade<=std::tan(10.*3.14159265358979323846/180.))++clear;
   }
  }
  std::cout<<std::fixed<<std::setprecision(2)
           <<"WORLD_AREA "<<names[i]<<" totalKm2="<<side*side/1000000.
           <<" emergentKm2Sampled="<<double(dry)*cell*cell/1000000.
           <<" potentialBuildableKm2Sampled="<<double(clear)*cell*cell/1000000.
           <<" sampleMeters="<<cell<<" groundedToNativeHeightFunction=true"
           <<" gamePlayabilityVerified=false\n";
 }
}
