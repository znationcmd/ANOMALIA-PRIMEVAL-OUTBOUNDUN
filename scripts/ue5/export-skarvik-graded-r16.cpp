// Standalone exact UE5 48x48km graded terrain export, NO proprietary assets.
// 3025x3025 signed landscape elevations encoded as little-endian unsigned R16.
#include "World/AnomaliaZPrigimaliaSkarvikGraded.h"
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
namespace Terrain=AnomaliaZPrigimaliaSkarvikGraded;
int main(int argc,char**argv)
{
 if(argc!=2) {std::cerr<<"Usage: skarvik-graded-export out.r16\n";return 2;}
 if(Terrain::Count!=124) throw std::runtime_error("Expected 124 graded urban sites");
 constexpr int Size=3025;
 constexpr double Half=24000.0,Side=48000.0;
 std::ofstream file(argv[1],std::ios::binary|std::ios::trunc);
 if(!file)throw std::runtime_error("R16 output could not be opened");
 for(int y=0;y<Size;++y){
  const double north=Half-Side*double(y)/double(Size-1);
  for(int x=0;x<Size;++x){
   const double east=-Half+Side*double(x)/double(Size-1);
   const std::uint16_t value=Terrain::Encode(Terrain::Height(east,north));
   const char bytes[2]={static_cast<char>(value&0xff),static_cast<char>((value>>8)&0xff)};
   file.write(bytes,2);
  }
  if(!file)throw std::runtime_error("R16 could not write complete row");
 }
 file.close();
 if(!file)throw std::runtime_error("R16 close failed");
 std::cout<<"SKARVIK_GRADED_48KM_R16_EXPORT_OK=true\n"
          <<"SKARVIK_GRADED_TOTAL_PIXELS="<<Size*Size<<"\n"
          <<"SKARVIK_GRADED_BYTE_COUNT="<<2LL*Size*Size<<"\n";
}
