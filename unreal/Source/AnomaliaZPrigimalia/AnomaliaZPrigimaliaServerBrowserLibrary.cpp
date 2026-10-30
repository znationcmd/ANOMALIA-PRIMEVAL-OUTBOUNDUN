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

TArray<FAnomaliaZPrigimaliaWorldMapCard> UAnomaliaZPrigimaliaServerBrowserLibrary::GetIndependentWorldMaps()
{
    // Each entry is a different .umap and has its own persistent identity.
    // This catalog is not a claim that a game server or world is already online.
    struct FDefinition { const TCHAR* Id; const TCHAR* Name; const TCHAR* Path; int32 Side; };
    const FDefinition Definitions[] = {
        {TEXT("archipelago-v2"), TEXT("SKARVIK"), TEXT("/Game/Maps/ANOMALIA_Archipelago_v2"), 48},
        {TEXT("inhabited-v2"), TEXT("DRAZOVIA"), TEXT("/Game/Maps/ANOMALIA_Inhabited_v2"), 48},
        {TEXT("karskov-v1"), TEXT("KARSKOV"), TEXT("/Game/Maps/PRIGIMALIA_KARSKOV"), 30},
        {TEXT("vorgrad-v1"), TEXT("VORGRAD"), TEXT("/Game/Maps/PRIGIMALIA_VORGRAD"), 30},
        {TEXT("nemoris-v1"), TEXT("NEMORIS"), TEXT("/Game/Maps/PRIGIMALIA_NEMORIS"), 20},
        {TEXT("drakheim-v1"), TEXT("DRAKHEIM"), TEXT("/Game/Maps/PRIGIMALIA_DRAKHEIM"), 20},
        {TEXT("solynacalyra-v1"), TEXT("SOLYNACALYRA"), TEXT("/Game/Maps/PRIGIMALIA_SOLYNACALYRA"), 15},
        {TEXT("nexavarkhos-v1"), TEXT("NEXAVARKHOS"), TEXT("/Game/Maps/PRIGIMALIA_NEXAVARKHOS"), 10},
        {TEXT("chernaskaluxria-v1"), TEXT("CHERNASKALUXRIA"), TEXT("/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA"), 100},
    };
    TArray<FAnomaliaZPrigimaliaWorldMapCard> Maps;
    Maps.Reserve(UE_ARRAY_COUNT(Definitions));
    for (const FDefinition& Definition : Definitions)
    {
        FAnomaliaZPrigimaliaWorldMapCard Card;
        Card.MapId = Definition.Id;
        Card.DisplayName = Definition.Name;
        Card.UnrealPackage = Definition.Path;
        Card.WidthKm = Definition.Side;
        Card.HeightKm = Definition.Side;
        Card.bPlayableValidated = false; // Never claim online/playable without native tests.
        Maps.Add(MoveTemp(Card));
    }
    return Maps;
}

TArray<FAnomaliaZPrigimaliaServerCard> UAnomaliaZPrigimaliaServerBrowserLibrary::FilterByMap(
    const TArray<FAnomaliaZPrigimaliaServerCard>& Servers, const FString& MapId, bool bOnlyOnline)
{
    TArray<FAnomaliaZPrigimaliaServerCard> Result;
    bool bValidMap = false;
    for (const FAnomaliaZPrigimaliaWorldMapCard& World : GetIndependentWorldMaps())
    {
        if (World.MapId == MapId) { bValidMap = true; break; }
    }
    if (!bValidMap) return Result; // Unknown map must never route to a different world.
    for (const FAnomaliaZPrigimaliaServerCard& Server : Servers)
    {
        if (Server.MapId != MapId) continue;
        if (bOnlyOnline && (!Server.bOnline || !Server.bProvisioned)) continue;
        Result.Add(Server);
    }
    return Result;
}
