#include "AnomaliaZPrigimaliaServerBrowserLibrary.h"

#include "Misc/PackageName.h"

TArray<FAnomaliaZPrigimaliaWorldChoice> UAnomaliaZPrigimaliaServerBrowserLibrary::GetWorldChoices()
{
    struct FWorld { const TCHAR* Id; const TCHAR* Title; const TCHAR* Package; };
    static const FWorld Worlds[] = {
        {TEXT("archipelago-v2"), TEXT("SKARVIK"), TEXT("/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1")},
        {TEXT("inhabited-v2"), TEXT("DRAZOVIA"), TEXT("/Game/Maps/ANOMALIA_Inhabited_v2")},
        {TEXT("karskov-v1"), TEXT("KARSKOV"), TEXT("/Game/Maps/PRIGIMALIA_KARSKOV")},
        {TEXT("vorgrad-v1"), TEXT("VORGRAD"), TEXT("/Game/Maps/PRIGIMALIA_VORGRAD")},
        {TEXT("nemoris-v1"), TEXT("NEMORIS"), TEXT("/Game/Maps/PRIGIMALIA_NEMORIS")},
        {TEXT("drakheim-v1"), TEXT("DRAKHEIM"), TEXT("/Game/Maps/PRIGIMALIA_DRAKHEIM")},
        {TEXT("solynacalyra-v1"), TEXT("SOLYNACALYRA"), TEXT("/Game/Maps/PRIGIMALIA_SOLYNACALYRA")},
        {TEXT("nexavarkhos-v1"), TEXT("NEXAVARKHOS"), TEXT("/Game/Maps/PRIGIMALIA_NEXAVARKHOS")},
        {TEXT("chernaskaluxria-v1"), TEXT("CHERNASKALUXRIA"), TEXT("/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA")},
        {TEXT("falc-v1"), TEXT("F.A.L.C"), TEXT("/Game/Maps/PRIGIMALIA_FALC")},
        {TEXT("kolchiem-origins-v1"), TEXT("KOLCHIEM ORIGINS"), TEXT("/Game/Maps/PRIGIMALIA_KOLCHIEM_ORIGINS")},
        {TEXT("roskatvia-b1-v1"), TEXT("ROSКАТVIA-B1"), TEXT("/Game/Maps/PRIGIMALIA_ROSKATVIA_B1")},
        {TEXT("nogokv-51-v1"), TEXT("НОГОКВ-51"), TEXT("/Game/Maps/PRIGIMALIA_NOGOKV_51")},
        {TEXT("paradisiomania-v1"), TEXT("PARADISIOMANIA"), TEXT("/Game/Maps/PRIGIMALIA_PARADISIOMANIA")},
        {TEXT("deadroot-v1"), TEXT("DEADROOT"), TEXT("/Game/Maps/PRIGIMALIA_DEADROOT")}
    };
    TArray<FAnomaliaZPrigimaliaWorldChoice> Result;
    Result.Reserve(UE_ARRAY_COUNT(Worlds));
    for (const FWorld& World : Worlds)
    {
        FAnomaliaZPrigimaliaWorldChoice Entry;
        Entry.MapId = World.Id;
        Entry.DisplayName = World.Title;
        Entry.WorldPackage = World.Package;
        Entry.bNativePackageFound = !Entry.WorldPackage.IsEmpty() && FPackageName::DoesPackageExist(Entry.WorldPackage);
        Entry.bMultiplayerVerified = false;
        Result.Add(MoveTemp(Entry));
    }
    return Result;
}


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
