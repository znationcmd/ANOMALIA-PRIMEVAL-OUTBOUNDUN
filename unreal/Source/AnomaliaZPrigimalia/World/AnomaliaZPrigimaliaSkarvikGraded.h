#pragma once
// Original-only SKARVIK relief v2: 124 graded settlement centres.
// Generated from public/config/skarvik-world-layout-48km.json.
// Does not change SKARVIK v1 or the protected D: original.
// Retains the City Sample 4x4 km pad at true size.
// Each site has an interior flat core for real building foundations, with
// smooth transition back to the surrounding native 48km mountain geometry.
#include "AnomaliaZPrigimaliaSkarvikTerrain.h"
namespace AnomaliaZPrigimaliaSkarvikGraded
{
struct BuildPad { double East, North, FlatHalfEast, FlatHalfNorth, Blend; };
// 10 large cities, 6 small towns, 26 towns, 83 villages total
// minus City Sample (SKARVIK-CENTRE), handled by terrain v1.
static constexpr BuildPad Pads[] = {
 { 14000.0, 15000.0, 230., 230., 380. }, // frostgard
 { 13000.0, 1000.0, 230., 230., 380. }, // valdoren
 { -5000.0, 4000.0, 125., 125., 180. }, // sylvane
 { -16000.0, 7000.0, 125., 125., 180. }, // kaelm
 { -17000.0, -13000.0, 90., 90., 130. }, // oasis
 { -12000.0, -19000.0, 90., 90., 130. }, // dunes
 { -9000.0, -10000.0, 125., 125., 180. }, // redridge
 { -5000.0, -4000.0, 90., 90., 130. }, // firvale
 { 5000.0, 5000.0, 90., 90., 130. }, // birch
 { -14000.0, 17000.0, 90., 90., 130. }, // highpass
 { 7000.0, 19000.0, 90., 90., 130. }, // snowpine
 { 20000.0, 12000.0, 125., 125., 180. }, // icehaven
 { 2000.0, 14000.0, 90., 90., 130. }, // northhamlet
 { 18000.0, -13000.0, 125., 125., 180. }, // harbor
 { 3000.0, -19000.0, 90., 90., 130. }, // southwood
 { -10000.0, -1000.0, 90., 90., 130. }, // river
 { -19000.0, -17000.0, 230., 230., 380. }, // ravenor
 { -18000.0, 4000.0, 230., 230., 380. }, // karstheim
 { -17000.0, 17000.0, 230., 230., 380. }, // varengard
 { -2000.0, 7000.0, 230., 230., 380. }, // eldervik
 { -1000.0, 20000.0, 230., 230., 380. }, // nordfjell
 { 19000.0, -5000.0, 230., 230., 380. }, // astermont
 { 5000.0, -21000.0, 230., 230., 380. }, // meridia
 { -15000.0, -8000.0, 145., 145., 220. }, // tarzel
 { -22000.0, 9000.0, 145., 145., 220. }, // brumecrete
 { 4000.0, 0.0, 145., 145., 220. }, // montbrume
 { 8000.0, 13000.0, 145., 145., 220. }, // hiverdal
 { 21000.0, -14000.0, 145., 145., 220. }, // rosephare
 { -3000.0, -19000.0, 145., 145., 220. }, // bois-sud
 { -15680.0, -19350.0, 125., 125., 180. }, // kharvel
 { -16930.0, -14420.0, 125., 125., 180. }, // sablecroix
 { -13750.0, -16140.0, 125., 125., 180. }, // miraze
 { -9380.0, 4360.0, 125., 125., 180. }, // pierremont
 { -17250.0, 8530.0, 125., 125., 180. }, // cimefonte
 { -17730.0, -1940.0, 125., 125., 180. }, // valleroche
 { 4020.0, 7940.0, 125., 125., 180. }, // boissauvage
 { 6340.0, -2440.0, 125., 125., 180. }, // clairvallon
 { 5450.0, 3620.0, 125., 125., 180. }, // montoree
 { -6240.0, 2370.0, 125., 125., 180. }, // valrivage
 { 8570.0, 18090.0, 125., 125., 180. }, // glacelac
 { 16630.0, 12620.0, 125., 125., 180. }, // nivergard
 { 15760.0, 20090.0, 125., 125., 180. }, // lysvik
 { 16340.0, -2200.0, 125., 125., 180. }, // baie-argent
 { 10970.0, -7150.0, 125., 125., 180. }, // hauterive
 { 11570.0, -10760.0, 125., 125., 180. }, // coteverte
 { 20470.0, -1680.0, 125., 125., 180. }, // port-azur
 { 4180.0, -14890.0, 125., 125., 180. }, // pont-vert
 { -4920.0, -14610.0, 125., 125., 180. }, // merivals
 { -3420.0, -16810.0, 125., 125., 180. }, // cendreval
 { 960.0, -18570.0, 125., 125., 180. }, // bas-moulin
 { -9630.0, -17730.0, 90., 90., 130. }, // khemir
 { -13990.0, -19300.0, 90., 90., 130. }, // sable-froid
 { -20400.0, -8780.0, 90., 90., 130. }, // ergued
 { -18350.0, -14870.0, 90., 90., 130. }, // dunevoile
 { -18950.0, -13470.0, 90., 90., 130. }, // almari
 { -19010.0, -7340.0, 90., 90., 130. }, // rocheseche
 { -19570.0, -12710.0, 90., 90., 130. }, // elzar
 { -9930.0, -16860.0, 90., 90., 130. }, // qarven
 { -9810.0, -8060.0, 90., 90., 130. }, // safran
 { -12880.0, -7430.0, 90., 90., 130. }, // solaroc
 { -9720.0, -15450.0, 90., 90., 130. }, // tinjar
 { -18540.0, -10370.0, 90., 90., 130. }, // arbelin
 { -14340.0, 14290.0, 90., 90., 130. }, // brumepierre
 { -19090.0, 18050.0, 90., 90., 130. }, // rochenord
 { -16470.0, 21050.0, 90., 90., 130. }, // vieux-col
 { -20160.0, -1880.0, 90., 90., 130. }, // aiguille-haute
 { -19360.0, 12520.0, 90., 90., 130. }, // ravin-dore
 { -20720.0, 680.0, 90., 90., 130. }, // sombreroch
 { -16120.0, 5550.0, 90., 90., 130. }, // melezac
 { -21030.0, -1800.0, 90., 90., 130. }, // pierrefeu
 { -13640.0, 19250.0, 90., 90., 130. }, // granitel
 { -14820.0, 5110.0, 90., 90., 130. }, // fonteval
 { -17870.0, 19080.0, 90., 90., 130. }, // cairn-bas
 { -18580.0, 20080.0, 90., 90., 130. }, // lauzeveil
 { 6930.0, -7940.0, 90., 90., 130. }, // fresnelac
 { 4530.0, -5000.0, 90., 90., 130. }, // orme-bas
 { -7010.0, -1220.0, 90., 90., 130. }, // charmeval
 { -6590.0, -8650.0, 90., 90., 130. }, // rosemosse
 { -7660.0, -9320.0, 90., 90., 130. }, // vieux-chene
 { -1600.0, -8610.0, 90., 90., 130. }, // millefeuille
 { 6410.0, 4810.0, 90., 90., 130. }, // boisdore
 { -7260.0, 5910.0, 90., 90., 130. }, // longpont
 { 7780.0, -8360.0, 90., 90., 130. }, // fontaine-verte
 { -710.0, -800.0, 90., 90., 130. }, // hautes-rives
 { -8700.0, 2360.0, 90., 90., 130. }, // epicea
 { 1180.0, -3120.0, 90., 90., 130. }, // valleron
 { 21990.0, 12150.0, 90., 90., 130. }, // neigerive
 { 12490.0, 18880.0, 90., 90., 130. }, // froidepin
 { 20030.0, 13880.0, 90., 90., 130. }, // osterlac
 { -4560.0, 11290.0, 90., 90., 130. }, // glacier-bas
 { 230.0, 10880.0, 90., 90., 130. }, // niveore
 { 2890.0, 10940.0, 90., 90., 130. }, // lysglace
 { 9780.0, 12770.0, 90., 90., 130. }, // fjordin
 { 15700.0, 11200.0, 90., 90., 130. }, // blanchecrete
 { -110.0, 12490.0, 90., 90., 130. }, // eiskorn
 { 18840.0, 13430.0, 90., 90., 130. }, // frostel
 { 2070.0, 10480.0, 90., 90., 130. }, // nordlac
 { 16000.0, 6140.0, 90., 90., 130. }, // malphare
 { 9900.0, -5930.0, 90., 90., 130. }, // ardelport
 { 11590.0, -8640.0, 90., 90., 130. }, // capvive
 { 19310.0, 1600.0, 90., 90., 130. }, // plage-cendre
 { 18410.0, 4770.0, 90., 90., 130. }, // cote-d-orval
 { 13390.0, -2900.0, 90., 90., 130. }, // sablemaree
 { 21390.0, -2730.0, 90., 90., 130. }, // vauclerc
 { 10800.0, -9050.0, 90., 90., 130. }, // etang-sale
 { 11730.0, -5500.0, 90., 90., 130. }, // vieux-quai
 { 18530.0, 6980.0, 90., 90., 130. }, // fonte-mer
 { 14320.0, -10130.0, 90., 90., 130. }, // elmarin
 { 18590.0, -8890.0, 90., 90., 130. }, // cap-aube
 { 15330.0, 4240.0, 90., 90., 130. }, // valest
 { 6140.0, -16730.0, 90., 90., 130. }, // auberive
 { -3240.0, -21560.0, 90., 90., 130. }, // herbehaute
 { 8300.0, -17140.0, 90., 90., 130. }, // sauleval
 { -140.0, -16300.0, 90., 90., 130. }, // merilac
 { 6300.0, -14820.0, 90., 90., 130. }, // boissain
 { -4390.0, -21720.0, 90., 90., 130. }, // pont-d-oree
 { -260.0, -20700.0, 90., 90., 130. }, // grandpre
 { -3220.0, -20590.0, 90., 90., 130. }, // corne-bois
 { -1020.0, -22370.0, 90., 90., 130. }, // rive-basse
 { -5490.0, -20990.0, 90., 90., 130. }, // montbrun
 { -1530.0, -14670.0, 90., 90., 130. }, // loupvallon
 { 5140.0, -18510.0, 90., 90., 130. }, // vermont
 { -80.0, -14700.0, 90., 90., 130. }, // coulevie
 { -1670.0, -15820.0, 90., 90., 130. }, // bellevigne
};
static constexpr int Count = int(sizeof(Pads)/sizeof(Pads[0]));
inline double Height(double east,double north)
{
 if(!std::isfinite(east)||!std::isfinite(north)) return -50.;
 double h=AnomaliaZPrigimaliaSkarvik::Height(east,north);
 for(const BuildPad& p : Pads)
 {
   const double dx=std::abs(east-p.East);
   const double dy=std::abs(north-p.North);
   if(dx>=p.FlatHalfEast+p.Blend || dy>=p.FlatHalfNorth+p.Blend) continue;
   const double d=std::max(dx-p.FlatHalfEast,dy-p.FlatHalfNorth);
   const double weight=1.-AnomaliaZPrigimaliaSkarvik::Smooth(d/p.Blend);
   if(weight<=0.) continue;
   // One local elevation per settlement: true flat, not floating mesh pivots.
   const double ground=AnomaliaZPrigimaliaSkarvik::Height(p.East,p.North);
   h=h*(1.-weight)+ground*weight;
 }
 return AnomaliaZPrigimaliaSkarvik::Clamp(h,-50.,1850.);
}
inline std::uint16_t Encode(double metres)
{
 return AnomaliaZPrigimaliaSkarvik::Encode(metres);
}
} // namespace AnomaliaZPrigimaliaSkarvikGraded
