#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
// Original ANOMALIA geography. Coordinates in metres; north is positive Y.
// No heightmap or geometry from third-party game maps is used.
namespace AnomaliaArchipelago {
inline double Clamp(double x,double lo,double hi){return std::max(lo,std::min(hi,x));}
inline double Smooth(double x){x=Clamp(x,0,1);return x*x*(3-2*x);}
inline double Hash(int x,int y){
 std::uint32_t h=static_cast<std::uint32_t>(x)*374761393u+static_cast<std::uint32_t>(y)*668265263u+1274126177u;
 h=(h^(h>>13))*1274126177u;h^=h>>16;return double(h)/4294967295.*2-1;
}
inline double ValueNoise(double x,double y,double scale){
 x/=scale;y/=scale;const int ix=static_cast<int>(std::floor(x)),iy=static_cast<int>(std::floor(y));
 const double fx=Smooth(x-ix),fy=Smooth(y-iy);
 const double a=Hash(ix,iy)*(1-fx)+Hash(ix+1,iy)*fx;
 const double b=Hash(ix,iy+1)*(1-fx)+Hash(ix+1,iy+1)*fx;
 return a*(1-fy)+b*fy;
}
inline double Noise(double x,double y){
 return .55*ValueNoise(x,y,3200)+.25*ValueNoise(x+1370,y-920,1400)
       +.13*ValueNoise(x-471,y+711,500)+.07*ValueNoise(x+121,y+81,180);
}
inline double Island(double x,double y,double cx,double cy,double rx,double ry,double phase){
 const double dx=(x-cx)/rx,dy=(y-cy)/ry,a=std::atan2(dy,dx);
 return (1+.11*std::sin(3*a+phase)+.065*std::sin(7*a-phase)+.035*std::sin(13*a+phase)-std::sqrt(dx*dx+dy*dy))*std::min(rx,ry);
}
inline double CoastDistance(double x,double y){
 // Connected irregular mainland with long bays, plus genuinely separated islands.
 double d=std::max({Island(x,y,-4500,2300,13300,14300,.4),
                    Island(x,y,3600,-4900,10200,10300,1.7),
                    Island(x,y,-10800,-7500,6600,5900,2.8)});
 // Eastern fjord and western bay penetrate the large island without flattening it.
 d=std::min(d,-Island(x,y,10600,5500,7900,1900,2));
 d=std::min(d,-Island(x,y,-16200,2500,6600,1800,.5));
 const double islands[][5]={{15100,14200,3600,3100,.8},{17800,-10100,2800,4200,2},
 {-17000,16800,3100,2500,1},{-5000,-18700,2800,1500,3},
 {6500,17800,1800,1900,1.5},{14900,1500,1700,2200,2.5},
 {-18800,-13900,1500,2100,.7},{7600,-19100,1700,1200,1.8}};
 for(const auto& i:islands)d=std::max(d,Island(x,y,i[0],i[1],i[2],i[3],i[4]));
 return d;
}
inline double Height(double x,double y){
 const double d=CoastDistance(x,y);
 if(d<0)return -std::min(440.,std::max(0.,-d*.16))+6*Noise(x,y)*Smooth(-d/300.);
 const double inland=Smooth(d/1700.);
 const double alpine=std::exp(-std::pow((x+5700)/5900.,2)-std::pow((y-6800)/7200.,2));
 const double ridge=std::pow(1-std::abs(ValueNoise(x+Noise(x,y)*1100,y-Noise(y,x)*1300,1800)),2.4);
 const double mountains=alpine*(560+1120*ridge);
 const double desert=Smooth((x-1200)/6000.)*Smooth((-y-1800)/5400.);
 const double dunes=desert*(10+8*std::sin(x*.009+y*.002));
 return d*.018+inland*(45+50*Noise(x,y)+mountains)+dunes*Smooth(d/500.);
}
inline std::uint16_t Encode(double height){
 // Unreal: (uint16 - 32768) / 128 * scaleZ cm. Scale Z = 800 => 0.0625 m/code.
 return static_cast<std::uint16_t>(std::lround(Clamp(32768+height*16,0,65535)));
}
}
