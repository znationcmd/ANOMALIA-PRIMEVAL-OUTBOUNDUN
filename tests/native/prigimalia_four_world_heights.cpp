#include "World/AnomaliaZPrigimaliaExtraWorldHeights.h"
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>

int main()
{
 using namespace AnomaliaZPrigimaliaExtraWorlds;
 constexpr std::array<EWorld,4> maps={EWorld::Karskov,EWorld::Vorgrad,EWorld::Nemoris,EWorld::Drakheim};
 assert(SideMeters(EWorld::Invalid)==0);
 assert(Resolution(EWorld::Invalid)==0);
 double centers[4]{};
 for(int i=0;i<4;++i)
 {
  auto map=maps[i];
  const int side=SideMeters(map),res=Resolution(map);
  assert(side==(i<2?30000:20000));
  assert(res==(i<2?3025:2017));
  const double step=double(side)/(res-1);
  assert(step>9. && step<11.);
  double minz=100000.,maxz=-100000.;
  int dry=0;
  for(int y=0;y<=40;++y)for(int x=0;x<=40;++x)
  {
   const double e=-side/2.+side*x/40.;
   const double n=-side/2.+side*y/40.;
   const double h=Height(map,e,n);
   assert(std::isfinite(h));
   assert(h==Height(map,e,n)); // deterministic, no hidden random state
   assert(Encode(h)<=65535);
   minz=std::min(minz,h);maxz=std::max(maxz,h);
   if(h>5.)++dry;
  }
  assert(minz>-500. && maxz<2000.);
  assert(maxz-minz>45.);
  assert(dry>350);
  assert(Height(map,side/2.+1.,0.)==-400.);
  centers[i]=Height(map,0.,0.);
  std::cout << "WORLD " << i << " " << side << "m resolution " << res
            << " height [" << minz << "," << maxz << "] drySamples=" << dry << "\n";
 }
 for(int i=0;i<4;++i)for(int j=i+1;j<4;++j)
  assert(std::abs(centers[i]-centers[j])>1.);
 std::cout << "FOUR_ORIGINAL_WORLDS_TERRAIN_MATH_PASSED\n";
 return 0;
}
