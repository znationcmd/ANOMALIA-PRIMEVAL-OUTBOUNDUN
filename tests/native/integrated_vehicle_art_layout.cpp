#include "unreal/Source/AnomaliaZPrigimalia/Vehicles/AnomaliaZPrigimaliaVehicleArtLayout.h"
#include <cassert>
int main(){
 using AnomaliaZPrigimaliaVehicleArt::IsLayoutConsistent;
 assert(IsLayoutConsistent(false,true,true,true,0,0));
 assert(!IsLayoutConsistent(false,true,true,false,0,0));
 assert(IsLayoutConsistent(true,false,false,false,4,4));
 assert(!IsLayoutConsistent(true,true,true,true,4,4));
 assert(!IsLayoutConsistent(true,false,false,false,3,4));
 assert(!IsLayoutConsistent(true,false,false,false,4,3));
 assert(!IsLayoutConsistent(false,true,true,true,4,4));
}
