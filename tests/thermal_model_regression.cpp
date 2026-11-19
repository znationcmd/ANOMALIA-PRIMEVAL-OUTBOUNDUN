#include "../unreal/Source/AnomaliaZPrigimalia/Survival/AnomaliaZPrigimaliaThermalModel.h"
#include <cassert>
#include <limits>
#include <iostream>
int main(){
 using namespace AnomaliaThermal;
 Item f;for(int i=0;i<60;++i)f=Advance(f,-25,60);assert(f.Ice>.99&&!Consumable(f));
 auto one=Advance(f,45,1);assert(one.Ice>.9);
 for(int i=0;i<60;++i){f=Advance(f,45,60);}
 assert(Consumable(f));
 assert(!Consumable({90,0}));assert(!Consumable({20,-1}));assert(!Consumable({std::numeric_limits<double>::quiet_NaN(),0}));
 assert(BodyTarget(45,5,0,1,0,0,.2)<BodyTarget(45,5,0,0,0,0,.2));
 assert(BodyTarget(-15,20,1,0,0,0,.7)<BodyTarget(-15,20,0,0,0,0,.7));
 assert(BodyTarget(-15,10,0,0,1,1,.7)>BodyTarget(-15,10,0,0,1,0,.7));
 assert(Advance({20,0},-20,0).Temperature==20);
 assert(Advance({20,0},std::numeric_limits<double>::quiet_NaN(),10).Temperature==20);
 Item warm,cold;for(int i=0;i<60;++i){warm=Advance(warm,-25,1,.8);cold=Advance(cold,-25,1,0);}assert(warm.Temperature>cold.Temperature);
 std::cout<<"12 thermal regression scenarios passed\n";
}
