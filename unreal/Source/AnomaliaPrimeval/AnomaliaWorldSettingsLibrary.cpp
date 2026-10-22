#include "AnomaliaWorldSettingsLibrary.h"
#include "AnomaliaConfigLibrary.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace
{
    const FString WorldSettingsStateId = TEXT("world-settings");

    bool IsValidGameMode(const FString& Mode)
    {
        return Mode == TEXT("pve") || Mode == TEXT("pvp") ||
               Mode == TEXT("rp") || Mode == TEXT("mixed");
    }
}

FAnomaliaWorldSettings UAnomaliaWorldSettingsLibrary::NormalizeWorldSettings(
    const FAnomaliaWorldSettings& Input)
{
    FAnomaliaWorldSettings Result;
    Result.Mode = IsValidGameMode(Input.Mode) ? Input.Mode : TEXT("pve");
    Result.Difficulty = FMath::IsFinite(Input.Difficulty) ? FMath::Clamp(Input.Difficulty, .2f, 5.f) : 1.f;
    Result.Xp = FMath::IsFinite(Input.Xp) ? FMath::Clamp(Input.Xp, .1f, 20.f) : 1.f;
    Result.Harvest = FMath::IsFinite(Input.Harvest) ? FMath::Clamp(Input.Harvest, .1f, 20.f) : 1.f;
    Result.Loot = FMath::IsFinite(Input.Loot) ? FMath::Clamp(Input.Loot, .1f, 20.f) : 1.f;
    Result.FoodDrain = FMath::IsFinite(Input.FoodDrain) ? FMath::Clamp(Input.FoodDrain, 0.f, 5.f) : 1.f;
    Result.WaterDrain = FMath::IsFinite(Input.WaterDrain) ? FMath::Clamp(Input.WaterDrain, 0.f, 5.f) : 1.f;
    Result.StaminaDrain = FMath::IsFinite(Input.StaminaDrain) ? FMath::Clamp(Input.StaminaDrain, 0.f, 5.f) : 1.f;
    Result.Taming = FMath::IsFinite(Input.Taming) ? FMath::Clamp(Input.Taming, .1f, 50.f) : 1.f;
    Result.Breeding = FMath::IsFinite(Input.Breeding) ? FMath::Clamp(Input.Breeding, .1f, 50.f) : 1.f;
    Result.Hatching = FMath::IsFinite(Input.Hatching) ? FMath::Clamp(Input.Hatching, .1f, 50.f) : 1.f;
    Result.Maturation = FMath::IsFinite(Input.Maturation) ? FMath::Clamp(Input.Maturation, .1f, 50.f) : 1.f;
    Result.DayLength = FMath::IsFinite(Input.DayLength) ? FMath::Clamp(Input.DayLength, .1f, 10.f) : 1.f;
    Result.NightLength = FMath::IsFinite(Input.NightLength) ? FMath::Clamp(Input.NightLength, .1f, 10.f) : 1.f;
    Result.MaxPlayers = FMath::Clamp(Input.MaxPlayers, 2, 64);
    return Result;
}

