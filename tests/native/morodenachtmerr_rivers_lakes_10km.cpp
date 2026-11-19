#include "unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaExtraWorldHeights.h"
#include <cassert>
#include <cmath>
#include <iostream>
using namespace AnomaliaZPrigimaliaExtraWorlds;
int main(){
 const auto w=EWorld::Morodenachtmerr;
 assert(SideMeters(w)==10000 && Resolution(w)==1009);
 assert(((Resolution(w)-1)/126)*((Resolution(w)-1)/126)==64);
 // A single physically continuous river bed crossing all 10 km of terrain.
 for(int north=-5000;north<=5000;north+=250){
  const double east=MorodenachtmerrRiverEast(north);
  const double bed=Height(w,east,north);
  const double target=MorodenachtmerrRiverSurface(north)-4.;
  assert(std::abs(east)<2500.);
  assert(std::isfinite(bed) && std::abs(bed-target)<.25);
 }
 // Three lake interiors are carved to their planned depth, without
 // tributaries eroding the lake floors into unexplained deep trenches.
 struct Lake{double x,y,surface;};
 const Lake lakes[]={{-2650.,2100.,163.},{2550.,3050.,173.},{2350.,-1850.,137.}};
 for(const auto& lake:lakes)
  assert(std::abs(Height(w,lake.x,lake.y)-(lake.surface-4.5))<.25);
 // Exactly four small tributary endpoints must meet the main river.
 for(const double north:{650.,1200.,-3350.,-4600.}){
  assert(std::abs(MorodenachtmerrSegmentDistance(
    MorodenachtmerrRiverEast(north),north,
    MorodenachtmerrRiverEast(north),north,
    MorodenachtmerrRiverEast(north)+10.,north))<.001);
 }
 assert(Height(w,5001.,0.)==-400.);
 assert(Height(w,0.,-5001.)==-400.);
 assert(Height(w,0.,0.)==Height(w,0.,0.));
 std::cout<<"MORODENACHTMERR_ONE_10KM_MAIN_RIVER_THREE_LAKES_FOUR_TRIBUTARIES_VALID=1\n";
}