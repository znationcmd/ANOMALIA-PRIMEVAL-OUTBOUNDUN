#pragma once
#include <algorithm>
#include <cmath>

// Deterministic game simulation; item phase change includes latent heat.
namespace AnomaliaThermal
{
struct Item { double Temperature=20, Ice=0; };
inline bool Valid(const Item& V) { return std::isfinite(V.Temperature)&&std::isfinite(V.Ice)&&V.Temperature>=-80&&V.Temperature<=120&&V.Ice>=0&&V.Ice<=1; }
inline bool Consumable(const Item& V) { return Valid(V)&&V.Ice<=.01&&V.Temperature>=0&&V.Temperature<=60; }
inline Item Advance(Item V,double Ambient,double Seconds,double Insulation=0)
{
    if(!Valid(V)||!std::isfinite(Ambient)||!std::isfinite(Seconds)||Seconds<=0||!std::isfinite(Insulation))return V;
    Ambient=std::clamp(Ambient,-80.,120.);Seconds=std::min(Seconds,60.);
    double Energy=V.Ice>0 ? -80*V.Ice+std::min(V.Temperature,0.)*2 : V.Temperature*4;
    while(Seconds>0)
    {
        const double Step=std::min(Seconds,1.);Seconds-=Step;
        Energy+=.16*(Ambient-V.Temperature)*Step*(1-std::clamp(Insulation,0.,.95));
        if(Energy< -80){V.Ice=1;V.Temperature=(Energy+80)/2;}
        else if(Energy<0){V.Ice=-Energy/80;V.Temperature=0;}
        else{V.Ice=0;V.Temperature=Energy/4;}
    }
    V.Temperature=std::clamp(V.Temperature,-80.,120.);return V;
}
inline double BodyTarget(double Ambient,double Wind,double Wetness,double HeadWetness,double Shelter,double Heat,double Insulation)
{
    if(!std::isfinite(Ambient)||!std::isfinite(Wind)||!std::isfinite(Wetness)||!std::isfinite(HeadWetness)||!std::isfinite(Shelter)||!std::isfinite(Heat)||!std::isfinite(Insulation))return 37;
    Wind=std::clamp(Wind,0.,60.)*(1-std::clamp(Shelter,0.,1.));
    const double Cold=std::max(0.,20-Ambient)*(1-std::clamp(Insulation,0.,.9)*.8);
    const double Chill=Cold*(.07+Wind*.003)*(1+std::clamp(Wetness,0.,1.));
    const double Hot=std::max(0.,Ambient-20)*.09;
    const double Evaporation=std::max(0.,Ambient-20)*std::clamp(HeadWetness,0.,1.)*.055;
    return std::clamp(37+Hot-Chill-Evaporation+std::clamp(Heat,0.,1.)*4,30.,43.);
}
}
