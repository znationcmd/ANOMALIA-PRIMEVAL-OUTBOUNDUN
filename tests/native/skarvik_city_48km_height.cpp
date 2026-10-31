// Source-only terrain invariants: independent of Unreal, does NOT launch Editor.
#include "World/AnomaliaZPrigimaliaSkarvikTerrain.h"
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
namespace Sk=AnomaliaZPrigimaliaSkarvik;
int main()
{
 constexpr double eps=0.00001;
 assert(std::abs(Sk::Height(2000.,-8000.)-100.)<eps);     // Full City Sample pad
 assert(std::abs(Sk::Height(14000.,15000.)-540.)<eps);   // Snow metropolis
 assert(std::abs(Sk::Height(13000.,1000.)-130.)<eps);    // Temperate city
 assert(std::abs(Sk::Height(-17000.,-13000.)-250.)<eps); // Desert village
 assert(std::abs(Sk::Height(-14000.,17000.)-1120.)<eps); // Snowy mountain village
 assert(std::abs(Sk::Height(7000.,19000.)-710.)<eps);   // Snow village
 assert(Sk::Encode(100.)==std::uint16_t(34368));
 assert(Sk::UnpaddedHeight(-17500.,10000.)>Sk::UnpaddedHeight(0.,-8000.)); // Alps rise
 double minH=100000.,maxH=-100000.;
 for(int y=-24000;y<=24000;y+=600)
  for(int x=-24000;x<=24000;x+=600)
  {
   const double h=Sk::Height(x,y);
   assert(std::isfinite(h)&&h>=-50.&&h<=1850.);
   const double q=double(Sk::Encode(h)-32768)/16.;
   assert(std::abs(q-h)<=.03126);
   minH=std::min(minH,h);maxH=std::max(maxH,h);
  }
 assert(maxH>1000.); // Real mountain altitudes
 assert(minH<20.);   // Low peripheral coast
 std::cout << "SKARVIK_48KM_TERRAIN_SOURCE_OK min=" << minH<<" max="<<maxH<<"\n";
}
