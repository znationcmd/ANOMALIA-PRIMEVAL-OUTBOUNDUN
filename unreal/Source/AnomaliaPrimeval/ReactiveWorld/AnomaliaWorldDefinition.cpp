#include "AnomaliaWorldDefinition.h"

bool FAnomaliaMechanismState::NetSerialize(FArchive& Ar,UPackageMap* Map,bool& bOutSuccess)
{
    uint8 Stage=uint8(Repair);Ar<<Stage;
    Ar<<RepairEndsUtc;Ar<<FuelSeconds;Ar<<bSwitchedOn;Ar<<bUnlocked;Ar<<PortalEndsUtc;
    uint8 Count=uint8(FMath::Min(Deposited.Num(),64));Ar<<Count;
    if(Count>64 || Stage>uint8(EAnomaliaRepairState::Disabled)) {bOutSuccess=false;return false;}
    if(Ar.IsLoading())
    {
        Repair=EAnomaliaRepairState(Stage);Deposited.Reset();
        for(uint8 I=0;I<Count;++I) {FName Id;int32 Units=0;Ar<<Id;Ar<<Units;Deposited.Add(Id,Units);}
    }
    else {uint8 I=0;for(auto& Pair:Deposited) {if(I++>=Count) break;FName Id=Pair.Key;int32 Units=Pair.Value;Ar<<Id;Ar<<Units;}}
    bOutSuccess=!Ar.IsError();return bOutSuccess;
}
