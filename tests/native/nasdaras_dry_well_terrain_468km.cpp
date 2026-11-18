#include "unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaExtraWorldHeights.h"
#include <cassert>
#include <cmath>
#include <iostream>
using namespace AnomaliaZPrigimaliaExtraWorlds;

int main() {
 const auto w=EWorld::Nasdaras;
 assert(WidthMeters(w)==18000 && HeightMeters(w)==26000);
 assert(SideMeters(w)==26000 && Resolution(w)==2017);
 assert(((Resolution(w)-1)/126)*((Resolution(w)-1)/126)==256);
 assert(Height(w,9001.,0.)==-400.);
 assert(Height(w,-9001.,0.)==-400.);
 assert(Height(w,0.,13001.)==-400.);
 assert(Height(w,0.,-13001.)==-400.);
 // A dry, original Sahelian terrain formula. Ten graded surface well sites,
 // not a water system nor proof of playable underground meshes.
 const double wells[10][2]={
   {-5100,8700},{1500,8400},{-5600,3300},{-700,3300},{4800,2900},
   {-5700,-2900},{-200,-2300},{4500,-3200},{-3800,-9000},{2800,-9200}};
 for(const auto& p:wells){
   const double z=Height(w,p[0],p[1]);
   assert(std::isfinite(z) && z>-150 && z<1700);
   assert(std::abs(z-NasdarasDryTerrainHeight(p[0],p[1]))<1e-8);
   const double dx=Height(w,p[0]+20,p[1])-z;
   assert(std::abs(dx)<18.0);
 }
 for(int y=-12000;y<=12000;y+=2000)
 for(int x=-8000;x<=8000;x+=2000){
   const double z=Height(w,x,y);
   assert(std::isfinite(z) && z>-500 && z<2000);
   assert(z==Height(w,x,y));
 }
 assert(WidthMeters(EWorld::Moscovie)==10000 && HeightMeters(EWorld::Moscovie)==10000);
 assert(WidthMeters(EWorld::Morodenachtmerr)==10000);
 std::cout << "NASDARAS_468KM2_18x26KM_DRY_TERRAIN_10_WELL_PADS_VALID=1\n";
}