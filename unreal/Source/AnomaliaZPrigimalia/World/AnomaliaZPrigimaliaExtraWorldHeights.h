#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

// Distinct original procedural geography, entirely independent of existing maps.
// Coordinates and elevations are metres. Pure code; testable outside Unreal.
namespace AnomaliaZPrigimaliaExtraWorlds
{
enum class EWorld : std::uint8_t { Karskov, Vorgrad, Nemoris, Drakheim, Solynacalyra, Nexavarkhos, Invalid };

inline int SideMeters(EWorld world)
{
 return (world==EWorld::Karskov || world==EWorld::Vorgrad) ? 30000 :
        (world==EWorld::Nemoris || world==EWorld::Drakheim) ? 20000 : world==EWorld::Solynacalyra ? 15000 : world==EWorld::Nexavarkhos ? 10000 : 0;
}
inline int Resolution(EWorld world) { int side=SideMeters(world); return side==30000 ? 3025 : side==20000 ? 2017 : side==15000 ? 1513 : side==10000 ? 1009 : 0; }
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
  // LIVONIA-like original geography: continuous wooded country, rolling meadows,
  // rural farming valleys, a meandering river, dense southern ridges (no fjords).
  const double southernRidge=Gaussian(east,north,-3400.,-6300.,7800.,6100.)*
    (260.+360.*std::pow(1.-std::abs(ValueNoise(east,north,1450.,707)),2.));
  const double river=north-(1650.*std::sin(east/3200.)-1050.);
  const double riverValley=85.*std::exp(-(river*river)/(1350.*1350.));
  const double fields=35.*std::sin(east/3600.)*std::cos(north/4100.);
  return 120.+70.*n+southernRidge+fields-riverValley;
 }
 if(world==EWorld::Vorgrad){
  // NASDARA + TAKISTANPLUS style, entirely original: arid badlands, mountain
  // chains, desert plateaus, carved valleys and dry seasonal riverbeds.
  const double eastMountains=610.*Gaussian(east,north,10200.,4800.,5500.,10400.)*(.55+.45*std::abs(r));
  const double westPlateau=290.*Gaussian(east,north,-10200.,-6000.,5300.,6100.);
  const double canyon=north-(1800.*std::sin(east/2700.)+850.*std::sin(east/760.));
  const double wadi=135.*std::exp(-(canyon*canyon)/(1100.*1100.));
  return 185.+112.*n+48.*r+eastMountains+westPlateau-wadi;
 }
 if(world==EWorld::Nemoris){
  // LUX-style original TROPICAL jungle: flooded creeks, rainforest hills,
  // marsh pools, dark inland lakes and a high eroded northern escarpment.
  const double ridge=320.*Gaussian(east,north,-3600.,5500.,7300.,3800.)*(.65+.35*std::abs(r));
  const double marsh=48.*Gaussian(east,north,2000.,-3900.,5700.,4200.);
  const double lakes=52.*Gaussian(east,north,3800.,-2000.,1200.,1800.)+
                     48.*Gaussian(east,north,-2800.,-4700.,1500.,1150.);
  return 33.+48.*n+ridge-marsh-lakes;
 }

 if(world==EWorld::Solynacalyra){
  // Original fragmented tropical islands and lagoons (not another world's terrain).
  auto isle=[east,north](double cx,double cy,double rx,double ry,double phase){
   double dx=(east-cx)/rx,dy=(north-cy)/ry,angle=std::atan2(dy,dx);
   return (1.+.07*std::sin(6.*angle+phase)-std::hypot(dx,dy))*std::min(rx,ry);
  };
  double coast=std::max({isle(-1700.,1100.,4100.,3300.,.2),
    isle(3900.,1600.,1750.,1500.,1.4),isle(2500.,-3900.,2300.,1700.,2.1),
    isle(-4800.,-3900.,1300.,1100.,.7)});
  if(coast<0.)return -std::min(120.,12.+std::abs(coast)*.13);
  double peaks=290.*Gaussian(east,north,-1100.,1350.,2300.,1800.);
  return std::max(.4,20.+coast*.04+25.*n+peaks);
 }
 if(world==EWorld::Nexavarkhos){
  // Independent devastated colony: original impact valley, ridges and ash flats.
  double radius=std::hypot((east+650.)/1900.,(north-300.)/1800.);
  double ring=170.*std::exp(-std::pow((radius-1.1)/.3,2.));
  double crater=310.*Gaussian(east,north,-650.,300.,840.,790.);
  double ridge=480.*Gaussian(east,north,2300.,2100.,1350.,1700.);
  return 130.+75.*n+ring+ridge-crater;
 }
 // DRAKHEIM: NAMALSK + SAKHAL style frozen volcanic archipelago, basalt
 // cliffs, snowy valleys and two original calderas (not copied terrain).
 const double a=Gaussian(east,north,-1400.,1750.,3200.,3300.);
 const double b=Gaussian(east,north,5300.,-3800.,2150.,2700.);
 const double r1=std::hypot((east+1400.)/1800.,(north-1750.)/1900.);
 const double r2=std::hypot((east-5300.)/1300.,(north+3800.)/1500.);
 const double crater=680.*std::exp(-std::pow(r1/.50,4.))+
                     350.*std::exp(-std::pow(r2/.55,4.));
 const double shore=Smooth((10000.-std::max(std::abs(east),std::abs(north)))/2100.);
 return (165.+95.*n+45.*r+1020.*a+570.*b-crater)*shore-110.*(1.-shore);
}
inline std::uint16_t Encode(double height)
{
 // Exactly the existing UE5 landscape encoding (Z scale 800 cm).
 return std::uint16_t(std::lround(Clamp(32768.+height*16.,0.,65535.)));
}
}
