#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

// ORIGINAL height field for a NEW 48x48 km SKARVIK world.
// All inputs are east/north in metres. This file does NOT edit the old archipelago.
// Urban sites are reserved/levelled, NOT claimed to have constructed buildings.
namespace AnomaliaZPrigimaliaSkarvik
{
inline double Clamp(double t,double a,double b){return std::max(a,std::min(b,t));}
inline double Smooth(double t){t=Clamp(t,0.,1.);return t*t*(3.-2.*t);}
inline double Gaussian(double x,double y,double cx,double cy,double rx,double ry)
{
 const double dx=(x-cx)/rx,dy=(y-cy)/ry;
 return std::exp(-(dx*dx+dy*dy));
}
inline double Fractal(double x,double y)
{
 return .54*std::sin(x/2550.)*std::cos(y/2830.)
       +.27*std::sin((x+1000.)/860.)*std::sin((y-770.)/970.)
       +.13*std::sin((x-y)/330.)*std::cos((x+y)/270.)
       +.06*std::sin(x/110.+y/140.);
}
inline double Ridge(double x,double y)
{
 const double v=std::sin(x/1770.+.30*std::sin(y/730.))
               *std::cos(y/1310.-.24*std::sin(x/680.));
 return 1.-std::abs(v);
}
struct UrbanPad
{
 double East,North,HalfEast,HalfNorth,FlatElevation,Blend;
};
static constexpr UrbanPad Sites[]={
 // Main City Sample full urban footprint 4x4 km, native scale is preserved.
 {  2000., -8000., 2200.,2200.,100., 1100.},
 // Large snow-bound city and eastern/lowland large city.
 { 14000., 15000., 1600.,1600.,540., 850.},
 { 13000.,  1000., 1450.,1450.,130., 600.},
 // Towns and actual planned villages in distinct climates.
 { -5000.,  4000., 700.,700.,185.,450.},
 {-16000.,  7000., 650.,650.,680.,450.},
 {-17000.,-13000.,350.,350.,250.,300.},
 {-12000.,-19000.,330.,330.,200.,300.},
 { -9000.,-10000.,650.,650.,195.,350.},
 { -5000., -4000.,330.,330.,135.,250.},
 {  5000.,  5000.,330.,330.,185.,280.},
 {-14000., 17000.,330.,330.,1120.,350.},
 {  7000., 19000.,350.,350.,710.,280.},
 { 20000., 12000.,500.,500.,480.,300.},
 {  2000., 14000.,340.,340.,750.,300.},
 { 18000.,-13000.,650.,650.,95.,450.},
 {  3000.,-19000.,340.,340.,110.,320.},
 {-10000., -1000.,340.,340.,210.,270.},
};

inline double UnpaddedHeight(double east,double north)
{
 const double noise=Fractal(east,north);
 const double ridge=Ridge(east,north);
 const double western=Gaussian(east,north,-16700.,8500.,7600.,12400.);
 const double northern=Gaussian(east,north,3200.,17500.,15900.,10500.);
 const double desert=Smooth((-east-6500.)/8500.)*(1.-Smooth((north+4000.)/11000.));
 const double westernPeaks=western*(210.+850.*ridge);
 const double northernPeaks=northern*(185.+820.*ridge);
 const double dunes=desert*(38.+28.*std::sin(east/410.+north/670.));
 const double valley=68.*Gaussian(east,north,1000.,-2700.,12500.,11000.);
 const double river=23.*std::exp(-std::pow((east+6000.-3600.*std::sin(north/7200.))/700.,2.));
 // Cold plateau in the northeast, above lowland woods and the western desert.
 double height=112.+52.*noise+westernPeaks+northernPeaks+dunes
              +160.*Smooth((north-3500.)/13000.)-valley-river;
 // Ensure a gradual rim/coast but retain land area across the entire 48km square.
 const double rim=std::min(24000.-std::abs(east),24000.-std::abs(north));
 height=height*Smooth((rim+350.)/1200.)-20.*(1.-Smooth((rim+350.)/1200.));
 return Clamp(height,-50.,1850.);
}
inline double Height(double east,double north)
{
 if(!std::isfinite(east)||!std::isfinite(north))return -50.;
 double h=UnpaddedHeight(east,north);
 for(const UrbanPad& p:Sites)
 {
  const double distance=std::max(std::abs(east-p.East)-p.HalfEast,
                                 std::abs(north-p.North)-p.HalfNorth);
  const double influence=1.-Smooth(distance/p.Blend);
  if(influence>0.)h=h*(1.-influence)+p.FlatElevation*influence;
 }
 return Clamp(h,-50.,1850.);
}
inline std::uint16_t Encode(double metres)
{
 // Landscape Z scale 800: 1 quantized value = 0.0625 metre.
 return static_cast<std::uint16_t>(std::lround(Clamp(32768.+metres*16.,0.,65535.)));
}
} // namespace AnomaliaZPrigimaliaSkarvik
