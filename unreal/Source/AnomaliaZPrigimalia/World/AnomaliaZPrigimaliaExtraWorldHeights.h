#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

// Distinct original procedural geography, entirely independent of existing maps.
// Coordinates and elevations are metres. Pure code; testable outside Unreal.
namespace AnomaliaZPrigimaliaExtraWorlds
{
enum class EWorld : std::uint8_t { Karskov, Vorgrad, Nemoris, Drakheim, Yudinavia, Moscovie, Corsivia, BotSever, CleosphinilX, Aethorion, Salveria, Warrakull, Dijkenhaven, Laguneria, Kuntaray, Velunda, Karverra, Noktera, LastCountyCanyon, Znieczulenie, Invalid };

inline int SideMeters(EWorld world)
{
 return (world==EWorld::Karskov || world==EWorld::Vorgrad) ? 30000 :
        (world==EWorld::Nemoris || world==EWorld::Drakheim) ? 20000 :
        world==EWorld::Yudinavia ? 12500 : world==EWorld::Moscovie ? 10000 :
        world==EWorld::Corsivia ? 15000 : world==EWorld::BotSever ? 50000 :
        world==EWorld::CleosphinilX ? 14000 :
        world==EWorld::Aethorion ? 12000 :
        world==EWorld::Salveria ? 18000 :
        world==EWorld::Warrakull ? 24000 :
        world==EWorld::Dijkenhaven ? 16000 :
        world==EWorld::Laguneria ? 10000 :
        world==EWorld::Kuntaray ? 18000 : world==EWorld::Velunda ? 16000 :
        world==EWorld::Karverra ? 20000 : world==EWorld::Noktera ? 10000 : (world==EWorld::LastCountyCanyon || world==EWorld::Znieczulenie) ? 18000 : 0;
}
inline int NorthSouthMeters(EWorld world)
{
 if(world==EWorld::Salveria)return 16000;
 if(world==EWorld::Warrakull)return 20000;
 if(world==EWorld::Dijkenhaven)return 14000;
 if(world==EWorld::Kuntaray)return 14000;
 if(world==EWorld::Karverra)return 16000;
 if(world==EWorld::Noktera)return 9400;
 if(world==EWorld::LastCountyCanyon)return 14000;
 if(world==EWorld::Znieczulenie)return 16000;
 return SideMeters(world);
}
inline int Resolution(EWorld world) { if(world>=EWorld::Aethorion && world<=EWorld::Znieczulenie)return 2017; const int side=SideMeters(world); return side==30000 ? 3025 : (side==14000 || side==20000 || side==50000) ? 2017 : side>0 ? 1009 : 0; }
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
    std::abs(east)>side/2. || std::abs(north)>NorthSouthMeters(world)/2.)return -400.;
 const double n=Fractal(east,north,100+int(world)*97);
 const double r=Fractal(east+2311.,north-1427.,510+int(world)*71);
 if(world==EWorld::Znieczulenie){
  const double river=std::abs(east-950.*std::sin(north/2050.));
  const double foothills=Smooth((river-400.)/2650.);
  const double ridge=195.*Gaussian(east,north,4900.,-3000.,2300.,4100.);
  return 24.+18.*Smooth((river-80.)/260.)+foothills*(65.+54.*n+ridge);
 }
 if(world==EWorld::LastCountyCanyon){
  const double creek=std::abs(north-1050.*std::sin(east/1900.)-400.*std::sin(east/640.));
  const double rim=145.*Smooth((creek-135.)/920.);
  const double mesas=120.*Smooth((r-.08)/.48)*Smooth((creek-740.)/1400.);
  return 32.+17.*n+rim+mesas;
 }
 if(world==EWorld::Velunda){
  const double trunk=east-720.*std::sin(north/1350.);
  const double branch=std::abs(trunk)-Smooth((north+2000.)/6600.)*3100.;
  const double channel=std::min(std::abs(trunk),std::abs(branch));
  return -4.+(12.+4.*n)*Smooth((channel-95.)/410.);
 }
 if(world==EWorld::Karverra){
  const double gorge=std::abs(north-1450.*std::sin(east/2150.));
  const double terraces=80.*Smooth((gorge-180.)/520.)+
                        185.*Smooth((gorge-1400.-780.*r)/630.);
  return 42.+terraces+20.*n;
 }
 if(world==EWorld::Noktera){
  // Surface above the planned underground levels.
  return 70.+26.*n+34.*Gaussian(east,north,1800.,-1000.,2100.,2800.);
 }
 if(world==EWorld::Aethorion){
  const double pillars=std::pow(Smooth((ValueNoise(east,north,880.,874)-.22)/.52),2.);
  return 48.+26.*n+310.*pillars*Gaussian(east,north,300.,350.,3300.,4500.);
 }
 if(world==EWorld::Salveria){
  const double bowl=std::hypot(east/7400.,north/6250.);
  const double rim=Smooth((bowl-.72)/.48);
  const double islands=32.*Gaussian(east,north,-1500.,1000.,750.,410.)+
                       40.*Gaussian(east,north,2750.,-1250.,480.,900.);
  return 10.+.4*n+rim*(65.+30.*n)+islands;
 }
 if(world==EWorld::Warrakull){
  const double escarpment=185.*Smooth((east-4600.+1000.*r)/3900.);
  const double basin=48.*Gaussian(east,north,-3300.,-1000.,4900.,6300.);
  return 94.+55.*n+escarpment-basin;
 }
 if(world==EWorld::Dijkenhaven){
  const double channel=std::abs(east-(1800.+370.*std::sin(north/1400.)));
  const double dike=6.*std::exp(-std::pow((channel-310.)/85.,2.));
  return -3.+(5.5+1.3*n)*Smooth((channel-100.)/170.)+dike;
 }
 if(world==EWorld::Laguneria){
  const double islands=std::max({
   Gaussian(east,north,-1700.,850.,1550.,1050.),
   Gaussian(east,north,600.,1900.,830.,1250.),
   Gaussian(east,north,2300.,-900.,1100.,1550.)
  });
  const double canal=std::abs(north-(820.+380.*std::sin(east/1300.)));
  return -5.+18.*Smooth((islands-.25)/.49)*Smooth((canal-36.)/100.);
 }
 if(world==EWorld::Kuntaray){
  const double valley=std::abs(east-950.*std::sin(north/1550.));
  const double rise=Smooth((valley-120.)/3400.);
  return 49.+rise*(570.+220.*n)+35.*r;
 }
 if(world==EWorld::CleosphinilX){
  // Water occupies the terrain below zero metres. The Nil flows north–south
  // and opens into an eastern basin containing three separate islands.
  const double riverCenter=620.*std::sin(north/1750.)+220.*std::sin(north/730.);
  const double riverDistance=std::abs(east-riverCenter);
  const double riverHalfWidth=210.+55.*std::cos(north/1120.);
  const double riverShore=riverDistance-riverHalfWidth;
  const double basinRadius=std::hypot((east-2450.)/3695.,(north-250.)/5100.);
  const double basinShore=(basinRadius-1.)*3695.;
  const double islandShore=std::min({
    std::hypot(east-2450.,north-1950.)-620.,
    std::hypot(east-1100.,north+1000.)-570.,
    std::hypot(east-3900.,north+1000.)-690.
  });
  const double oasisShore=std::min({
    std::hypot(east+3700.,north+2100.)-240.,
    std::hypot(east+4600.,north-2600.)-190.,
    std::hypot(east+2100.,north-4100.)-155.
  });
  const double shore=std::min({riverShore,std::max(basinShore,-islandShore),oasisShore});
  if(shore<=0.)return std::max(-26.,shore*.045);
  const double dunePhase=(east+0.36*north)/185.+1.5*r;
  const double dunes=48.*std::pow(0.5+0.5*std::sin(dunePhase),2.)*
    Smooth((-east-900.)/2400.);
  const double plateau=165.*Smooth((east-1850.+420.*r)/1150.)*
    (0.78+0.22*std::sin(north/1350.));
  const double dryRelief=30.+18.*n+dunes+plateau;
  return 22.*Smooth(shore/250.)+dryRelief*Smooth(shore/1000.);
 }
 // Original draft landforms, not surveyed Moscow/Corsica/Scandinavia data.
 if(world==EWorld::BotSever){
  // Original continental draft; southern naming boundary is exactly -17500 m.
  const double river=north-(2400.*std::sin(east/4500.)-1200.);
  const double valley=95.*std::exp(-river*river/(1500.*1500.));
  const double southern=Smooth((-north-14000.)/7000.);
  return 130.+85.*n-valley+southern*(350.+450.*std::abs(r));
 }
 if(world==EWorld::Yudinavia){
  const double ridge=620.*Gaussian(east,north,1300.,1100.,3200.,4900.);
  const double coast=Smooth((east+5600.+500.*std::sin(north/900.))/1700.);
  const double fjord=310.*Gaussian(east,north,-1800.,900.,2900.,350.)+
                     240.*Gaussian(east,north,-2800.,-1800.,2500.,420.);
  return (100.+ridge+95.*n-fjord)*coast-95.*(1.-coast);
 }
 if(world==EWorld::Moscovie){
  const double river=north-(630.*std::sin(east/1400.)+270.*std::sin(east/570.));
  const double bank=Smooth((std::abs(river)-70.)/170.);
  return -6.+bank*(24.+12.*n+5.*r);
 }
 if(world==EWorld::Corsivia){
  // All four edges are below sea level; no artificial rectangular island cliff.
  const double island=Smooth((1.-std::hypot((east+450.*std::sin(north/1700.))/4700.,north/6500.))/.24);
  const double spine=1120.*Gaussian(east,north,-600.,900.,1800.,4100.)*(.78+.22*r);
  const double river=north-(1100.+450.*std::sin(east/1100.));
  const double valley=150.*std::exp(-river*river/(300.*300.));
  return island*std::max(15.,70.+spine+85.*n-valley)-110.*(1.-island);
 }
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
