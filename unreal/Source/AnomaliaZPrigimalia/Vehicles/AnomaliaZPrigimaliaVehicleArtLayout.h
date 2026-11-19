#pragma once
namespace AnomaliaZPrigimaliaVehicleArt
{
// A complete skeletal vehicle must not silently combine with duplicate detached art.
// Modular configurations preserve the original body + reference-wheel contract.
inline bool IsLayoutConsistent(bool integrated,bool anyDetachedArt,bool body,bool wheel,int classes,int radii)
{
 if(integrated)return !anyDetachedArt && classes==4 && radii==4;
 return body && wheel && classes==0 && radii==0;
}
}
