#include "unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaExtraWorldHeights.h"
#include <cassert>
#include <cmath>
#include <iostream>
using namespace AnomaliaZPrigimaliaExtraWorlds;
int main() {
  constexpr auto world=EWorld::ApocalypticOutbreak;
  assert(SideMeters(world)==15000);
  assert(Resolution(world)==1009);
  assert(((Resolution(world)-1)/126)*((Resolution(world)-1)/126)==64);
  const auto a=Height(world,0,0), b=Height(world,4200,-4800);
  const auto c=Height(world,-5200,4000),d=Height(world,-3550,-2550);
  for(const double x:{a,b,c,d}){ assert(std::isfinite(x)); assert(x>-300 && x<1800); }
  assert(std::abs(a-b)>10);
  assert(std::abs(a-c)>20);
  assert(Height(world,8000,0)==-400);
  assert(Height(world,0,8000)==-400);
  assert(Height(world,0,0)==a);
  assert(Encode(0)==32768);
  std::cout<<"APOCALYPTIC_OUTBREAK_NATIVE_HEIGHT_15KM_VALID=1; settlement assets and gameplay remain untested\n";
}