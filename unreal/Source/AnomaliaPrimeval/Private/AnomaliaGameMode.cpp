#include "AnomaliaGameMode.h"
#include "AnomaliaServerSettingsSubsystem.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/GameInstance.h"

void AAnomaliaGameMode::InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage)
{
    Super::InitGame(MapName, Options, ErrorMessage);
    if (UGameInstance* Instance = GetGameInstance())
    {
        if (UAnomaliaServerSettingsSubsystem* Config = Instance->GetSubsystem<UAnomaliaServerSettingsSubsystem>())
        {
            const FString ServerId = UGameplayStatics::ParseOption(Options, TEXT("ServerId"));
            FString ConfigError;
            if (!Config->LoadServerSettings(ServerId.IsEmpty() ? TEXT("main") : ServerId, ConfigError))
            {
                UE_LOG(LogTemp, Error, TEXT("ANOMALIA server config: %s"), *ConfigError);
                ErrorMessage = ConfigError;
                return;
            }
            const FAnomaliaServerSettings Settings = Config->GetServerSettings();
            ActiveMode = Settings.GameMode;
            ConfiguredMaxPlayers = Settings.MaxPlayers;
            UE_LOG(LogTemp, Display, TEXT("ANOMALIA server '%s' mode=%s maxPlayers=%d"), *Config->GetServerId(), *ActiveMode, ConfiguredMaxPlayers);
        }
    }
}
