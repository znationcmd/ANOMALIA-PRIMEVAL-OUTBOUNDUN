#include "AnomaliaConfigFusionLibrary.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace
{
    bool IsUnsafeKey(const FString& Key)
    {
        return Key == TEXT("__proto__") || Key == TEXT("constructor") ||
               Key == TEXT("prototype");
    }

    bool ParseObjectLayer(const FString& Json, TSharedPtr<FJsonObject>& Out, FString& OutError)
    {
        if (Json.TrimStartAndEnd().IsEmpty())
        {
            Out = MakeShared<FJsonObject>();
            return true;
        }
        if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json), Out) ||
            !Out.IsValid())
        {
            OutError = TEXT("Config layer must be a JSON object");
            return false;
        }
        return true;
    }

    bool WriteObject(const TSharedRef<FJsonObject>& Object, FString& OutJson)
    {
        OutJson.Empty();
        return FJsonSerializer::Serialize(Object, TJsonWriterFactory<>::Create(&OutJson));
    }

    FString EncodedValue(const TSharedPtr<FJsonValue>& Value)
    {
        TSharedRef<FJsonObject> Wrapper = MakeShared<FJsonObject>();
        Wrapper->SetField(TEXT("value"), Value);
        FString Encoded;
        WriteObject(Wrapper, Encoded);
        return Encoded;
    }

    struct FDomainDefinition
    {
        FString Name;
        FString Primary;
        TArray<FString> Legacy;
    };

    const TArray<FDomainDefinition>& Domains()
    {
        static const TArray<FDomainDefinition> Definitions = {
        {TEXT("server"), TEXT("config.json"), {TEXT("serverDZ.cfg")}},
        {TEXT("permissions"), TEXT("admin_config.json"), {TEXT("AllowedCheaterSteamIDs.txt")}},
        {TEXT("gameplay"), TEXT("GameUserSettings.ini"), {TEXT("cfggameplay.json")}},
        {TEXT("advanced"), TEXT("Game.ini"), {}},
        {TEXT("loot"), TEXT("types.xml"), {TEXT("cfglootspawn.xml"), TEXT("cfgspawnabletypes.xml"), TEXT("loot_tiers.json"), TEXT("loot_items_catalog.json")}},
        {TEXT("events"), TEXT("events.xml"), {TEXT("cfgeventspawns.xml"), TEXT("radiation_zones.json")}},
        {TEXT("vehicles"), TEXT("vehicles.xml"), {}},
        {TEXT("maps"), TEXT("scenarios.json"), {TEXT("world-settings.json"), TEXT("cfgplayerspawnpoints.xml"), TEXT("mapping/manifest.json")}},
        {TEXT("creatures"), TEXT("dinosaurs/catalog.json"), {TEXT("creatures.json"), TEXT("ai.xml"), TEXT("dino_species_catalog.json"), TEXT("dino_variants_catalog.json"), TEXT("dino_moro_creatures_catalog.json"), TEXT("dino_kibbles_catalog.json")}},
        {TEXT("economy"), TEXT("globals.xml"), {TEXT("economy.xml"), TEXT("cfgeconomycore.xml")}},
        {TEXT("mods"), TEXT("mods.json"), {}},
        {TEXT("persistence"), TEXT("world.json"), {}}
        };
        return Definitions;
    }
}

bool UAnomaliaConfigFusionLibrary::ParseIniToJson(
    const FString& IniText, FString& OutSectionsJson, FString& OutError)
{
    OutError.Empty();
    OutSectionsJson.Empty();
    TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
    FString Section;
    TArray<FString> Lines;
    IniText.ParseIntoArrayLines(Lines, false);

    for (const FString& Raw : Lines)
    {
        const FString Line = Raw.TrimStartAndEnd();
        if (Line.IsEmpty() || Line.StartsWith(TEXT(";")) || Line.StartsWith(TEXT("#")))
            continue;

        if (Line.StartsWith(TEXT("[")) && Line.EndsWith(TEXT("]")) && Line.Len() >= 2)
        {
            Section = Line.Mid(1, Line.Len() - 2);
            if (IsUnsafeKey(Section))
            {
                OutError = TEXT("Unsafe INI section");
                return false;
            }
            // Keep sections that have no keys as well.
            if (!Root->HasField(Section))
                Root->SetObjectField(Section, MakeShared<FJsonObject>());
            continue;
        }

        int32 EqualIndex = INDEX_NONE;
        if (!Line.FindChar(TEXT('='), EqualIndex) || EqualIndex < 1) continue;
        const FString Key = Line.Left(EqualIndex).TrimStartAndEnd();
        if (IsUnsafeKey(Key))
        {
            OutError = TEXT("Unsafe INI key");
            return false;
        }
        const FString Value = Line.Mid(EqualIndex + 1).TrimStartAndEnd();

        const TSharedPtr<FJsonObject>* CurrentSection = nullptr;
        if (!Root->TryGetObjectField(Section, CurrentSection) ||
            !CurrentSection || !CurrentSection->IsValid())
        {
            Root->SetObjectField(Section, MakeShared<FJsonObject>());
            Root->TryGetObjectField(Section, CurrentSection);
        }
        if (!CurrentSection || !CurrentSection->IsValid())
        {
            OutError = TEXT("Cannot allocate INI section");
            return false;
        }
        (*CurrentSection)->SetStringField(Key, Value);
    }

    if (!WriteObject(Root, OutSectionsJson))
    {
        OutError = TEXT("Could not serialize INI");
        return false;
    }
    return true;
}

