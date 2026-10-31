#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
// Original procedural geography for four ADDITIONAL independent worlds.
// Metres, with zero as planned waterline. Non-UE pure C++ for deterministic CI.
// Water render, safe ice traversal, vegetation, roads and combat POIs need UE5 validation.
namespace AnomaliaZPrigimaliaNewFour
{
enum class EWorld : std::uint8_t { RoskatviaB1, Nogokv51, Paradisiomania, Deadroot, Invalid };
inline int SideMetres(EWorld v) {
 switch(v){case EWorld::RoskatviaB1:return 12800;case EWorld::Nogokv51:return 15300;
 case EWorld::Paradisiomania:return 10000;case EWorld::Deadroot:return 8000;
 default:return 0;}
}
inline int SamplesPerSide(EWorld v) {
 switch(v){case EWorld::RoskatviaB1:return 1261; // 10 x 126 quads = 100 components
 case EWorld::Nogokv51:return 1513; // 12 x 126 quads = 144 components
 case EWorld::Paradisiomania:return 1009; // 8 x 126 quads = 64 components
 case EWorld::Deadroot:return 1009;default:return 0;}
}
inline int ExpectedComponents(EWorld v) {const int n=SamplesPerSide(v);return n?((n-1)/126)*((n-1)/126):0;}
inline double Clamp(double a,double lo,double hi) {return std::max(lo,std::min(hi,a));}
inline double Smooth(double t){t=Clamp(t,0.,1.);return t*t*(3.-2.*t);}
inline double Gaussian(double x,double y,double cx,double cy,double sx,double sy) {
 const double a=(x-cx)/sx,b=(y-cy)/sy;return std::exp(-(a*a+b*b));
}
inline double Fractal(double x,double y) {
 return 0.52*std::sin(x/650.+std::cos(y/1400.))
       +0.26*std::cos(y/430.-x/1150.)
       +0.14*std::sin((x+y)/290.) +0.08*std::cos((x-y)/115.);
}
inline double NogokvScore(double x,double y) {
 const double base=std::max({
 1.10*Gaussian(x,y,-2850,1500,3450,3000),
 1.02*Gaussian(x,y,2300,-1800,2700,2400),
 .95*Gaussian(x,y,3800,3900,1500,1300),
 .87*Gaussian(x,y,-4600,-4000,1650,1300),
 .86*Gaussian(x,y,1000,4300,1350,1200)});
 return base + .07*std::sin(x/900.+std::cos(y/2000.))
             + .045*std::cos(y/1050.)+.025*std::sin((x+y)/290.);
}
inline double ParadiseMainScore(double x,double y) {
 return 1.-std::pow((x+300.)/4300.,2.)-std::pow((y-100.)/4400.,2.)
        +.06*std::sin(x/700.+y/1200.)+.04*std::cos(y/450.);
}
inline double ParadiseIslandsScore(double x,double y) {
 return std::max({1.-std::pow((x-4500.)/700.,2.)-std::pow((y-2700.)/1000.,2.),
 1.-std::pow((x+4250.)/750.,2.)-std::pow((y-3500.)/650.,2.),
 1.-std::pow((x-4300.)/1050.,2.)-std::pow((y+3800.)/730.,2.),
 1.-std::pow((x+3400.)/950.,2.)-std::pow((y+4200.)/590.,2.),
 1.-std::pow((x-3000.)/800.,2.)-std::pow((y-4450.)/700.,2.),
 1.-std::pow((x-4700.)/490.,2.)-std::pow((y+1000.)/650.,2.)});
}
// Area is sampled on terrain grid and checked by tests. "ice" is a candidate
// terrain heightfield; actual traction, collision, water volumes and weather must be tested.
enum class ESurface : std::uint8_t { DryLand, Ice, OpenWater };
inline ESurface Surface(EWorld v,double x,double y) {
 if(v==EWorld::Nogokv51){
  const double score=NogokvScore(x,y);
  if(score>=.309812376)return ESurface::DryLand; // calibrated ~83/234.09 km²
  if(score>=.209422890)return ESurface::Ice; // ~22 additional km²
  return ESurface::OpenWater;
 }
 if(v==EWorld::Paradisiomania) {
  if(ParadiseMainScore(x,y)>=-.026686431 || ParadiseIslandsScore(x,y)>0.)
   return ESurface::DryLand;
  return ESurface::OpenWater;
 }
 if(v==EWorld::RoskatviaB1 || v==EWorld::Deadroot)return ESurface::DryLand;
 return ESurface::OpenWater;
}
inline bool ParadiseMainland(double x,double y) {
 return ParadiseMainScore(x,y)>=-.026686431;
}
inline double Height(EWorld v,double x,double y){
 const int side=SideMetres(v);
 if(!side||!std::isfinite(x)||!std::isfinite(y)||std::abs(x)>side/2.||std::abs(y)>side/2.)return -300.;
 const double n=Fractal(x,y);
 if(v==EWorld::RoskatviaB1) {
  // Temperate woodland, open plains and a broad network of lakes/river valleys.
  const double river1=y- (450.*std::sin(x/1250.)+310.*std::sin(x/360.));
  const double river2=x- (2600.+520.*std::sin(y/1600.));
  const double lake=27.*Gaussian(x,y,-2800,2900,1100,1050)
                   +26.*Gaussian(x,y,3500,-2700,920,1150);
  const double bank=52.*std::exp(-(river1*river1)/(300.*300.))
                   +31.*std::exp(-(river2*river2)/(230.*230.));
  return 65.+27.*n+12.*std::sin(x/2450.)*std::cos(y/3100.)-lake-bank;
 }
 if(v==EWorld::Nogokv51){
  const double score=NogokvScore(x,y);
  if(score>=.309812376)return 5.+240.*(score-.309812376)+11.*n;
  if(score>=.209422890)return 1.4+.7*std::sin(x/550.)*std::cos(y/700.); // candidate frozen sea shelf
  return -28.+75.*(score-.209422890);
 }
 if(v==EWorld::Paradisiomania){
  if(ParadiseMainland(x,y))
   return 9.+160.*(ParadiseMainScore(x,y)+.026686431)+11.*n;
  if(ParadiseIslandsScore(x,y)>0.)
   return 5.+55.*ParadiseIslandsScore(x,y)+5.*n;
  return -24.+7.*n;
 }
 // DEADROOT: 8x8 km competitive deathmatch arena, low relief plus rocky cover.
 const double central=35.*Gaussian(x,y,0.,0.,1750.,1350.);
 const double west=66.*Gaussian(x,y,-2750,1200,850.,1850.);
 const double east=54.*Gaussian(x,y,2200,-1700,1400.,920.);
 return 70.+22.*n+central+west+east;
}
inline std::uint16_t Encode(double metres) {
 const double s=Clamp((metres/800.+1.)*32768.,0.,65535.);
 return static_cast<std::uint16_t>(std::round(s));
}
} // namespace
