// Sample the actual authored SKARVIK final seven-island C++ coast and terrain.
// The CSV is a read-only road-design GRID, not a playable UE5 Landscape.
#include "World/AnomaliaZPrigimaliaSkarvikFinalCoast.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <string>

namespace coast=AnomaliaZPrigimaliaSkarvikFinalCoast;
namespace archipelago=AnomaliaZPrigimaliaArchipelago;

int main(int argc,char** argv){
  if(argc!=2){std::cerr<<"usage: skarvik_survey_grid /tmp/skarvik-native-grid.csv\n";return 2;}
  const std::string path=argv[1];
  std::ofstream out(path,std::ios::binary);
  if(!out){std::cerr<<"Cannot create road-grid output file\n";return 3;}
  // A vertex is sampled every 200 m. 241x241 covers exactly -24 to +24 km.
  constexpr int cells=241,meters=200;
  constexpr double minimumDriveableCoastDistance=110.0;
  out<<"east_m,north_m,terrain_z_m,coast_distance_m,land_for_road,source_cxx\n";
  std::uint64_t land=0,coastal=0,wet=0;
  for(int j=0;j<cells;++j){
    const int north=-24000+j*meters;
    for(int i=0;i<cells;++i){
      const int east=-24000+i*meters;
      const double z=coast::Height(east,north);
      const double c=archipelago::CoastDistance(east,north);
      if(!std::isfinite(z)||!std::isfinite(c)||z<-500.||z>2200.){
        std::cerr<<"Invalid authored C++ height at "<<east<<","<<north<<"\n";return 4;
      }
      const bool dry=(z>5.&&c>minimumDriveableCoastDistance);
      land+=dry;
      coastal+=(z>5.&&!dry);
      wet+=(z<=5.);
      out<<east<<","<<north<<","<<z<<","<<c<<","<<(dry?1:0)
         <<",\"SKARVIK_FINAL_7_ISLANDS_CXX_V1\"\n";
    }
  }
  out.close();
  if(!out){std::cerr<<"Failed while writing terrain samples\n";return 5;}
  if(land<1000||wet<1000){std::cerr<<"Terrain mask implausible\n";return 6;}
  std::cout<<"SKARVIK_AUTHOR_CXX_GRID=241x241\n";
  std::cout<<"SKARVIK_GRID_SPACING_METRES=200\n";
  std::cout<<"SKARVIK_ROAD_DESIGN_LAND_CELLS="<<land<<"\n";
  std::cout<<"SKARVIK_ROAD_DESIGN_BEACH_CELLS="<<coastal<<"\n";
  std::cout<<"SKARVIK_ROAD_DESIGN_WATER_CELLS="<<wet<<"\n";
  std::cout<<"SKARVIK_SEVEN_ISLAND_NATIVE_UNREAL_LEVEL_MODIFIED=false\n";
  return 0;
}
