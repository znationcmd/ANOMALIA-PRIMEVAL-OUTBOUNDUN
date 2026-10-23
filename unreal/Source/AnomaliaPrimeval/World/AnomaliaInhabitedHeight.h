#pragma once
#include "AnomaliaArchipelagoHeight.h"
// Original town sites selected on ANOMALIA terrain, never imported from another game.
// Only used in the separate Inhabited_v1 world; the original archipelago stays intact.
namespace AnomaliaInhabited {
inline constexpr double Sites[][2]={
 {-3300,-17900},
 {6800,-20000},
 {9200,-19300},
 {-18600,-12700},
 {-13400,-9200},
 {-1200,-9900},
 {6800,-9200},
 {11300,-9200},
 {17200,-9200},
 {-10600,-6100},
 {-1200,-4000},
 {3300,-2600},
 {12000,-1900},
 {17900,-6100},
 {-17900,6800},
 {-14100,6800},
 {6800,1900},
 {14800,1900},
 {-18600,14800},
 {-12700,9900},
 {-6100,13400},
 {6100,9200},
 {14800,14100},
 {17200,13400},
 {-19300,17900},
 {-14100,17200},
 {6800,17900}
};
inline double Height(double East,double North){
 const double Base=AnomaliaArchipelago::Height(East,North);
 if(Base<=1)return Base; // Preserve the ocean and its original coastline.
 double Result=Base;
 for(const auto& Site:Sites){
  const double Distance=std::max(std::abs(East-Site[0]),std::abs(North-Site[1]));
  if(Distance>=580)continue;
  const double Weight=(1-AnomaliaArchipelago::Smooth((Distance-380)/200))*AnomaliaArchipelago::Smooth((Base-1)/5);
  const double Pad=AnomaliaArchipelago::Height(Site[0],Site[1]);
  Result=Base+(Pad-Base)*Weight;
 }
 return Result;
}
}
