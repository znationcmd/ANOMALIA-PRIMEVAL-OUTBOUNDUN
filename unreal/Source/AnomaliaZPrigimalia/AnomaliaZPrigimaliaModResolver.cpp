#include "AnomaliaZPrigimaliaModResolver.h"
#include "Templates/Function.h"

namespace
{
    bool IsDigitAscii(TCHAR C) { return C >= TEXT('0') && C <= TEXT('9'); }
    bool IsLowerAscii(TCHAR C) { return C >= TEXT('a') && C <= TEXT('z'); }
    bool IsUpperAscii(TCHAR C) { return C >= TEXT('A') && C <= TEXT('Z'); }
    bool IsAlphaNumericAscii(TCHAR C)
    {
        return IsDigitAscii(C) || IsLowerAscii(C) || IsUpperAscii(C);
    }
}

bool UAnomaliaZPrigimaliaModResolver::ValidModId(const FString& Id)
{
    if (Id.Len() < 2 || Id.Len() > 80 ||
        !(IsLowerAscii(Id[0]) || IsDigitAscii(Id[0]))) return false;
    for (const TCHAR C : Id)
        if (!(IsLowerAscii(C) || IsDigitAscii(C) ||
              C == TEXT('.') || C == TEXT('_') || C == TEXT('-'))) return false;
    return true;
}

bool UAnomaliaZPrigimaliaModResolver::ValidSha256(const FString& Hash)
{
    if (Hash.Len() != 64) return false;
    for (const TCHAR C : Hash)
        if (!(IsDigitAscii(C) || (C >= TEXT('a') && C <= TEXT('f')) ||
              (C >= TEXT('A') && C <= TEXT('F')))) return false;
    return true;
}

bool UAnomaliaZPrigimaliaModResolver::ValidVersion(const FString& Version)
{
    FString CoreVersion = Version;
    int32 DashIndex = INDEX_NONE;
    if (Version.FindChar(TEXT('-'), DashIndex))
    {
        CoreVersion = Version.Left(DashIndex);
        const FString Suffix = Version.Mid(DashIndex + 1);
        if (Suffix.IsEmpty()) return false;
        for (TCHAR C : Suffix)
            if (!(IsAlphaNumericAscii(C) || C == TEXT('.') || C == TEXT('-')))
                return false;
    }

    TArray<FString> Numbers;
    CoreVersion.ParseIntoArray(Numbers, TEXT("."), false);
    if (Numbers.Num() != 3) return false;
    for (const FString& Number : Numbers)
    {
        if (Number.IsEmpty()) return false;
        for (TCHAR C : Number)
            if (!IsDigitAscii(C)) return false;
    }
    return true;
}

bool UAnomaliaZPrigimaliaModResolver::ValidateModManifest(
    const FAnomaliaZPrigimaliaModManifest& Manifest, FString& OutError)
{
    OutError.Empty();
    if (!ValidModId(Manifest.Id)) { OutError = TEXT("Invalid mod ID"); return false; }
    if (!ValidVersion(Manifest.Version)) { OutError = TEXT("Invalid mod version"); return false; }
    if (!ValidSha256(Manifest.Sha256)) { OutError = TEXT("Missing SHA-256 checksum"); return false; }
    for (const FString& Dependency : Manifest.Dependencies)
        if (!ValidModId(Dependency))
        {
            OutError = TEXT("Invalid dependencies");
            return false;
        }
    if (!Manifest.Compatibility.Contains(TEXT("solo")) &&
        !Manifest.Compatibility.Contains(TEXT("cmd-hosting")) &&
        !Manifest.Compatibility.Contains(TEXT("dedicated")))
    {
        OutError = TEXT("No supported installation mode");
        return false;
    }
    if (!Manifest.bSigned) { OutError = TEXT("Unsigned mod rejected"); return false; }
    return true;
}

