#include "AnomaliaServerBrowserLibrary.h"

TArray<FAnomaliaServerCard> UAnomaliaServerBrowserLibrary::GetOfficialServerTemplates()
{
    TArray<FAnomaliaServerCard> Result;
    Result.Reserve(15);
    struct FModeLabel { EAnomaliaServerFilter Mode; const TCHAR* Id; const TCHAR* Display; };
    const FModeLabel Modes[] = {
        {EAnomaliaServerFilter::PVE, TEXT("pve"), TEXT("PVE")},
        {EAnomaliaServerFilter::PVP, TEXT("pvp"), TEXT("PVP")},
        {EAnomaliaServerFilter::RP, TEXT("rp"), TEXT("RP")}
    };
    for (const FModeLabel& Group : Modes)
    {
        for (int32 Index = 1; Index <= 5; ++Index)
        {
            FAnomaliaServerCard Card;
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

TArray<FAnomaliaServerCard> UAnomaliaServerBrowserLibrary::FilterByMode(
    const TArray<FAnomaliaServerCard>& Servers, EAnomaliaServerFilter Mode, bool bOnlyOnline)
{
    TArray<FAnomaliaServerCard> Result;
    for (const FAnomaliaServerCard& Card : Servers)
    {
        if (Mode != EAnomaliaServerFilter::All && Card.Mode != Mode) continue;
        if (bOnlyOnline && (!Card.bOnline || !Card.bProvisioned)) continue;
        Result.Add(Card);
    }
    return Result;
}
