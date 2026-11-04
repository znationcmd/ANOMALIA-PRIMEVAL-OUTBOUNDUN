// Export the exactly matching 48x48km landscape samples used by UE5's
// CreateSkarvikCityLandscape() on a GitHub-hosted runner. No Epic assets used.
#include "World/AnomaliaZPrigimaliaSkarvikTerrain.h"
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
namespace Sk=AnomaliaZPrigimaliaSkarvik;
int main(int argc,char** argv)
{
 if(argc!=2){std::cerr<<"Usage: skarvik-export out.r16\n";return 2;}
 constexpr int N=3025;
 constexpr double side=48000.,half=24000.;
 std::ofstream f(argv[1],std::ios::binary|std::ios::trunc);
 if(!f)throw std::runtime_error("Unable to open R16 output");
 for(int y=0;y<N;++y)
 {
  const double north=half-side*double(y)/(N-1);
  for(int x=0;x<N;++x)
  {
   const double east=-half+side*double(x)/(N-1);
   const std::uint16_t h=Sk::Encode(Sk::Height(east,north));
   const char b[2]={static_cast<char>(h&0xff),static_cast<char>((h>>8)&0xff)};
   f.write(b,2);
  }
  if(!f)throw std::runtime_error("R16 output failed during row write");
 }
 f.close();
 if(!f)throw std::runtime_error("R16 output not saved completely");
 std::cout<<"SKARVIK_48X48_REAL_R16_EXPORTED samples="<<N*N
          <<" bytes="<<(2LL*N*N)<<" format=little-endian-u16\n";
}
