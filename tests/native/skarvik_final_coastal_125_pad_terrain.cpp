#include "World/AnomaliaZPrigimaliaSkarvikFinalCoast.h"
#include <algorithm>
#include <cmath>
#include <iostream>
#include <limits>
using namespace AnomaliaZPrigimaliaArchipelago;
using AnomaliaZPrigimaliaSkarvikFinalCoast::Pads;
using AnomaliaZPrigimaliaSkarvikFinalCoast::Count;
int main() {
 if(Count!=125){std::cerr<<"Expected 125 pad centres, got "<<Count<<"\n";return 2;}
 int wet=0;double maxgrade=0,minCoast=1e9,minHeight=1e9;
 for(const auto& p:Pads){
  const double c=CoastDistance(p.East,p.North);
  minCoast=std::min(minCoast,c);
  if(c<105.){++wet;continue;}
  const double z=AnomaliaZPrigimaliaSkarvikFinalCoast::Height(p.East,p.North);
  minHeight=std::min(z,minHeight);
  double minZ=z,maxZ=z;
  for(double e:{-40.,0.,40.})for(double n:{-40.,0.,40.}){
   const double h=AnomaliaZPrigimaliaSkarvikFinalCoast::Height(p.East+e,p.North+n);
   if(!std::isfinite(h)){std::cerr<<"nonfinite native coastal height\n";return 3;}
   minZ=std::min(minZ,h);maxZ=std::max(maxZ,h);
  }
  if(maxZ-minZ>.25)std::cerr<<"SKARVIK_SITE_TERRACE_GRADE_EAST_NORTH_METRES="<<p.East<<","<<p.North<<","<<(maxZ-minZ)<<",coast="<<c<<"\n";
  maxgrade=std::max(maxgrade,maxZ-minZ);
 }
 if(wet){std::cerr<<"Cannot safely site "<<wet<<" final towns in coastal sea\n";return 4;}
 // Original ocean depths must not be raised by false 125-city mainland terraces.
 for(int e=-23500;e<23500;e+=350)for(int n=-23500;n<23500;n+=350){
  if(CoastDistance(e,n)>100.)continue;
  if(std::abs(AnomaliaZPrigimaliaSkarvikFinalCoast::Height(e,n)-AnomaliaZPrigimaliaArchipelago::Height(e,n))>1.e-8){
   std::cerr<<"Ocean or beach height changed at "<<e<<","<<n<<"\n";return 5;
  }
 }
 if(maxgrade>2.0){std::cerr<<"At least one city terrace grade too steep "<<maxgrade<<"m\n";return 6;}
 std::cout<<"SKARVIK_FINAL_COAST_SOURCE_PAD_COUNT=125\n";
 std::cout<<"SKARVIK_FINAL_COAST_NATIVE_SEVEN_ISLAND_TOPOLOGY_PRESERVED=true\n";
 std::cout<<"SKARVIK_FINAL_COAST_SOURCE_125_TERRACE_MAX_GRADE_METRES="<<maxgrade<<"\n";
 std::cout<<"SKARVIK_FINAL_COAST_ORIGINAL_UNDERWATER_SHORE_PRESERVED=true\n";
 std::cout<<"SKARVIK_FINAL_COAST_NATIVE_WORLD_SAVED=false\n";
 return 0;
}
