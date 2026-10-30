#include "AnomaliaZPrigimaliaServerBrowserLibrary.h"

TArray<FAnomaliaZPrigimaliaServerCard> UAnomaliaZPrigimaliaServerBrowserLibrary::GetOfficialServerTemplates()
{
    TArray<FAnomaliaZPrigimaliaServerCard> Result;
    Result.Reserve(15);
    struct FModeLabel { EAnomaliaZPrigimaliaServerFilter Mode; const TCHAR* Id; const TCHAR* Display; };
    const FModeLabel Modes[] = {
        {EAnomaliaZPrigimaliaServerFilter::PVE, TEXT("pve"), TEXT("PVE")},
        {EAnomaliaZPrigimaliaServerFilter::PVP, TEXT("pvp"), TEXT("PVP")},
        {EAnomaliaZPrigimaliaServerFilter::RP, TEXT("rp"), TEXT("RP")}
    };
    for (const FModeLabel& Group : Modes)
    {
        for (int32 Index = 1; Index <= 5; ++Index)
        {
            FAnomaliaZPrigimaliaServerCard Card;
            Card.ServerId = FString::Printf(TEXT("official-%s-%02d"), Group.Id, Index);
            Card.DisplayName = FString::Printf(TEXT("ANOMALIA OFFICIEL %s %02d"), Group.Display, Index);
            Card.Mode = Group.Mode;
            // Never pretend a planned slot is online or already deployed.
            Card.bProvisioned = false;
            Card.bOnline = false;
            Card.CurrentPlayers = 0;
            Card.PingMs = -1;
            Result.Add(Card);
        }
    }
    return Result;
}

TArray<FAnomaliaZPrigimaliaServerCard> UAnomaliaZPrigimaliaServerBrowserLibrary::FilterByMode(
    const TArray<FAnomaliaZPrigimaliaServerCard>& Servers, EAnomaliaZPrigimaliaServerFilter Mode, bool bOnlyOnline)
{
    TArray<FAnomaliaZPrigimaliaServerCard> Result;
    for (const FAnomaliaZPrigimaliaServerCard& Card : Servers)
    {
        if (Mode != EAnomaliaZPrigimaliaServerFilter::All && Card.Mode != Mode) continue;
        if (bOnlyOnline && (!Card.bOnline || !Card.bProvisioned)) continue;
        Result.Add(Card);
    }
    return Result;
}
