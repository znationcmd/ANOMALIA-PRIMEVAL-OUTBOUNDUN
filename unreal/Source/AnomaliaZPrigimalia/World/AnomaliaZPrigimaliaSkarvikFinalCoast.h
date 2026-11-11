#pragma once
// SKARVIK final coastline v1 (48x48km): original seven detached islands
// with exactly 125 controlled building terraces on *dry* native land.
// Terrain staging ONLY for /Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.
// Do not replace populated graded v2 or completed seven-island v1 sources.
// 67 wet-site coordinates were provisionally relocated with preserved source IDs.
// Ocean, shore and all CoastDistance <= 100m remain original native geography.
#include "AnomaliaZPrigimaliaArchipelagoHeight.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
namespace AnomaliaZPrigimaliaSkarvikFinalCoast {
struct Terrace {double East;double North;double Half;double Blend;};
static constexpr Terrace Pads[]={
 {2000.0,-8000.0,2000.0,425.0}, // citysample fixed-dry
 {14000.0,15000.0,230.0,300.0}, // frostgard fixed-dry
 {12402.0,548.0,230.0,300.0}, // valdoren RELOCATED_FROM_SEA
 {-5000.0,4000.0,125.0,160.0}, // sylvane fixed-dry
 {-16000.0,7000.0,125.0,160.0}, // kaelm fixed-dry
 {-15556.0,-11617.0,90.0,130.0}, // oasis RELOCATED_FROM_SEA
 {-13338.0,-12895.0,90.0,130.0}, // dunes RELOCATED_FROM_SEA
 {-9000.0,-10000.0,125.0,160.0}, // redridge fixed-dry
 {-5000.0,-4000.0,90.0,130.0}, // firvale fixed-dry
 {4709.0,3529.0,90.0,130.0}, // birch RELOCATED_FROM_SEA
 {-14000.0,17000.0,90.0,130.0}, // highpass fixed-dry
 {7000.0,19000.0,90.0,130.0}, // snowpine fixed-dry
 {8970.0,8745.0,125.0,160.0}, // icehaven RELOCATED_FROM_SEA
 {2000.0,14000.0,90.0,130.0}, // northhamlet fixed-dry
 {18000.0,-13000.0,125.0,160.0}, // harbor fixed-dry
 {3873.0,-14586.0,90.0,130.0}, // southwood RELOCATED_FROM_SEA
 {-10000.0,-1000.0,90.0,130.0}, // river fixed-dry
 {-14289.0,-12892.0,230.0,300.0}, // ravenor RELOCATED_FROM_SEA
 {-17759.0,4438.0,230.0,300.0}, // karstheim RELOCATED_FROM_SEA
 {-17000.0,17000.0,230.0,300.0}, // varengard fixed-dry
 {-2000.0,7000.0,230.0,300.0}, // eldervik fixed-dry
 {318.0,14918.0,230.0,300.0}, // nordfjell RELOCATED_FROM_SEA
 {14018.0,-4579.0,230.0,300.0}, // astermont RELOCATED_FROM_SEA
 {5322.0,-14758.0,230.0,300.0}, // meridia RELOCATED_FROM_SEA
 {-15000.0,-8000.0,145.0,185.0}, // tarzel fixed-dry
 {-18573.0,5711.0,145.0,185.0}, // brumecrete RELOCATED_FROM_SEA
 {4000.0,0.0,145.0,185.0}, // montbrume fixed-dry
 {6384.0,11092.0,145.0,185.0}, // hiverdal RELOCATED_FROM_SEA
 {13824.0,-9444.0,145.0,185.0}, // rosephare RELOCATED_FROM_SEA
 {-3000.0,-19000.0,145.0,185.0}, // bois-sud fixed-dry
 {-12900.0,-12654.0,125.0,160.0}, // kharvel RELOCATED_FROM_SEA
 {-15074.0,-12063.0,125.0,160.0}, // sablecroix RELOCATED_FROM_SEA
 {-12365.0,-12387.0,125.0,160.0}, // miraze RELOCATED_FROM_SEA
 {-9380.0,4360.0,125.0,160.0}, // pierremont fixed-dry
 {-16855.0,8223.0,125.0,160.0}, // cimefonte RELOCATED_FROM_SEA
 {-14980.0,-1905.0,125.0,160.0}, // valleroche RELOCATED_FROM_SEA
 {4020.0,7940.0,125.0,160.0}, // boissauvage fixed-dry
 {6340.0,-2440.0,125.0,160.0}, // clairvallon fixed-dry
 {5327.0,3402.0,125.0,160.0}, // montoree RELOCATED_FROM_SEA
 {-6240.0,2370.0,125.0,160.0}, // valrivage fixed-dry
 {2063.0,14893.0,125.0,160.0}, // glacelac RELOCATED_FROM_SEA
 {16630.0,12620.0,125.0,160.0}, // nivergard fixed-dry
 {7552.0,10662.0,125.0,160.0}, // lysvik RELOCATED_FROM_SEA
 {13702.0,-1423.0,125.0,160.0}, // baie-argent RELOCATED_FROM_SEA
 {10970.0,-7150.0,125.0,160.0}, // hauterive fixed-dry
 {11570.0,-10360.0,125.0,160.0}, // coteverte dry-coastal-adjusted
 {13574.0,-480.0,125.0,160.0}, // port-azur RELOCATED_FROM_SEA
 {4180.0,-14890.0,125.0,160.0}, // pont-vert fixed-dry
 {-4212.0,-13580.0,125.0,160.0}, // merivals RELOCATED_FROM_SEA
 {-2122.0,-14673.0,125.0,160.0}, // cendreval RELOCATED_FROM_SEA
 {729.0,-14827.0,125.0,160.0}, // bas-moulin RELOCATED_FROM_SEA
 {-7479.0,-12941.0,90.0,130.0}, // khemir RELOCATED_FROM_SEA
 {-13308.0,-12333.0,90.0,130.0}, // sable-froid RELOCATED_FROM_SEA
 {-17650.0,-8745.0,90.0,130.0}, // ergued RELOCATED_FROM_SEA
 {-18350.0,-14870.0,90.0,130.0}, // dunevoile fixed-dry
 {-18950.0,-13470.0,90.0,130.0}, // almari fixed-dry
 {-17507.0,-8237.0,90.0,130.0}, // rocheseche RELOCATED_FROM_SEA
 {-19570.0,-12710.0,90.0,130.0}, // elzar fixed-dry
 {-8261.0,-12681.0,90.0,130.0}, // qarven RELOCATED_FROM_SEA
 {-9810.0,-8060.0,90.0,130.0}, // safran fixed-dry
 {-12880.0,-7430.0,90.0,130.0}, // solaroc fixed-dry
 {-7843.0,-12797.0,90.0,130.0}, // tinjar RELOCATED_FROM_SEA
 {-16931.0,-9682.0,90.0,130.0}, // arbelin RELOCATED_FROM_SEA
 {-13101.0,14126.0,90.0,130.0}, // brumepierre RELOCATED_FROM_SEA
 {-19090.0,18050.0,90.0,130.0}, // rochenord fixed-dry
 {-12231.0,15479.0,90.0,130.0}, // vieux-col RELOCATED_FROM_SEA
 {-15199.0,-1256.0,90.0,130.0}, // aiguille-haute RELOCATED_FROM_SEA
 {-16208.0,10489.0,90.0,130.0}, // ravin-dore RELOCATED_FROM_SEA
 {-18672.0,4687.0,90.0,130.0}, // sombreroch RELOCATED_FROM_SEA
 {-16120.0,5550.0,90.0,130.0}, // melezac fixed-dry
 {-15102.0,-873.0,90.0,130.0}, // pierrefeu RELOCATED_FROM_SEA
 {-12018.0,15869.0,90.0,130.0}, // granitel RELOCATED_FROM_SEA
 {-14820.0,5110.0,90.0,130.0}, // fonteval fixed-dry
 {-17850.0,18750.0,90.0,130.0}, // cairn-bas fixed-dry
 {-12794.0,14556.0,90.0,130.0}, // lauzeveil RELOCATED_FROM_SEA
 {6930.0,-7940.0,90.0,130.0}, // fresnelac fixed-dry
 {4530.0,-5000.0,90.0,130.0}, // orme-bas fixed-dry
 {-7010.0,-1220.0,90.0,130.0}, // charmeval fixed-dry
 {-6590.0,-8650.0,90.0,130.0}, // rosemosse fixed-dry
 {-7660.0,-9320.0,90.0,130.0}, // vieux-chene fixed-dry
 {-1600.0,-8610.0,90.0,130.0}, // millefeuille fixed-dry
 {5759.0,3186.0,90.0,130.0}, // boisdore RELOCATED_FROM_SEA
 {-7260.0,5910.0,90.0,130.0}, // longpont fixed-dry
 {7780.0,-8360.0,90.0,130.0}, // fontaine-verte fixed-dry
 {-710.0,-800.0,90.0,130.0}, // hautes-rives fixed-dry
 {-8700.0,2360.0,90.0,130.0}, // epicea fixed-dry
 {1180.0,-3120.0,90.0,130.0}, // valleron fixed-dry
 {9080.0,8203.0,90.0,130.0}, // neigerive RELOCATED_FROM_SEA
 {7884.0,10286.0,90.0,130.0}, // froidepin RELOCATED_FROM_SEA
 {8512.0,9709.0,90.0,130.0}, // osterlac RELOCATED_FROM_SEA
 {-4560.0,11290.0,90.0,130.0}, // glacier-bas fixed-dry
 {230.0,10880.0,90.0,130.0}, // niveore fixed-dry
 {2890.0,10940.0,90.0,130.0}, // lysglace fixed-dry
 {7163.0,10843.0,90.0,130.0}, // fjordin RELOCATED_FROM_SEA
 {15700.0,11200.0,90.0,130.0}, // blanchecrete fixed-dry
 {-110.0,12490.0,90.0,130.0}, // eiskorn fixed-dry
 {8718.0,9123.0,90.0,130.0}, // frostel RELOCATED_FROM_SEA
 {2070.0,10480.0,90.0,130.0}, // nordlac fixed-dry
 {9812.0,3443.0,90.0,130.0}, // malphare RELOCATED_FROM_SEA
 {9900.0,-5930.0,90.0,130.0}, // ardelport fixed-dry
 {11590.0,-8640.0,90.0,130.0}, // capvive fixed-dry
 {13253.0,58.0,90.0,130.0}, // plage-cendre RELOCATED_FROM_SEA
 {13089.0,-516.0,90.0,130.0}, // cote-d-orval RELOCATED_FROM_SEA
 {13390.0,-2900.0,90.0,130.0}, // sablemaree fixed-dry
 {13651.0,-3140.0,90.0,130.0}, // vauclerc RELOCATED_FROM_SEA
 {10800.0,-9050.0,90.0,130.0}, // etang-sale fixed-dry
 {11730.0,-5500.0,90.0,130.0}, // vieux-quai fixed-dry
 {13683.0,-899.0,90.0,130.0}, // fonte-mer RELOCATED_FROM_SEA
 {13602.0,-9912.0,90.0,130.0}, // elmarin RELOCATED_FROM_SEA
 {18590.0,-8890.0,90.0,130.0}, // cap-aube fixed-dry
 {13011.0,-190.0,90.0,130.0}, // valest RELOCATED_FROM_SEA
 {5900.0,-13990.0,90.0,130.0}, // auberive RELOCATED_FROM_SEA
 {-1117.0,-15153.0,90.0,130.0}, // herbehaute RELOCATED_FROM_SEA
 {6438.0,-13600.0,90.0,130.0}, // sauleval RELOCATED_FROM_SEA
 {24.0,-15061.0,90.0,130.0}, // merilac RELOCATED_FROM_SEA
 {6073.0,-13591.0,90.0,130.0}, // boissain RELOCATED_FROM_SEA
 {-1610.0,-15024.0,90.0,130.0}, // pont-d-oree RELOCATED_FROM_SEA
 {-357.0,-15201.0,90.0,130.0}, // grandpre RELOCATED_FROM_SEA
 {-674.0,-15157.0,90.0,130.0}, // corne-bois RELOCATED_FROM_SEA
 {243.0,-14724.0,90.0,130.0}, // rive-basse RELOCATED_FROM_SEA
 {-2710.0,-14294.0,90.0,130.0}, // montbrun RELOCATED_FROM_SEA
 {-1530.0,-14670.0,90.0,130.0}, // loupvallon fixed-dry
 {4451.0,-14316.0,90.0,130.0}, // vermont RELOCATED_FROM_SEA
 {-80.0,-14700.0,90.0,130.0}, // coulevie fixed-dry
 {-962.0,-14790.0,90.0,130.0}, // bellevigne RELOCATED_FROM_SEA
};
static constexpr int Count=int(sizeof(Pads)/sizeof(Pads[0]));
inline double Height(double e,double n){
 using namespace AnomaliaZPrigimaliaArchipelago;
 if(!std::isfinite(e)||!std::isfinite(n))return -440.;
 const double coast=CoastDistance(e,n);
 double h=AnomaliaZPrigimaliaArchipelago::Height(e,n);
 if(coast<=100.)return h; // never raise oceanbed, coastline, or beach across sea
 double bestWeight=0.;
 double bestTarget=h;
 for(const auto& p:Pads){
  const double dx=std::abs(e-p.East),dy=std::abs(n-p.North);
  if(dx>p.Half+p.Blend || dy>p.Half+p.Blend)continue;
  const double d=std::max(dx-p.Half,dy-p.Half);
  const double weight=1.-Smooth(d/p.Blend);
  if(weight<=bestWeight)continue;
  // Source terrain elevation at the pad center (on its own landmass).
  // No height guessed from the old graded mainland-only terrain.
  bestWeight=weight;
  bestTarget=AnomaliaZPrigimaliaArchipelago::Height(p.East,p.North);
 }
 h=h*(1.-bestWeight)+bestTarget*bestWeight;
 return Clamp(h,-440.,1850.);
}
inline std::uint16_t Encode(double h){
 return AnomaliaZPrigimaliaArchipelago::Encode(h);
}
} // namespace AnomaliaZPrigimaliaSkarvikFinalCoast
