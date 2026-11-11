#include "World/AnomaliaArchipelagoHeight.h"
#include <fstream>
#include <iostream>
#include <cassert>
int main(int argc,char** argv){
 double area=0,peak=-1000,minimum=1000;
 for(int y=0;y<1920;++y)for(int x=0;x<1920;++x){
  double h=AnomaliaArchipelago::Height(-23987.5+25*x,23987.5-25*y);
  assert(std::isfinite(h));if(h>0)area+=.000625;
  peak=std::max(peak,h);minimum=std::min(minimum,h);
  const double decoded=(int(AnomaliaArchipelago::Encode(h))-32768)/16.;
  assert(std::abs(decoded-h)<=.031251);
 }
 assert(area>300 && area<1500);assert(peak>1200 && peak<2000);assert(minimum<-300);
 for(int i=-24;i<=24;++i){assert(AnomaliaArchipelago::Height(i*1000.,24000)<0);assert(AnomaliaArchipelago::Height(i*1000.,-24000)<0);}
 std::cout<<"dryLandKm2="<<area<<" peakMeters="<<peak<<" minMeters="<<minimum<<"\n";
 if(argc>1){std::ofstream f(argv[1],std::ios::binary);for(int y=0;y<3025;++y)for(int x=0;x<3025;++x){auto v=AnomaliaArchipelago::Encode(AnomaliaArchipelago::Height(-24000.+48000.*x/3024,24000.-48000.*y/3024));char b[2]={static_cast<char>(v&255),static_cast<char>(v>>8)};f.write(b,2);}}
}
