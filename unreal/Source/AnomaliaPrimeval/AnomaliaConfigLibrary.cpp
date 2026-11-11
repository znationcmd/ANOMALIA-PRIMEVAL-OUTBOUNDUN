#include "AnomaliaConfigLibrary.h"
#include "Dom/JsonObject.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace
{
    constexpr int32 MaxProfileChars = 1024 * 1024;
    bool ParseObject(const FString& Text, TSharedPtr<FJsonObject>& Object)
    {
        TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Text);
        return FJsonSerializer::Deserialize(Reader, Object) && Object.IsValid();
    }
    FString SerializeObject(const TSharedRef<FJsonObject>& Object)
    {
        FString Text;
        TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Text);
        FJsonSerializer::Serialize(Object, Writer);
        return Text;
    }
}

bool UAnomaliaConfigLibrary::ValidId(const FString& Id)
{
    if (Id.IsEmpty() || Id.Len() > 64) return false;
    for (const TCHAR C : Id)
    {
        if (!FChar::IsAlnum(C) && C != TEXT('-') && C != TEXT('_')) return false;
        if (C > 127) return false;
    }
    return true;
}

FString UAnomaliaConfigLibrary::ServerRoot(const FString& ServerId)
{
    return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Servers"), ServerId);
}

bool UAnomaliaConfigLibrary::WriteJsonSafely(const FString& File, const FString& Json, FString& OutError)
{
    OutError.Empty();
    if (Json.Len() > MaxProfileChars)
    {
        OutError = TEXT("JSON too large");
        return false;
    }
    TSharedPtr<FJsonObject> Parsed;
    if (!ParseObject(Json, Parsed))
    {
        OutError = TEXT("Invalid JSON object");
        return false;
    }
    const FString Directory = FPaths::GetPath(File);
    if (!IFileManager::Get().MakeDirectory(*Directory, true))
    {
        OutError = TEXT("Cannot create configuration directory");
        return false;
    }
    const FString Temp = File + TEXT(".tmp");
    if (!FFileHelper::SaveStringToFile(Json, *Temp, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
    {
        OutError = TEXT("Cannot write temporary configuration");
        return false;
    }
    // Replace only the target file within the validated server/profile directory.
    if (!IFileManager::Get().Move(*File, *Temp, true, true))
    {
        IFileManager::Get().Delete(*Temp);
        OutError = TEXT("Cannot commit configuration");
        return false;
    }
    return true;
}

bool UAnomaliaConfigLibrary::LoadServerSettings(const FString& ServerId, FAnomaliaServerSettings& OutSettings, FString& OutError)
{
    OutSettings = FAnomaliaServerSettings{};
    OutError.Empty();
    if (!ValidId(ServerId)) { OutError = TEXT("Invalid server identifier"); return false; }
    const FString Saved = FPaths::Combine(ServerRoot(ServerId), TEXT("config.json"));
    const FString Template = FPaths::Combine(FPaths::ProjectConfigDir(), TEXT("Anomalia"), TEXT("config.json"));
    const FString File = IFileManager::Get().FileExists(*Saved) ? Saved : Template;
    FString Raw;
    if (!FFileHelper::LoadFileToString(Raw, *File))
    {
        OutError = TEXT("No configuration file; defaults returned");
        return false;
    }
    TSharedPtr<FJsonObject> Root;
    if (!ParseObject(Raw, Root)) { OutError = TEXT("Malformed config.json"); return false; }
    const TSharedPtr<FJsonObject>* ServerPtr = nullptr;
    if (!Root->TryGetObjectField(TEXT("server"), ServerPtr) || !ServerPtr || !ServerPtr->IsValid())
    {
        OutError = TEXT("Missing server section");
        return false;
    }
    const TSharedPtr<FJsonObject>& Server = *ServerPtr;
    FString Value;
    if (Server->TryGetStringField(TEXT("name"), Value)) OutSettings.Name = Value.Left(96);
    if (Server->TryGetStringField(TEXT("mode"), Value) &&
        (Value == TEXT("rp") || Value == TEXT("pvp") || Value == TEXT("pve") || Value == TEXT("mixed"))) OutSettings.Mode = Value;
    double Number = 0;
    if (Server->TryGetNumberField(TEXT("port"), Number)) OutSettings.Port = FMath::Clamp(FMath::RoundToInt(Number), 1024, 65535);
    if (Server->TryGetNumberField(TEXT("maxPlayers"), Number)) OutSettings.MaxPlayers = FMath::Clamp(FMath::RoundToInt(Number), 1, 64);
    if (Server->TryGetNumberField(TEXT("timeMultiplier"), Number)) OutSettings.TimeMultiplier = FMath::Clamp(static_cast<float>(Number), 0.1f, 24.0f);
    bool bValue = false;
    if (Server->TryGetBoolField(TEXT("thirdPerson"), bValue)) OutSettings.bThirdPerson = bValue;
    // Missing survival fields preserve the original gameplay defaults.
    const TSharedPtr<FJsonObject>* SurvivalPtr = nullptr;
    if (Root->TryGetObjectField(TEXT("survival"), SurvivalPtr) && SurvivalPtr && SurvivalPtr->IsValid())
    {
        const TSharedPtr<FJsonObject>& Survival = *SurvivalPtr;
        if (Survival->TryGetNumberField(TEXT("hungerDrainPerSecond"), Number) && FMath::IsFinite(Number))
            OutSettings.HungerDrainPerSecond = FMath::Clamp(static_cast<float>(Number), 0.f, 10.f);
        if (Survival->TryGetNumberField(TEXT("thirstDrainPerSecond"), Number) && FMath::IsFinite(Number))
            OutSettings.ThirstDrainPerSecond = FMath::Clamp(static_cast<float>(Number), 0.f, 10.f);
        if (Survival->TryGetNumberField(TEXT("starvationDamagePerSecond"), Number) && FMath::IsFinite(Number))
            OutSettings.StarvationDamagePerSecond = FMath::Clamp(static_cast<float>(Number), 0.f, 10.f);
        if (Survival->TryGetNumberField(TEXT("ambientTemperatureC"), Number) && FMath::IsFinite(Number))
            OutSettings.AmbientTemperatureC = FMath::Clamp(static_cast<float>(Number), -50.f, 60.f);
    }
    return true;
}

bool UAnomaliaConfigLibrary::SaveServerSettings(const FString& ServerId, const FAnomaliaServerSettings& Settings, FString& OutError)
{
    if (!ValidId(ServerId)) { OutError = TEXT("Invalid server identifier"); return false; }
    if (Settings.Name.IsEmpty() || Settings.Name.Len() > 96 || Settings.Port < 1024 || Settings.Port > 65535 ||
        Settings.MaxPlayers < 1 || Settings.MaxPlayers > 64 || Settings.TimeMultiplier < 0.1f || Settings.TimeMultiplier > 24.f ||
        !FMath::IsFinite(Settings.HungerDrainPerSecond) || Settings.HungerDrainPerSecond < 0.f || Settings.HungerDrainPerSecond > 10.f ||
        !FMath::IsFinite(Settings.ThirstDrainPerSecond) || Settings.ThirstDrainPerSecond < 0.f || Settings.ThirstDrainPerSecond > 10.f ||
        !FMath::IsFinite(Settings.StarvationDamagePerSecond) || Settings.StarvationDamagePerSecond < 0.f || Settings.StarvationDamagePerSecond > 10.f ||
        !FMath::IsFinite(Settings.AmbientTemperatureC) || Settings.AmbientTemperatureC < -50.f || Settings.AmbientTemperatureC > 60.f ||
        !(Settings.Mode == TEXT("rp") || Settings.Mode == TEXT("pvp") || Settings.Mode == TEXT("pve") || Settings.Mode == TEXT("mixed")))
    {
        OutError = TEXT("Invalid server settings");
        return false;
    }
    // Merge instead of rewriting: retain password, extensions and unknown keys.
    const FString File = FPaths::Combine(ServerRoot(ServerId), TEXT("config.json"));
    const FString Template = FPaths::Combine(FPaths::ProjectConfigDir(), TEXT("Anomalia"), TEXT("config.json"));
    FString Existing;
    TSharedPtr<FJsonObject> Root;
    if (FFileHelper::LoadFileToString(Existing, *File) || FFileHelper::LoadFileToString(Existing, *Template))
    {
        if (!ParseObject(Existing, Root)) { OutError = TEXT("Existing configuration is invalid; left untouched"); return false; }
    }
    else Root = MakeShared<FJsonObject>();
    const TSharedPtr<FJsonObject>* Previous = nullptr;
    TSharedPtr<FJsonObject> Server = (Root->TryGetObjectField(TEXT("server"), Previous) && Previous && Previous->IsValid())
        ? *Previous : MakeShared<FJsonObject>();
    Server->SetStringField(TEXT("name"), Settings.Name);
    Server->SetNumberField(TEXT("port"), Settings.Port);
    Server->SetNumberField(TEXT("maxPlayers"), Settings.MaxPlayers);
    Server->SetStringField(TEXT("mode"), Settings.Mode);
    Server->SetBoolField(TEXT("thirdPerson"), Settings.bThirdPerson);
    Server->SetNumberField(TEXT("timeMultiplier"), Settings.TimeMultiplier);
    const TSharedPtr<FJsonObject>* PreviousSurvival = nullptr;
    TSharedPtr<FJsonObject> Survival = (Root->TryGetObjectField(TEXT("survival"), PreviousSurvival) && PreviousSurvival && PreviousSurvival->IsValid())
        ? *PreviousSurvival : MakeShared<FJsonObject>();
    Survival->SetNumberField(TEXT("hungerDrainPerSecond"), Settings.HungerDrainPerSecond);
    Survival->SetNumberField(TEXT("thirstDrainPerSecond"), Settings.ThirstDrainPerSecond);
    Survival->SetNumberField(TEXT("starvationDamagePerSecond"), Settings.StarvationDamagePerSecond);
    Survival->SetNumberField(TEXT("ambientTemperatureC"), Settings.AmbientTemperatureC);
    Root->SetObjectField(TEXT("survival"), Survival);
        Root->SetNumberField(TEXT("schemaVersion"), 1);
    Root->SetObjectField(TEXT("server"), Server);
    return WriteJsonSafely(File, SerializeObject(Root.ToSharedRef()), OutError);
}

bool UAnomaliaConfigLibrary::LoadPlayerProfile(const FString& ServerId, const FString& PlayerId, FString& OutJson, FString& OutError)
{
    OutJson.Empty();
    OutError.Empty();
    if (!ValidId(ServerId) || !ValidId(PlayerId)) { OutError = TEXT("Invalid profile scope"); return false; }
    const FString File = FPaths::Combine(ServerRoot(ServerId), TEXT("userProfile"), PlayerId + TEXT(".json"));
    if (!FFileHelper::LoadFileToString(OutJson, *File)) { OutError = TEXT("Profile not found"); return false; }
    TSharedPtr<FJsonObject> Parsed;
    if (OutJson.Len() > MaxProfileChars || !ParseObject(OutJson, Parsed))
    {
        OutJson.Empty();
        OutError = TEXT("Invalid profile data");
        return false;
    }
    return true;
}

bool UAnomaliaConfigLibrary::SavePlayerProfile(const FString& ServerId, const FString& PlayerId, const FString& Json, FString& OutError)
{
    if (!ValidId(ServerId) || !ValidId(PlayerId)) { OutError = TEXT("Invalid profile scope"); return false; }
    const FString File = FPaths::Combine(ServerRoot(ServerId), TEXT("userProfile"), PlayerId + TEXT(".json"));
    return WriteJsonSafely(File, Json, OutError);
}