bool UAnomaliaZPrigimaliaModResolver::ResolveMods(
    const TArray<FString>& Requested,
    const TArray<FAnomaliaZPrigimaliaModManifest>& Catalog,
    const TArray<FAnomaliaZPrigimaliaModManifest>& Installed,
    FAnomaliaZPrigimaliaModResolution& OutResolution,
    FString& OutError)
{
    OutResolution = FAnomaliaZPrigimaliaModResolution();
    OutError.Empty();
    TMap<FString, const FAnomaliaZPrigimaliaModManifest*> ById;
    for (const FAnomaliaZPrigimaliaModManifest& Manifest : Catalog)
    {
        if (ById.Contains(Manifest.Id))
        {
            OutError = FString::Printf(TEXT("Duplicate catalog mod ID: %s"), *Manifest.Id);
            return false;
        }
        ById.Add(Manifest.Id, &Manifest);
    }

    FAnomaliaZPrigimaliaModResolution Result;
    TMap<FString, int32> State; // absent / 1 visiting / 2 visited
    TFunction<bool(const FString&)> Visit;
    Visit = [&](const FString& Id) -> bool
    {
        const int32 Current = State.FindRef(Id);
        if (Current == 2) return true;
        if (Current == 1)
        {
            OutError = FString::Printf(TEXT("Circular mod dependency: %s"), *Id);
            return false;
        }
        const FAnomaliaZPrigimaliaModManifest* const* Found = ById.Find(Id);
        if (!Found || !*Found)
        {
            OutError = FString::Printf(TEXT("Missing mod dependency: %s"), *Id);
            return false;
        }
        const FAnomaliaZPrigimaliaModManifest& Mod = **Found;
        if (!ValidateModManifest(Mod, OutError)) return false;
        State.Add(Id, 1);
        for (const FString& Dependency : Mod.Dependencies)
            if (!Visit(Dependency)) return false;
        State.Add(Id, 2);
        Result.Required.Add(Mod);
        return true;
    };

    for (const FString& Id : Requested)
        if (!Visit(Id)) return false;

    TMap<FString, FString> InstalledChecksums;
    for (const FAnomaliaZPrigimaliaModManifest& Current : Installed)
        InstalledChecksums.Add(Current.Id, Current.Sha256);

    for (const FAnomaliaZPrigimaliaModManifest& Mod : Result.Required)
    {
        const FString* CurrentHash = InstalledChecksums.Find(Mod.Id);
        if (CurrentHash && *CurrentHash == Mod.Sha256)
            Result.AlreadyInstalled.Add(Mod);
        else
            Result.Downloads.Add(Mod); // A *plan*, not an actual network request.
    }
    Result.bRequiresConsent = true;
    OutResolution = MoveTemp(Result);
    return true;
}

bool UAnomaliaZPrigimaliaModResolver::ValidatePlacementManifest(
    const TArray<FString>& RelativeFiles, FString& OutError)
{
    OutError.Empty();
    for (const FString& File : RelativeFiles)
    {
        if (File.IsEmpty() || File.StartsWith(TEXT("/")) || File.Contains(TEXT("..")) ||
            File.Contains(TEXT("\\")) || !File.EndsWith(TEXT(".json"), ESearchCase::CaseSensitive))
        {
            OutError = FString::Printf(TEXT("Unsafe mapping path: %s"), *File);
            return false;
        }
        TArray<FString> Segments;
        File.ParseIntoArray(Segments, TEXT("/"), false);
        for (const FString& Segment : Segments)
        {
            if (Segment.IsEmpty() || Segment.EndsWith(TEXT(" ")) || Segment.EndsWith(TEXT(".")))
            {
                OutError = FString::Printf(TEXT("Unsafe mapping path: %s"), *File);
                return false;
            }
        }
        for (const TCHAR C : File)
        {
            if (C < 32 || C == TEXT(':') || C == TEXT('#') || C == TEXT('?') || C == TEXT('%'))
            {
                OutError = FString::Printf(TEXT("Unsafe mapping path: %s"), *File);
                return false;
            }
        }
    }
    return true;
}
