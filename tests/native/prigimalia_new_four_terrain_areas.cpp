#include "World/AnomaliaZPrigimaliaNewFourWorldHeights.h"
#include <cassert>
#include <cmath>
#include <iostream>
#include <string>
using namespace AnomaliaZPrigimaliaNewFour;
struct Acc { double land=0,ice=0,main=0,island=0,water=0; };
Acc Measure(EWorld w) {
 const int N=350;const double side=SideMetres(w);const double area=side*side/1.e6;
 Acc a;
 for(int y=0;y<N;++y)for(int x=0;x<N;++x){
  const double e=side*((x+.5)/N-.5),n=side*((y+.5)/N-.5);
  const double h=Height(w,e,n);
  assert(std::isfinite(h)&&h>-300&&h<2000);
  const auto kind=Surface(w,e,n);
  if(kind==ESurface::DryLand){a.land+=1.;if(w==EWorld::Paradisiomania){if(ParadiseMainland(e,n))a.main+=1.;else a.island+=1.;}}
  else if(kind==ESurface::Ice)a.ice+=1.;
  else a.water+=1.;
 }
 for(double* p:{&a.land,&a.ice,&a.main,&a.island,&a.water})*p=*p*area/(N*N);
 return a;
}
int main(){
 const EWorld order[]={EWorld::RoskatviaB1,EWorld::Nogokv51,EWorld::Paradisiomania,EWorld::Deadroot};
 const int sides[]={12800,15300,10000,8000};const int components[]={100,144,64,64};
 for(int i=0;i<4;i++){
  assert(SideMetres(order[i])==sides[i]);
  assert(ExpectedComponents(order[i])==components[i]);
  auto a=Measure(order[i]);
  assert(std::abs(a.land+a.ice+a.water-sides[i]*sides[i]/1.e6)<0.01);
  std::cout<<i<<" "<<sides[i]<<" m land="<<a.land<<" ice="<<a.ice<<" water="<<a.water
           <<" main="<<a.main<<" islands="<<a.island<<"\n";
  if(i==1){assert(std::abs(a.land-83.)<3.5);assert(std::abs(a.ice-22.)<3.5);
    assert(std::abs((a.land+a.ice)-105.)<3.5);}
  if(i==2){assert(std::abs(a.main-60.)<3.);assert(std::abs(a.island-10.)<3.);
    assert(std::abs(a.water-30.)<3.);}
  if(i==0){assert(a.land>150.);}// predominantly land, forests and plains
  if(i==3){assert(a.land>63.5);}// deathmatch no ocean
 }
 std::cout<<"PRIGIMALIA_NEW_FOUR_TERRAINS_SOURCE_MATH_VALID=true\n";
}