bool UAnomaliaConfigFusionLibrary::FlattenIniJson(
    const FString& SectionsJson, FString& OutFlatJson, FString& OutError)
{
    OutFlatJson.Empty();
    OutError.Empty();
    TSharedPtr<FJsonObject> Sections;
    if (!ParseObjectLayer(SectionsJson, Sections, OutError)) return false;
    TSharedRef<FJsonObject> Flat = MakeShared<FJsonObject>();

    for (const auto& Section : Sections->Values)
    {
        const FString SectionName(Section.Key.Len(), *Section.Key);
        if (IsUnsafeKey(SectionName) || !Section.Value.IsValid() ||
            Section.Value->Type != EJson::Object)
        {
            OutError = TEXT("Invalid INI section object");
            return false;
        }
        const TSharedPtr<FJsonObject> Values = Section.Value->AsObject();
        for (const auto& Entry : Values->Values)
        {
            const FString EntryName(Entry.Key.Len(), *Entry.Key);
            const FString Name = SectionName.IsEmpty() ? EntryName :
                SectionName + TEXT(".") + EntryName;
            if (IsUnsafeKey(EntryName) || IsUnsafeKey(Name))
            {
                OutError = TEXT("Unsafe flattened key");
                return false;
            }
            Flat->SetField(Name, Entry.Value);
        }
    }
    if (!WriteObject(Flat, OutFlatJson))
    {
        OutError = TEXT("Could not serialize flattened INI");
        return false;
    }
    return true;
}

bool UAnomaliaConfigFusionLibrary::MergeConfigJson(
    const FString& DefaultsJson, const FString& LegacyJson,
    const FString& CanonicalJson, const FString& ServerJson,
    FString& OutReportJson, FString& OutError)
{
    OutReportJson.Empty();
    OutError.Empty();

    TSharedPtr<FJsonObject> Defaults, Legacy, Canonical, Server;
    if (!ParseObjectLayer(DefaultsJson, Defaults, OutError) ||
        !ParseObjectLayer(LegacyJson, Legacy, OutError) ||
        !ParseObjectLayer(CanonicalJson, Canonical, OutError) ||
        !ParseObjectLayer(ServerJson, Server, OutError))
        return false;

    TSharedRef<FJsonObject> Merged = MakeShared<FJsonObject>();
    TArray<TSharedPtr<FJsonValue>> Conflicts;
    struct FLayer { const TCHAR* Name; TSharedPtr<FJsonObject> Data; };
    const TArray<FLayer> Layers = {
        {TEXT("defaults"), Defaults}, {TEXT("legacy"), Legacy},
        {TEXT("canonical"), Canonical}, {TEXT("server"), Server}
    };

    for (const FLayer& Layer : Layers)
    {
        for (const auto& Entry : Layer.Data->Values)
        {
            const FString EntryName(Entry.Key.Len(), *Entry.Key);
            if (IsUnsafeKey(EntryName) || !Entry.Value.IsValid())
            {
                OutError = TEXT("Unsafe or invalid config key");
                return false;
            }
            if (Merged->HasField(EntryName))
            {
                const TSharedPtr<FJsonValue> Previous = Merged->Values.FindRef(Entry.Key);
                if (EncodedValue(Previous) != EncodedValue(Entry.Value))
                {
                    TSharedRef<FJsonObject> Conflict = MakeShared<FJsonObject>();
                    Conflict->SetStringField(TEXT("key"), EntryName);
                    Conflict->SetField(TEXT("from"), Previous);
                    Conflict->SetField(TEXT("to"), Entry.Value);
                    Conflict->SetStringField(TEXT("source"), Layer.Name);
                    Conflicts.Add(MakeShared<FJsonValueObject>(Conflict));
                }
            }
            Merged->SetField(EntryName, Entry.Value);
        }
    }

    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetObjectField(TEXT("values"), Merged);
    Result->SetArrayField(TEXT("conflicts"), Conflicts);
    TArray<TSharedPtr<FJsonValue>> Precedence;
    for (const FLayer& Layer : Layers)
        Precedence.Add(MakeShared<FJsonValueString>(Layer.Name));
    Result->SetArrayField(TEXT("precedence"), Precedence);
    if (!WriteObject(Result, OutReportJson))
    {
        OutError = TEXT("Could not serialize merge report");
        return false;
    }
    return true;
}

bool UAnomaliaConfigFusionLibrary::BuildFusionReport(
    const TArray<FString>& PresentFilePaths, FString& OutReportJson, FString& OutError)
{
    OutReportJson.Empty();
    OutError.Empty();
    TSet<FString> Present;
    for (const FString& Path : PresentFilePaths) Present.Add(Path);
    TArray<TSharedPtr<FJsonValue>> Rows;
    for (const FDomainDefinition& Domain : Domains())
    {
        TSharedRef<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetStringField(TEXT("domain"), Domain.Name);
        Row->SetStringField(TEXT("primary"), Domain.Primary);
        Row->SetBoolField(TEXT("primaryPresent"), Present.Contains(Domain.Primary));
        TArray<TSharedPtr<FJsonValue>> Legacy;
        for (const FString& Path : Domain.Legacy)
        {
            TSharedRef<FJsonObject> Entry = MakeShared<FJsonObject>();
            Entry->SetStringField(TEXT("path"), Path);
            Entry->SetBoolField(TEXT("present"), Present.Contains(Path));
            Legacy.Add(MakeShared<FJsonValueObject>(Entry));
        }
        Row->SetArrayField(TEXT("legacy"), Legacy);
        Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetArrayField(TEXT("domains"), Rows);
    if (!WriteObject(Report, OutReportJson))
    {
        OutError = TEXT("Could not serialize fusion report");
        return false;
    }
    return true;
}
