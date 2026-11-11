// Validate the graded 48km SKARVIK terrain without Epic/UE5 binaries.
// Ensure actual flat buildable lots and preserve main CitySample footprint.
#include "World/AnomaliaZPrigimaliaSkarvikGraded.h"
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <algorithm>
namespace Old=AnomaliaZPrigimaliaSkarvik;
namespace New=AnomaliaZPrigimaliaSkarvikGraded;
int main()
{
 if(New::Count!=124) throw std::runtime_error("Expected 124 new non-CitySample graded settlements");
 for(const auto& p : New::Pads){
  if(std::abs(p.East)>23500||std::abs(p.North)>23500) throw std::runtime_error("Graded site out of terrain");
  const double base=New::Height(p.East,p.North);
  for(const double east : {-60.,0.,60.})for(const double north : {-60.,0.,60.}){
   const double a=New::Height(p.East+east,p.North+north);
   if(std::abs(a-base)>0.0000001){
    std::cerr<<"NOT_FLAT centre="<<p.East<<","<<p.North<<" difference_m="<<a-base<<"\n";
    throw std::runtime_error("Construction nucleus is not truly level");
   }
  }
 }
 for(const double north : {-9950.,-8000.,-6000.})
  for(const double east : {0.,2000.,4000.}){
   if(std::abs(New::Height(east,north)-Old::Height(east,north))>1e-7)
    throw std::runtime_error("City Sample full-size urban pad changed");
  }
 for(const auto [east,north] : {std::pair{-23900.,-23900.},std::pair{23500.,-23000.},std::pair{23000.,22000.},std::pair{-24000.,23000.}}){
  if(std::abs(New::Height(east,north)-Old::Height(east,north))>1e-7)
   throw std::runtime_error("Terrain outside cities should not change");
 }
 std::cout<<"SKARVIK_GRADED_RELIEF_V2_TEST_SUCCESS=true\n";
 std::cout<<"SKARVIK_NATIVE_48KM_EXTENT_PRESERVED=true\n";
 std::cout<<"SKARVIK_CITYSAMPLE_ORIGINAL_PAD_PRESERVED=true\n";
 std::cout<<"SKARVIK_124_REAL_LEVEL_BUILDING_PADS_CONFIRMED=true\n";
}
