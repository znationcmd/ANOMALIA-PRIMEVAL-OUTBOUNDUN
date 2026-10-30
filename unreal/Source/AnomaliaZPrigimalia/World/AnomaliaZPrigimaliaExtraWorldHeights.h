#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

// Distinct original procedural geography, entirely independent of existing maps.
// Coordinates and elevations are metres. Pure code; testable outside Unreal.
namespace AnomaliaZPrigimaliaExtraWorlds
{
enum class EWorld : std::uint8_t { Karskov, Vorgrad, Nemoris, Drakheim, Invalid };

inline int SideMeters(EWorld world)
{
 return (world==EWorld::Karskov || world==EWorld::Vorgrad) ? 30000 :
        (world==EWorld::Nemoris || world==EWorld::Drakheim) ? 20000 : 0;
}
inline int Resolution(EWorld world) { return SideMeters(world)==30000 ? 3025 : SideMeters(world)==20000 ? 2017 : 0; }
inline double Clamp(double n,double lo,double hi) { return std::max(lo,std::min(hi,n)); }
inline double Smooth(double v) { v=Clamp(v,0.,1.); return v*v*(3.-2.*v); }
inline double Hash(int x,int y,int seed)
{
 std::uint32_t h=std::uint32_t(x)*374761393u+std::uint32_t(y)*668265263u+std::uint32_t(seed)*1274126177u;
 h=(h^(h>>13))*1274126177u;
 return double(h^(h>>16))/4294967295.*2.-1.;
}
inline double ValueNoise(double x,double y,double spacing,int seed)
{
 x/=spacing; y/=spacing;
 const int ix=int(std::floor(x)),iy=int(std::floor(y));
 const double tx=Smooth(x-ix),ty=Smooth(y-iy);
 const double a=Hash(ix,iy,seed)*(1.-tx)+Hash(ix+1,iy,seed)*tx;
 const double b=Hash(ix,iy+1,seed)*(1.-tx)+Hash(ix+1,iy+1,seed)*tx;
 return a*(1.-ty)+b*ty;
}
inline double Fractal(double x,double y,int seed)
{
 return .59*ValueNoise(x,y,2600.,seed)+.28*ValueNoise(x,y,860.,seed+19)+
        .13*ValueNoise(x,y,265.,seed+53);
}
inline double Gaussian(double x,double y,double cx,double cy,double rx,double ry)
{
 const double dx=(x-cx)/rx,dy=(y-cy)/ry;
 return std::exp(-(dx*dx+dy*dy));
}
inline double Height(EWorld world,double east,double north)
{
 const int side=SideMeters(world);
 if(side==0 || !std::isfinite(east) || !std::isfinite(north) ||
    std::abs(east)>side/2. || std::abs(north)>side/2.)return -400.;
 const double n=Fractal(east,north,100+int(world)*97);
 const double r=Fractal(east+2311.,north-1427.,510+int(world)*71);
 if(world==EWorld::Karskov){
  // Cold fjords, narrow bays, wooded uplands and a snowy central massif.
  const double fjord=Gaussian(east,north,3800.,-1200.,900.,12500.)*155.;
  const double massif=Gaussian(east,north,-2800.,3300.,6900.,6700.)*
    (420.+510.*std::pow(1.-std::abs(ValueNoise(east,north,1500.,707)),2.));
  const double coast=Smooth((15000.-std::max(std::abs(east),std::abs(north)))/1600.);
  return (45.+125.*n+massif-fjord)*coast-35.*(1.-coast);
 }
 if(world==EWorld::Vorgrad){
  // Broad continental country: rolling farmland, a river corridor and eastern ridges.
  const double hills=260.*Gaussian(east,north,10500.,5500.,5400.,11000.)*(.6+.4*std::abs(r));
  const double river=north-(1300.*std::sin(east/3000.)+800.*std::sin(east/1200.));
  const double cut=80.*std::exp(-(river*river)/(850.*850.));
  return 85.+58.*n+38.*r+hills-cut;
 }
 if(world==EWorld::Nemoris){
  // Humid rainforest, marsh pools, dark lakes and an eroded northern escarpment.
  const double ridge=320.*Gaussian(east,north,-3600.,5500.,7300.,3800.)*(.65+.35*std::abs(r));
  const double marsh=48.*Gaussian(east,north,2000.,-3900.,5700.,4200.);
  const double lakes=52.*Gaussian(east,north,3800.,-2000.,1200.,1800.)+
                     48.*Gaussian(east,north,-2800.,-4700.,1500.,1150.);
  return 33.+48.*n+ridge-marsh-lakes;
 }
 // DRAKHEIM: ash valleys, eroded basalt ridges and two volcanic calderas.
 const double a=Gaussian(east,north,-1400.,1750.,3200.,3300.);
 const double b=Gaussian(east,north,5300.,-3800.,2150.,2700.);
 const double r1=std::hypot((east+1400.)/1800.,(north-1750.)/1900.);
 const double r2=std::hypot((east-5300.)/1300.,(north+3800.)/1500.);
 const double crater=680.*std::exp(-std::pow(r1/.50,4.))+
                     350.*std::exp(-std::pow(r2/.55,4.));
 return 165.+95.*n+45.*r+1020.*a+570.*b-crater;
}
inline std::uint16_t Encode(double height)
{
 // Exactly the existing UE5 landscape encoding (Z scale 800 cm).
 return std::uint16_t(std::lround(Clamp(32768.+height*16.,0.,65535.)));
}
}
