#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

// Distinct original procedural geography, entirely independent of existing maps.
// Coordinates and elevations are metres. Pure code; testable outside Unreal.
namespace AnomaliaZPrigimaliaExtraWorlds
{
enum class EWorld : std::uint8_t { Karskov, Vorgrad, Nemoris, Drakheim, Yudinavia, Moscovie, Corsivia, BotSever, ApocalypticOutbreak, Morodenachtmerr, Nasdaras, Invalid };

inline int SideMeters(EWorld world)
{
 return (world==EWorld::Karskov || world==EWorld::Vorgrad) ? 30000 :
        (world==EWorld::Nemoris || world==EWorld::Drakheim) ? 20000 :
        world==EWorld::Yudinavia ? 12500 : world==EWorld::Moscovie ? 10000 :
        world==EWorld::Corsivia ? 15000 : world==EWorld::BotSever ? 50000 :
        world==EWorld::ApocalypticOutbreak ? 15000 : world==EWorld::Morodenachtmerr ? 10000 :
        world==EWorld::Nasdaras ? 26000 : 0;
}
inline int WidthMeters(EWorld world) { return world==EWorld::Nasdaras ? 18000 : SideMeters(world); }
inline int HeightMeters(EWorld world) { return world==EWorld::Nasdaras ? 26000 : SideMeters(world); }
inline int Resolution(EWorld world) { const int side=SideMeters(world); return side==30000 ? 3025 : (side==20000 || side==50000 || world==EWorld::Nasdaras) ? 2017 : side>0 ? 1009 : 0; }
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
// Shared analytic course used to grade the countryside's ONE main river.
// The matching World Partition water-spline design is in the 10 km layout JSON.
inline double MorodenachtmerrRiverEast(double north)
{
 return -480.+570.*std::sin(north/1280.)+190.*std::sin(north/460.);
}
inline double MorodenachtmerrRiverSurface(double north)
{
 return 139.+.007*north;
}
inline double MorodenachtmerrSegmentDistance(double east,double north,
 double ax,double ay,double bx,double by)
{
 const double vx=bx-ax,vy=by-ay,den=vx*vx+vy*vy;
 if(den<1.e-9)return std::hypot(east-ax,north-ay);
 const double t=Clamp(((east-ax)*vx+(north-ay)*vy)/den,0.,1.);
 return std::hypot(east-(ax+t*vx),north-(ay+t*vy));
}
inline double Height(EWorld world,double east,double north)
{
 const int width=WidthMeters(world), height=HeightMeters(world);
 if(width==0 || height==0 || !std::isfinite(east) || !std::isfinite(north) ||
    std::abs(east)>width/2. || std::abs(north)>height/2.)return -400.;
 const double n=Fractal(east,north,100+int(world)*97);
 const double r=Fractal(east+2311.,north-1427.,510+int(world)*71);
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
 if(world==EWorld::ApocalypticOutbreak){
  // 15 km x 15 km original post-outbreak landmass: river scar, industrial
  // basin, burned hills, an abandoned central metropolis, and blast craters.
  // These are terrain features, not proof of buildings, radiation gameplay,
  // ruins, or surviving NPC population already placed in Unreal.
  const double metropolis=Gaussian(east,north,-450.,850.,2450.,2250.);
  const double ashHills=390.*Gaussian(east,north,-5100.,4200.,2400.,3600.)*(.72+.28*std::abs(r));
  const double burntRidge=270.*Gaussian(east,north,4100.,-4500.,3100.,1850.)*(.76+.24*std::abs(n));
  const double industrialBasin=90.*Gaussian(east,north,3200.,1100.,1400.,1600.);
  const double riverEast=600.*std::sin(north/1500.)+310.*std::sin(north/610.)+1650.;
  const double riverDist=east-riverEast;
  const double riverCut=75.*std::exp(-(riverDist*riverDist)/(380.*380.));
  const double craterDist=std::hypot(east+3600.,north+2500.);
  const double craterBowl=94.*Gaussian(east,north,-3600.,-2500.,620.,610.);
  const double craterRim=32.*std::exp(-std::pow((craterDist-850.)/230.,2.));
  const double highwayCut=12.*Gaussian(east,north,0.,-1700.,5400.,360.);
  const double wild=133.+95.*n+35.*r+ashHills+burntRidge-industrialBasin-riverCut-craterBowl+craterRim-highwayCut;
  const double cityGrade=119.+14.*ValueNoise(east,north,1300.,2993)-.17*riverCut;
  return wild*(1.-.84*metropolis)+cityGrade*(.84*metropolis);
 }
 if(world==EWorld::Morodenachtmerr){
  // Single 10-km north-to-south MAIN river with a continuous carved bed;
  // three lake basins and four smaller tributaries in a rural terrain.
  // Real water surfaces, boats, fish and gameplay still need UE Water actors.
  const double westRidge=270.*Gaussian(east,north,-3900.,1700.,1250.,2800.)*(.7+.3*std::abs(r));
  const double northWoods=230.*Gaussian(east,north,1700.,3500.,2800.,1800.)*(.65+.35*std::abs(n));
  const double southHills=175.*Gaussian(east,north,3200.,-3400.,2100.,1550.);
  const double fields=18.*std::sin(east/1050.)*std::cos(north/1450.);
  const double marsh=30.*Gaussian(east,north,-850.,-2850.,1280.,900.);
  const double quarry=65.*Gaussian(east,north,3700.,1800.,720.,600.);
  const double hamlet=Gaussian(east,north,-2700.,-1000.,550.,580.);
  const double natural=159.+.007*north+58.*n+20.*r+fields+
    westRidge+northWoods+southHills-marsh-quarry;
  const double townGrade=153.+.007*north+5.*ValueNoise(east,north,1000.,4829);
  double terrain=natural*(1.-.72*hamlet)+townGrade*(.72*hamlet);

  // The only main watercourse: its analytic centre remains within the world
  // from N=+5000 metres to N=-5000 metres. Mean channel width 150-210 m.
  const double riverEast=MorodenachtmerrRiverEast(north);
  const double riverDistance=std::abs(east-riverEast);
  const double riverMask=Smooth((235.-riverDistance)/165.);
  const double riverBed=MorodenachtmerrRiverSurface(north)-4.0;
  terrain=terrain*(1.-riverMask)+riverBed*riverMask;

  // Three connected water bodies. Lake edges blend into the countryside;
  // the lake-water plan in the layout JSON gives exact future actor levels.
  double protectedLakeInterior=0.;
  const double lakes[3][5]={
    {-2650.,2100.,560.,410.,163.},
    {2550.,3050.,480.,340.,173.},
    {2350.,-1850.,590.,460.,137.}
  };
  for(const auto& lake:lakes){
    const double dx=(east-lake[0])/lake[2],dy=(north-lake[1])/lake[3];
    const double ellipse=std::sqrt(dx*dx+dy*dy);
    const double mask=Smooth((1.18-ellipse)/.42);
    protectedLakeInterior=std::max(protectedLakeInterior,Smooth((1.07-ellipse)/.20));
    const double lakeBed=lake[4]-4.5;
    terrain=terrain*(1.-mask)+lakeBed*mask;
  }

  // Four tributaries, using winding independent segments that meet the trunk.
  // They are deliberately narrower than the single main river.
  const double tributaries[4][5][2]={
    {{-4550.,3980.},{-2650.,2100.},{-1600.,1750.},{-700.,1100.},{MorodenachtmerrRiverEast(650.),650.}},
    {{4300.,4100.},{2550.,3050.},{1750.,2500.},{900.,1850.},{MorodenachtmerrRiverEast(1200.),1200.}},
    {{4400.,-550.},{2350.,-1850.},{1500.,-2450.},{600.,-2850.},{MorodenachtmerrRiverEast(-3350.),-3350.}},
    {{-4450.,-3050.},{-3150.,-3650.},{-2200.,-3850.},{-1450.,-4300.},{MorodenachtmerrRiverEast(-4600.),-4600.}}
  };
  double tributaryDistance=1.e9;
  for(const auto& creek:tributaries)
    for(int i=0;i<4;++i)
      tributaryDistance=std::min(tributaryDistance,
        MorodenachtmerrSegmentDistance(east,north,creek[i][0],creek[i][1],creek[i+1][0],creek[i+1][1]));
  const double creekMask=Smooth((52.-tributaryDistance)/35.)*(1.-protectedLakeInterior);
  const double creekBed=MorodenachtmerrRiverSurface(north)-1.6;
  terrain=terrain*(1.-creekMask)+std::min(terrain,creekBed)*creekMask;
  return terrain;
 }
 if(world==EWorld::Nasdaras){
  // 18 x 26 km Sahel-inspired fictional landscape, independent from all maps:
  // northern green escarpment, acacia savannah, desert dunes, oasis basins,
  // dry wadis, palm groves and rocky desert massif. These are terrain shapes:
  // real water, foliage, roads and buildings still require authored UE actors.
  const double northEscarpment=690.*Gaussian(east,north,-6200.,10000.,3100.,6100.)
                                *(.68+.32*std::abs(r));
  const double westHighlands=500.*Gaussian(east,north,-7500.,1600.,2500.,5700.)
                               *(.7+.3*std::abs(n));
  const double eastMassif=730.*Gaussian(east,north,6100.,2200.,2600.,5400.)
                            *(.65+.35*std::abs(r));
  const double drySouth=Smooth((-north-2400.)/5500.);
  const double duneWaves=110.*drySouth*std::pow(std::sin(east/530.+north/920.),2.)
                        +42.*drySouth*std::pow(std::sin(east/170.-north/350.),2.);
  const double scrubSavanna=26.*std::sin(east/1760.)*std::cos(north/2280.);
  const double base=220.+120.*n+50.*r+scrubSavanna+northEscarpment+
                    westHighlands+eastMassif+duneWaves;
  // The broad seasonal Wadi Al-Nasdar valley links the green north to the
  // central savannah, with smaller eroded branches and planted floodplains.
  const double wadiEast=-840.+1400.*std::sin(north/3300.)+
                         540.*std::sin(north/1160.);
  const double riverDistance=std::abs(east-wadiEast);
  const double channel=145.*std::exp(-std::pow(riverDistance/390.,2.));
  const double valley=54.*std::exp(-std::pow(riverDistance/1550.,2.));
  const double sideWadi1=north-(3800.+1300.*std::sin(east/1800.));
  const double sideWadi2=north-(-5600.+980.*std::sin((east+1200.)/1350.));
  const double branches=68.*std::exp(-std::pow(sideWadi1/340.,2.))+
                        59.*std::exp(-std::pow(sideWadi2/300.,2.));
  double terrain=base-channel-valley-branches;
  // Sealed topographic basins; water surfaces and vegetation are NOT created
  // by this native height formula, they must be placed on the saved level.
  const double springs[8][5]={
   {-4800.,6000.,900.,620.,168.},
   {1300.,8700.,720.,580.,202.},
   {-6000.,-1600.,760.,710.,174.},
   {3300.,3000.,800.,560.,192.},
   {5600.,-5200.,1050.,820.,199.},
   {-2200.,-8000.,960.,680.,147.},
   {1700.,-10800.,740.,560.,163.},
   {-7200.,-10500.,660.,540.,155.}
  };
  for(const auto& spring:springs){
   const double d=std::hypot((east-spring[0])/spring[2],
                             (north-spring[1])/spring[3]);
   const double blend=Smooth((1.35-d)/.65);
   const double basinFloor=spring[4]-4.5;
   terrain=terrain*(1.-blend)+basinFloor*blend;
  }
  return terrain;
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
