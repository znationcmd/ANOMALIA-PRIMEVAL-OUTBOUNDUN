#include "AnomaliaServerSettingsSubsystem.h"
#include "Dom/JsonObject.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

bool UAnomaliaServerSettingsSubsystem::IsSafeServerId(const FString& ServerId)
{
    if (ServerId.IsEmpty() || ServerId.Len() > 64) return false;
    for (TCHAR Character : ServerId)
    {
        if (!FChar::IsAlnum(Character) && Character != TEXT('-') && Character != TEXT('_')) return false;
    }
    return true;
}

FString UAnomaliaServerSettingsSubsystem::GetServerSaveDirectory() const
{
    return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Servers"), ActiveServerId);
}

bool UAnomaliaServerSettingsSubsystem::LoadServerSettings(const FString& ServerId, FString& Error)
{
    Error.Empty();
    if (!IsSafeServerId(ServerId))
    {
        Error = TEXT("Identifiant de serveur invalide.");
        return false;
    }
    const FString File = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Servers"), ServerId, TEXT("config.json"));
    FAnomaliaServerSettings Loaded;
    if (IFileManager::Get().FileExists(*File))
    {
        FString Text;
        if (!FFileHelper::LoadFileToString(Text, *File) || Text.Len() > 65536)
        {
            Error = TEXT("Lecture de config.json impossible ou fichier trop grand.");
            return false;
        }
        TSharedPtr<FJsonObject> Root;
        const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Text);
        if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
        {
            Error = TEXT("JSON invalide. Le fichier existant n'a pas ete modifie.");
            return false;
        }
        const TSharedPtr<FJsonObject>* Server = nullptr;
        if (!Root->TryGetObjectField(TEXT("server"), Server) || !Server || !Server->IsValid())
        {
            Error = TEXT("Section server manquante.");
            return false;
        }
        FString Name, Mode;
        double Number = 0;
        if ((*Server)->TryGetStringField(TEXT("name"), Name)) Loaded.ServerName = Name.Left(96);
        if ((*Server)->TryGetStringField(TEXT("mode"), Mode)) Loaded.GameMode = Mode;
        if ((*Server)->TryGetNumberField(TEXT("port"), Number)) Loaded.Port = FMath::Clamp((int32)Number, 1024, 65535);
        if ((*Server)->TryGetNumberField(TEXT("maxPlayers"), Number)) Loaded.MaxPlayers = FMath::Clamp((int32)Number, 1, 64);
        if ((*Server)->TryGetNumberField(TEXT("timeMultiplier"), Number)) Loaded.TimeMultiplier = FMath::Clamp((float)Number, 0.1f, 24.0f);
        bool bThirdPerson = true;
        if ((*Server)->TryGetBoolField(TEXT("thirdPerson"), bThirdPerson)) Loaded.bThirdPerson = bThirdPerson;
        if (Loaded.GameMode != TEXT("pve") && Loaded.GameMode != TEXT("pvp") &&
            Loaded.GameMode != TEXT("rp") && Loaded.GameMode != TEXT("mixed"))
        {
            Error = TEXT("Mode de jeu invalide.");
            return false;
        }
    }
    ActiveServerId = ServerId;
    Settings = Loaded;
    return true;
}

bool UAnomaliaServerSettingsSubsystem::SaveServerSettings(FString& Error)
{
    Error.Empty();
    if (!IsSafeServerId(ActiveServerId))
    {
        Error = TEXT("Identifiant de serveur invalide.");
        return false;
    }
    const FString Folder = GetServerSaveDirectory();
    if (!IFileManager::Get().MakeDirectory(*Folder, true))
    {
        Error = TEXT("Impossible de creer le dossier serveur.");
        return false;
    }
    const FString File = FPaths::Combine(Folder, TEXT("config.json"));
    TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
    // Preserve unrelated fields, including future mod and editor metadata.
    if (IFileManager::Get().FileExists(*File))
    {
        FString Previous;
        if (!FFileHelper::LoadFileToString(Previous, *File) || Previous.Len() > 65536 ||
            !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Previous), Root) || !Root.IsValid())
        {
            Error = TEXT("Configuration existante illisible : sauvegarde annulee pour eviter toute perte.");
            return false;
        }
    }
    TSharedPtr<FJsonObject> Server = MakeShared<FJsonObject>();
    const TSharedPtr<FJsonObject>* ExistingServer = nullptr;
    if (Root->TryGetObjectField(TEXT("server"), ExistingServer) && ExistingServer && ExistingServer->IsValid())
        Server = MakeShared<FJsonObject>(**ExistingServer);
    Server->SetStringField(TEXT("name"), Settings.ServerName.Left(96));
    Server->SetStringField(TEXT("mode"), Settings.GameMode);
    Server->SetNumberField(TEXT("port"), FMath::Clamp(Settings.Port, 1024, 65535));
    Server->SetNumberField(TEXT("maxPlayers"), FMath::Clamp(Settings.MaxPlayers, 1, 64));
    Server->SetNumberField(TEXT("timeMultiplier"), FMath::Clamp(Settings.TimeMultiplier, 0.1f, 24.0f));
    Server->SetBoolField(TEXT("thirdPerson"), Settings.bThirdPerson);
    Root->SetNumberField(TEXT("schemaVersion"), 1);
    Root->SetObjectField(TEXT("server"), Server);
    FString Output;
    if (!FJsonSerializer::Serialize(Root.ToSharedRef(), TJsonWriterFactory<>::Create(&Output)))
    {
        Error = TEXT("Echec de serialisation JSON.");
        return false;
    }
    // Atomic-ish replace: stage in the same directory, retain a backup of prior data.
    const FString Staged = File + TEXT(".tmp");
    if (!FFileHelper::SaveStringToFile(Output, *Staged))
    {
        Error = TEXT("Echec d'ecriture du fichier temporaire.");
        return false;
    }
    if (IFileManager::Get().FileExists(*File))
    {
        const FString Backup = File + TEXT(".bak");
        if (!IFileManager::Get().Copy(*Backup, *File, true, true) == COPY_OK)
        {
            IFileManager::Get().Delete(*Staged);
            Error = TEXT("Impossible de sauvegarder l'ancien fichier.");
            return false;
        }
    }
    if (!IFileManager::Get().Move(*File, *Staged, true, true))
    {
        Error = TEXT("Impossible de finaliser la sauvegarde.");
        return false;
    }
    return true;
}