bool UAnomaliaWorldSettingsLibrary::LoadWorldSettings(
    const FString& ServerId, FAnomaliaWorldSettings& OutSettings, FString& OutError)
{
    OutSettings = FAnomaliaWorldSettings();
    FString Raw;
    if (!UAnomaliaConfigLibrary::LoadWorldState(ServerId, WorldSettingsStateId, Raw, OutError))
        return false;

    TSharedPtr<FJsonObject> Root;
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Raw), Root) || !Root.IsValid())
    {
        OutError = TEXT("Invalid world settings JSON");
        return false;
    }
    const TSharedPtr<FJsonObject>* SettingsObject = nullptr;
    if (!Root->TryGetObjectField(TEXT("settings"), SettingsObject) ||
        !SettingsObject || !SettingsObject->IsValid())
    {
        OutError = TEXT("Missing world settings data");
        return false;
    }

    const TSharedPtr<FJsonObject>& Values = *SettingsObject;
    FAnomaliaWorldSettings Settings;
    FString Mode;
    if (Values->TryGetStringField(TEXT("mode"), Mode))
        Settings.Mode = IsValidGameMode(Mode) ? Mode : TEXT("pve");
    double Numeric = 0.0;
    if (Values->TryGetNumberField(TEXT("difficulty"), Numeric))
        Settings.Difficulty = FMath::IsFinite(Numeric) ? static_cast<float>(FMath::Clamp(Numeric, static_cast<double>(.2f), static_cast<double>(5.f))) : 1.f;
    if (Values->TryGetNumberField(TEXT("xp"), Numeric))
        Settings.Xp = FMath::IsFinite(Numeric) ? static_cast<float>(FMath::Clamp(Numeric, static_cast<double>(.1f), static_cast<double>(20.f))) : 1.f;
    if (Values->TryGetNumberField(TEXT("harvest"), Numeric))
        Settings.Harvest = FMath::IsFinite(Numeric) ? static_cast<float>(FMath::Clamp(Numeric, static_cast<double>(.1f), static_cast<double>(20.f))) : 1.f;
    if (Values->TryGetNumberField(TEXT("loot"), Numeric))
        Settings.Loot = FMath::IsFinite(Numeric) ? static_cast<float>(FMath::Clamp(Numeric, static_cast<double>(.1f), static_cast<double>(20.f))) : 1.f;
    if (Values->TryGetNumberField(TEXT("foodDrain"), Numeric))
        Settings.FoodDrain = FMath::IsFinite(Numeric) ? static_cast<float>(FMath::Clamp(Numeric, static_cast<double>(0.f), static_cast<double>(5.f))) : 1.f;
    if (Values->TryGetNumberField(TEXT("waterDrain"), Numeric))
        Settings.WaterDrain = FMath::IsFinite(Numeric) ? static_cast<float>(FMath::Clamp(Numeric, static_cast<double>(0.f), static_cast<double>(5.f))) : 1.f;
    if (Values->TryGetNumberField(TEXT("staminaDrain"), Numeric))
        Settings.StaminaDrain = FMath::IsFinite(Numeric) ? static_cast<float>(FMath::Clamp(Numeric, static_cast<double>(0.f), static_cast<double>(5.f))) : 1.f;
    if (Values->TryGetNumberField(TEXT("taming"), Numeric))
        Settings.Taming = FMath::IsFinite(Numeric) ? static_cast<float>(FMath::Clamp(Numeric, static_cast<double>(.1f), static_cast<double>(50.f))) : 1.f;
    if (Values->TryGetNumberField(TEXT("breeding"), Numeric))
        Settings.Breeding = FMath::IsFinite(Numeric) ? static_cast<float>(FMath::Clamp(Numeric, static_cast<double>(.1f), static_cast<double>(50.f))) : 1.f;
    if (Values->TryGetNumberField(TEXT("hatching"), Numeric))
        Settings.Hatching = FMath::IsFinite(Numeric) ? static_cast<float>(FMath::Clamp(Numeric, static_cast<double>(.1f), static_cast<double>(50.f))) : 1.f;
    if (Values->TryGetNumberField(TEXT("maturation"), Numeric))
        Settings.Maturation = FMath::IsFinite(Numeric) ? static_cast<float>(FMath::Clamp(Numeric, static_cast<double>(.1f), static_cast<double>(50.f))) : 1.f;
    if (Values->TryGetNumberField(TEXT("dayLength"), Numeric))
        Settings.DayLength = FMath::IsFinite(Numeric) ? static_cast<float>(FMath::Clamp(Numeric, static_cast<double>(.1f), static_cast<double>(10.f))) : 1.f;
    if (Values->TryGetNumberField(TEXT("nightLength"), Numeric))
        Settings.NightLength = FMath::IsFinite(Numeric) ? static_cast<float>(FMath::Clamp(Numeric, static_cast<double>(.1f), static_cast<double>(10.f))) : 1.f;
    if (Values->TryGetNumberField(TEXT("maxPlayers"), Numeric) && FMath::IsFinite(Numeric))
        Settings.MaxPlayers = FMath::RoundToInt(FMath::Clamp(Numeric, 2.0, 64.0));

    OutSettings = NormalizeWorldSettings(Settings);
    OutError.Empty();
    return true;
}

bool UAnomaliaWorldSettingsLibrary::SaveWorldSettings(
    const FString& ServerId, const FAnomaliaWorldSettings& Input, FString& OutError)
{
    const FAnomaliaWorldSettings Settings = NormalizeWorldSettings(Input);
    TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
    TSharedPtr<FJsonObject> Values = MakeShared<FJsonObject>();
    Root->SetNumberField(TEXT("schemaVersion"), 1);
    Values->SetStringField(TEXT("mode"), Settings.Mode);
    Values->SetNumberField(TEXT("difficulty"), Settings.Difficulty);
    Values->SetNumberField(TEXT("xp"), Settings.Xp);
    Values->SetNumberField(TEXT("harvest"), Settings.Harvest);
    Values->SetNumberField(TEXT("loot"), Settings.Loot);
    Values->SetNumberField(TEXT("foodDrain"), Settings.FoodDrain);
    Values->SetNumberField(TEXT("waterDrain"), Settings.WaterDrain);
    Values->SetNumberField(TEXT("staminaDrain"), Settings.StaminaDrain);
    Values->SetNumberField(TEXT("taming"), Settings.Taming);
    Values->SetNumberField(TEXT("breeding"), Settings.Breeding);
    Values->SetNumberField(TEXT("hatching"), Settings.Hatching);
    Values->SetNumberField(TEXT("maturation"), Settings.Maturation);
    Values->SetNumberField(TEXT("dayLength"), Settings.DayLength);
    Values->SetNumberField(TEXT("nightLength"), Settings.NightLength);
    Values->SetNumberField(TEXT("maxPlayers"), Settings.MaxPlayers);
    Root->SetObjectField(TEXT("settings"), Values);
    FString Raw;
    if (!FJsonSerializer::Serialize(Root.ToSharedRef(), TJsonWriterFactory<>::Create(&Raw)))
    {
        OutError = TEXT("Could not serialize world settings");
        return false;
    }
    return UAnomaliaConfigLibrary::SaveWorldState(ServerId, WorldSettingsStateId, Raw, OutError);
}
